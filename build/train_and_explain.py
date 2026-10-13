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

# group -> (display name, known at discharge?, plain-English description)
FEATURES = {
    "age": ("Age", True, "Patient's age in years at discharge."),
    "sex": ("Sex", True, "Recorded sex (male = 1)."),
    "deprivation_decile": ("Deprivation decile", True, "Area deprivation of the patient's home, 1 = most deprived, 10 = least."),
    "long_term_conditions": ("Long-term conditions", True, "Number of long-term conditions on the record."),
    "emergency_admissions_prev_12m": ("Emergency admissions in previous 12 months", True, "Emergency admissions in the year before this one."),
    "length_of_stay_days": ("Length of stay (days)", True, "Days in hospital for this admission."),
    "number_of_medications": ("Number of medications", True, "Medicines the patient is discharged on."),
    "discharge_destination": ("Discharge destination", True, "Home, home with a care package, or care home."),
    "lives_alone": ("Lives alone", True, "Whether the patient lives alone."),
    "discharge_specialty": ("Discharge specialty", True, "The specialty the patient was discharged from."),
    "discharge_day": ("Discharge day", True, "Day of the week of discharge."),
    "gp_contacts_since_discharge": ("GP contacts since discharge", False, "GP contacts in the 30 days after discharge. Only known once those 30 days have passed."),
    "outpatient_followup_attended": ("Outpatient follow-up attended", False, "Whether an outpatient follow-up was attended. Only known afterwards."),
    "community_nursing_visits_since_discharge": ("Community nursing visits since discharge", False, "Community nursing visits in the 30 days after discharge. Only known afterwards."),
}
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
    explainer = shap.TreeExplainer(model, data=shap.sample(X_train, N_BACKGROUND, random_state=SEED),
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
        {k: {"display": d, "known_at_discharge": kd, "description": desc} for k, (d, kd, desc) in FEATURES.items()}, indent=2))
    (OUT / "shap_summary.json").write_text(json.dumps({"base_value_pp": shap_base, "mean_abs_shap_pp": importance}, indent=2))
    (OUT / "meta.json").write_text(json.dumps(meta, indent=2))
    print("v1 top features:", list(importance["v1"])[:4])
    print("v2 top features:", list(importance["v2"])[:4])
    print(f"wrote exports to {OUT}")


if __name__ == "__main__":
    main()
