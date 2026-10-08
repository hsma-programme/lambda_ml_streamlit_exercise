"""Generate synthetic 30-day emergency readmission data (offline build step).

All data is synthetic and seeded. The outcome comes from a known logistic model.
Planted features:
  * leakage: three columns recorded AFTER discharge, generated from the outcome
  * confounder: Friday discharges come disproportionately from elderly-care wards;
    Friday has NO effect on readmission once ward/frailty is accounted for
  * fairness hook: deprivation has a DIRECT effect on readmission in this synthetic
    mechanism (it is not a pure proxy). Teach "predictive association does not show
    which intervention would help", not a claim about real-world causes of deprivation

Run:  python build/generate_data.py
Writes build/out/discharges.csv
"""
from pathlib import Path

import numpy as np
import pandas as pd

SEED = 42
N = 20_000
TARGET_RATE = 0.12
HIDDEN_SD = 2.4
OUT = Path(__file__).parent / "out" / "discharges.csv"

SPECIALTIES = ["Elderly care", "General medicine", "Respiratory", "Cardiology", "General surgery", "Orthopaedics"]
SPEC_P = [0.20, 0.25, 0.15, 0.12, 0.14, 0.14]
# Probability of a Friday discharge, by specialty (the confounder)
FRIDAY_P = {"Elderly care": 0.65, "General medicine": 0.12, "Respiratory": 0.12,
            "Cardiology": 0.10, "General surgery": 0.10, "Orthopaedics": 0.10}
OTHER_DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Saturday", "Sunday"]
SPEC_EFFECT = {"Elderly care": 0.25, "General medicine": 0.05, "Respiratory": 0.30,
               "Cardiology": 0.0, "General surgery": -0.5, "Orthopaedics": -0.6}


def sigmoid(x):
    return 1 / (1 + np.exp(-x))


def generate(n=N, seed=SEED):
    rng = np.random.default_rng(seed)
    spec = rng.choice(SPECIALTIES, size=n, p=SPEC_P)

    # Age depends on specialty
    age_mean = pd.Series(spec).map({"Elderly care": 83, "General medicine": 68, "Respiratory": 70,
                                    "Cardiology": 66, "General surgery": 58, "Orthopaedics": 64}).to_numpy()
    age = np.clip(rng.normal(age_mean, 12), 18, 100).round().astype(int)
    sex = rng.choice(["Female", "Male"], size=n)
    deprivation = rng.integers(1, 11, size=n)  # 1 = most deprived, 10 = least

    frailty = np.clip((age - 60) / 20 + rng.normal(0, 0.5, n), 0, None)
    ltc = np.clip(rng.poisson(0.6 + 1.2 * frailty + (10 - deprivation) * 0.08), 0, 10)
    prev_emerg = np.clip(rng.poisson(0.25 + 0.35 * ltc * 0.5 + (10 - deprivation) * 0.03), 0, 10)
    los = np.clip(rng.gamma(2.0, 1.5 + 1.5 * frailty), 1, 40).round().astype(int)
    meds = np.clip(rng.poisson(3 + 1.2 * ltc + 0.03 * (age - 60)), 0, 25)
    lives_alone = rng.random(n) < sigmoid(-1.0 + 0.8 * frailty - 0.1 * (deprivation - 5))
    p_care = sigmoid(-3.2 + 1.3 * frailty)
    p_cc = sigmoid(-3.5 + 1.0 * frailty + 0.6 * lives_alone)
    u = rng.random(n)
    dest = np.where(u < p_care, "Care home", np.where(u < p_care + p_cc, "Home with care package", "Home"))

    friday_p = pd.Series(spec).map(FRIDAY_P).to_numpy()
    is_friday = rng.random(n) < friday_p
    day = np.where(is_friday, "Friday", rng.choice(OTHER_DAYS, size=n))

    # Unobserved risk (things the data doesn't capture) keeps a clean model realistically modest
    hidden = rng.normal(0, HIDDEN_SD, n)

    def outcome_prob(intercept):
        z = (intercept + hidden
             + 0.35 * ltc
             + 0.25 * prev_emerg
             + 0.015 * (age - 70)
             + 0.03 * los
             + 0.02 * meds
             + 0.5 * frailty
             + 0.12 * (5.5 - deprivation)
             + 0.3 * lives_alone
             + 0.4 * (dest == "Care home") - 0.2 * (dest == "Home with care package")
             + pd.Series(spec).map(SPEC_EFFECT).to_numpy())
        return sigmoid(z)

    # Bisect the intercept so the base rate hits the target
    lo, hi = -10.0, 2.0
    for _ in range(60):
        mid = (lo + hi) / 2
        if outcome_prob(mid).mean() > TARGET_RATE:
            hi = mid
        else:
            lo = mid
    p = outcome_prob((lo + hi) / 2)
    readmitted = (rng.random(n) < p).astype(int)

    # Leaky columns: extract pulled 30 days AFTER discharge, generated FROM the outcome
    gp = rng.poisson(np.where(readmitted == 1, 3.2, 0.9))
    opd = np.where(readmitted == 1, rng.random(n) < 0.15, rng.random(n) < 0.70).astype(int)
    nursing = rng.poisson(np.where(readmitted == 1, 4.0, 0.7))

    return pd.DataFrame({
        "age": age, "sex": sex, "deprivation_decile": deprivation,
        "long_term_conditions": ltc, "emergency_admissions_prev_12m": prev_emerg,
        "length_of_stay_days": los, "number_of_medications": meds,
        "discharge_destination": dest, "lives_alone": lives_alone.astype(int),
        "discharge_specialty": spec, "discharge_day": day,
        "gp_contacts_since_discharge": gp,
        "outpatient_followup_attended": opd,
        "community_nursing_visits_since_discharge": nursing,
        "readmitted_30d": readmitted,
    })


def check(df):
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import roc_auc_score

    rate = df.readmitted_30d.mean()
    assert 0.11 <= rate <= 0.13, f"base rate {rate:.3f} outside 11-13%"
    fri = df.discharge_day == "Friday"
    raw_fri, raw_other = df.readmitted_30d[fri].mean(), df.readmitted_30d[~fri].mean()
    assert raw_fri > raw_other * 1.15, "Friday confounder too weak in raw rates"
    grp = df.groupby(["discharge_specialty", fri.rename("fri")]).readmitted_30d.agg(["mean", "count"]).unstack()
    by_ward = grp["mean"]
    gap = (by_ward[True] - by_ward[False]).abs().max()
    print(f"base rate {rate:.3%}; Friday raw {raw_fri:.2%} vs other {raw_other:.2%}; max within-ward Friday gap {gap:.2%}")
    print(by_ward.round(3))

    # Within-specialty Friday difference should be consistent with sampling noise, not a real effect
    se = np.sqrt(sum(by_ward[f] * (1 - by_ward[f]) / grp["count"][f] for f in (True, False)))
    z = ((by_ward[True] - by_ward[False]) / se).abs()
    assert z.max() < 3.5, f"within-specialty Friday gap larger than sampling noise (max |z|={z.max():.1f})"
    weights = grp["count"][True]
    pooled = ((by_ward[True] - by_ward[False]) * weights).sum() / weights.sum()
    assert abs(pooled) < 0.01, f"pooled within-specialty Friday gap {pooled:.2%} not close to zero"
    print(f"within-specialty Friday gaps: max |z|={z.max():.1f}, pooled gap {pooled:+.2%}")

    # Quick linear sanity check on discharge-time signal vs leakage (the real check is in train_and_explain.py)
    num = pd.get_dummies(df.drop(columns=["readmitted_30d"]), drop_first=True).astype(float)
    leak = ["gp_contacts_since_discharge", "outpatient_followup_attended", "community_nursing_visits_since_discharge"]
    clean = num.drop(columns=leak)
    for name, X in [("all columns", num), ("discharge-time only", clean)]:
        m = LogisticRegression(max_iter=2000).fit((X - X.mean()) / X.std(), df.readmitted_30d)
        print(f"logistic AUC ({name}): {roc_auc_score(df.readmitted_30d, m.predict_proba((X - X.mean()) / X.std())[:, 1]):.3f}")


if __name__ == "__main__":
    df = generate()
    check(df)
    OUT.parent.mkdir(exist_ok=True)
    df.to_csv(OUT, index=False)
    print(f"wrote {len(df):,} rows to {OUT}")
