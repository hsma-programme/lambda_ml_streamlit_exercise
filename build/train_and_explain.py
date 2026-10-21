"""Train the two readmission models, explain them with SHAP and export for the app (offline build step).

v1 = every column in the extract (what the team submits for sign-off; includes post-discharge leakage)
v2 = discharge-time columns only

Pipeline follows the slides' SHAP demo (_SECTION_shap_demo.qmd): XGBoost with early stopping,
75/10/15 train/validation/test split, TreeExplainer on predicted probability with interventional
perturbation, SHAP values scaled to percentage points.

Run (after generate_data.py):  python build/train_and_explain.py
Writes app/data/*. All metrics are held-out (test split).
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
import shap
import sklearn
import xgboost
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split
from xgboost import XGBClassifier

SEED = 42
N_SHAP = 2000
N_BACKGROUND = 500  # slides use 100; 500 keeps E[f(X)] close to the true average risk
ROOT = Path(__file__).parent
SRC = ROOT / "out" / "discharges.csv"
OUT = ROOT.parent / "app" / "data"

# group -> (display name, same information available at discharge?, plain-English description)
# The leaked columns are named as they would be in a real extract: "last 30 days" is counted back
# from the extract date, so in training it covers the month AFTER discharge. At discharge the same
# field could be filled in, but would cover the 30 days before (mostly in hospital), so it would be
# different information from what the model learnt from.
FEATURES = {
    "age": ("Age", True, "Patient's age in years."),
    "sex": ("Sex", True, "Recorded sex (male = 1)."),
    "deprivation_decile": ("Deprivation decile", True, "Deprivation of the area the patient lives in (1 = most deprived, 10 = least)."),
    "long_term_conditions": ("Long-term conditions", True, "Number of long-term conditions on the patient's record."),
    "emergency_admissions_prev_12m": ("Emergency admissions in previous 12 months", True, "Emergency admissions in the year before this one."),
    "length_of_stay_days": ("Length of stay (days)", True, "Days in hospital for this admission."),
    "number_of_medications": ("Number of medications", True, "Medicines the patient is discharged on."),
    "discharge_destination": ("Discharge destination", True, "Home, home with a care package, or care home."),
    "lives_alone": ("Lives alone", True, "Whether the patient lives alone."),
    "discharge_specialty": ("Discharge specialty", True, "The specialty the patient was discharged from."),
    "discharge_day": ("Discharge day", True, "Day of the week of discharge."),
    "gp_contacts_since_discharge": ("GP contacts (last 30 days)", False, "Number of contacts with the patient's GP practice in the last 30 days."),
    "outpatient_followup_attended": ("Outpatient follow-up attended", False, "Whether the patient attended an outpatient follow-up appointment."),
    "community_nursing_visits_since_discharge": ("Community nursing visits (last 30 days)", False, "Number of community nursing visits to the patient in the last 30 days."),
}
# Where each column comes from, written as the analytics team's data dictionary would put it.
# It is a fact about the column, not an answer: learners have to connect "before the extract
# date" with when the extract was run (30 days after discharge, stated in the dictionary's
# header on the page) to see that some columns aren't available at the moment of discharge.
SOURCE = {
    "age": "Patient administration system. Age on the admission date.",
    "sex": "Patient administration system.",
    "deprivation_decile": "Derived from the home postcode on the patient administration system.",
    "long_term_conditions": "Linked GP record. Conditions coded up to the admission date.",
    "emergency_admissions_prev_12m": "Hospital admissions data. The 12 months before the admission date.",
    "length_of_stay_days": "Patient administration system. Admission date to discharge date.",
    "number_of_medications": "Electronic prescribing. The discharge prescription.",
    "discharge_destination": "Patient administration system. The discharge record.",
    "lives_alone": "Social history taken during the admission.",
    "discharge_specialty": "Patient administration system. The discharge record.",
    "discharge_day": "Patient administration system. Day of the week of the discharge date.",
    "gp_contacts_since_discharge": "Linked GP record. Contacts in the 30 days before the extract date.",
    "outpatient_followup_attended": "Outpatient system. Status of the first follow-up appointment, as at the extract date.",
    "community_nursing_visits_since_discharge": "Community services record. Visits in the 30 days before the extract date.",
}

# Shown to learners only AFTER they answer "would the model get the same information in real use?", so the
# display names and descriptions above must not give the answer away.
WHY = {
    "gp_contacts_since_discharge": "At discharge you could fill in a 'last 30 days' count, but it would cover the 30 days before the patient left, mostly spent in hospital. In the training data the 30 days were counted back from the extract date, so they cover the month after discharge, when patients who are getting worse see their GP more. Same name, different information.",
    "outpatient_followup_attended": "Whether a follow-up was attended can only be recorded once the appointment date has passed, which is after discharge.",
    "community_nursing_visits_since_discharge": "In the training data the 'last 30 days' are the month after discharge, so this counts visits made after the patient went home, which readmitted patients tend to have more of. At discharge the same field would count something else.",
}
WHY["length_of_stay_days"] = (
    "A stay isn't over until the patient leaves, so you couldn't know this at admission. But the model is run "
    "as the patient leaves, and by then we do have it. The moment the model is run decides what counts."
)
WHY["number_of_medications"] = (
    "The discharge prescription is written before the patient leaves, so we have it at the moment of discharge."
)
WHY_DEFAULT = "This is recorded during the admission, so we have it at the moment of discharge."
CATEGORICAL = ["discharge_destination", "discharge_specialty", "discharge_day"]


def build_matrix(df):
    """Return (X, group_of_column). Categoricals are one-hot encoded; group_of_column maps back to the feature."""
    X = df[[c for c in FEATURES if c not in CATEGORICAL and c != "sex"]].copy()
    X["sex"] = (df["sex"] == "Male").astype(int)
    group = {c: c for c in X.columns}
    for c in CATEGORICAL:
        d = pd.get_dummies(df[c], prefix=c, prefix_sep="=", dtype=int)
        for col in d.columns:
            group[col] = c
        X = pd.concat([X, d], axis=1)
    return X, group


def train(X_train, y_train, X_val, y_val):
    model = XGBClassifier(n_estimators=1000, learning_rate=0.05, early_stopping_rounds=50,
                          eval_metric="logloss", enable_categorical=False, random_state=SEED)
    model.fit(X_train, y_train, eval_set=[(X_val, y_val)], verbose=False)
    return model


def explain(model, X_train, X_sample, group):
    # shap silently subsamples a background set to 100 rows unless the masker's max_samples is
    # raised, so pass an explicit masker to really use N_BACKGROUND rows.
    background = shap.maskers.Independent(
        shap.sample(X_train, N_BACKGROUND, random_state=SEED), max_samples=N_BACKGROUND
    )
    explainer = shap.TreeExplainer(model, data=background,
                                   model_output="probability", feature_perturbation="interventional")
    ex = explainer(X_sample)
    vals = pd.DataFrame(ex.values * 100, columns=X_sample.columns, index=X_sample.index)
    grouped = vals.T.groupby(group).sum().T  # sum one-hot columns back to the original feature
    base = float(np.mean(ex.base_values) * 100)
    return grouped, base


def main():
    df = pd.read_csv(SRC)
    df.insert(0, "row_id", np.arange(len(df)))
    y = df["readmitted_30d"]
    X_all, group = build_matrix(df)
    leaky = [c for c in FEATURES if not FEATURES[c][1]]
    X_v2 = X_all[[c for c in X_all.columns if group[c] not in leaky]]
    Xs = {"v1": X_all, "v2": X_v2}

    # Same split for both models (75/10/15), stratified on the outcome
    idx_train, idx_temp = train_test_split(df.index, train_size=0.75, stratify=y, random_state=SEED)
    idx_val, idx_test = train_test_split(idx_temp, test_size=0.6, stratify=y[idx_temp], random_state=SEED)
    y_test = y[idx_test]
    shap_idx = np.sort(np.random.default_rng(SEED).choice(idx_test, size=N_SHAP, replace=False))

    OUT.mkdir(parents=True, exist_ok=True)
    meta = {"seed": SEED, "n_total": len(df), "n_test": len(idx_test), "n_shap": N_SHAP,
            "base_rate_all": float(y.mean()), "base_rate_test": float(y_test.mean()),
            "baseline_accuracy_nobody_readmitted_test": float(1 - y_test.mean()),
            "versions": {"numpy": np.__version__, "pandas": pd.__version__, "scikit-learn": sklearn.__version__,
                         "xgboost": xgboost.__version__, "shap": shap.__version__},
            "models": {}}
    preds = df.loc[idx_test, ["row_id", "readmitted_30d", "discharge_day", "discharge_specialty"]].copy()
    importance = {}
    shap_base = {}

    for name, X in Xs.items():
        model = train(X.loc[idx_train], y[idx_train], X.loc[idx_val], y[idx_val])
        p = model.predict_proba(X.loc[idx_test])[:, 1]
        preds[f"p_{name}"] = p.round(5)
        auc = roc_auc_score(y_test, p)
        acc50 = float(((p >= 0.5) == y_test.to_numpy()).mean())
        meta["models"][name] = {"auc_test": float(auc), "accuracy_at_50pct": acc50,
                                "n_flagged_at_50pct": int((p >= 0.5).sum()), "best_iteration": int(model.best_iteration)}
        print(f"{name}: held-out AUC {auc:.4f}, accuracy@50% {acc50:.4f}, flagged {int((p >= 0.5).sum())}, trees {model.best_iteration}")

        grouped, base = explain(model, X.loc[idx_train], X.loc[shap_idx], group)
        # Row alignment and additivity: base + contributions == model probability (percentage points)
        p_sample = pd.Series(p, index=idx_test).loc[shap_idx].to_numpy() * 100
        err = float(np.abs(grouped.sum(axis=1).to_numpy() + base - p_sample).max())
        print(f"{name}: SHAP additivity max error {err:.4f} percentage points; base value {base:.2f}")
        assert err < 0.5, f"{name}: SHAP does not sum to predicted probability (max err {err:.3f} pp)"
        meta["models"][name]["shap_additivity_max_error_pp"] = err
        grouped.insert(0, "row_id", df.loc[shap_idx, "row_id"].to_numpy())
        grouped.round(4).to_csv(OUT / f"shap_{name}.csv", index=False)
        shap_base[name] = base
        importance[name] = grouped.drop(columns="row_id").abs().mean().sort_values(ascending=False).round(4).to_dict()

    # Assertions on held-out data (not the generator's training-set check)
    assert 0.11 <= meta["base_rate_all"] <= 0.13
    assert meta["models"]["v1"]["auc_test"] >= 0.93, "v1 held-out AUC too low"
    assert 0.68 <= meta["models"]["v2"]["auc_test"] <= 0.75, "v2 held-out AUC outside 0.68-0.75"
    assert (preds["row_id"].to_numpy() == df.loc[idx_test, "row_id"].to_numpy()).all()

    preds.to_csv(OUT / "test_predictions.csv", index=False)

    # Patient feature values for the SHAP sample (display labels, for waterfalls)
    vals = df.loc[shap_idx, ["row_id"] + list(FEATURES)].copy()
    vals["sex"] = vals["sex"]
    vals.to_csv(OUT / "shap_patient_values.csv", index=False)

    # Friday aggregates over the whole synthetic extract (the confounder reveal)
    fri = df["discharge_day"] == "Friday"
    agg = lambda d: {"n": int(len(d)), "readmitted": int(d["readmitted_30d"].sum()), "rate": float(d["readmitted_30d"].mean())}
    elderly = df["discharge_specialty"] == "Elderly care"
    friday = {"friday": agg(df[fri]), "other_days": agg(df[~fri]),
              "share_of_friday_discharges_elderly_care": float(elderly[fri].mean()),
              "share_of_other_day_discharges_elderly_care": float(elderly[~fri].mean()),
              "elderly_care": {"friday": agg(df[elderly & fri]), "other_days": agg(df[elderly & ~fri])},
              "other_wards": {"friday": agg(df[~elderly & fri]), "other_days": agg(df[~elderly & ~fri])}}
    (OUT / "friday.json").write_text(json.dumps(friday, indent=2))

    (OUT / "features.json").write_text(json.dumps(
        {k: {"display": d, "known_at_discharge": kd, "description": desc, "source": SOURCE[k], "why": WHY.get(k, WHY_DEFAULT)}
         for k, (d, kd, desc) in FEATURES.items()}, indent=2))
    (OUT / "shap_summary.json").write_text(json.dumps({"base_value_pp": shap_base, "mean_abs_shap_pp": importance}, indent=2))
    (OUT / "meta.json").write_text(json.dumps(meta, indent=2))
    print("v1 top features:", list(importance["v1"])[:4])
    print("v2 top features:", list(importance["v2"])[:4])
    print(f"wrote exports to {OUT}")


if __name__ == "__main__":
    main()
