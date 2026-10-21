"""Per-patient explanations from the exported SHAP values (pandas only; no Streamlit)."""
import pandas as pd

# Which Stage 5 statements the explanation genuinely supports. The page asserts its own
# statement list agrees with this, so the memo and the page cannot drift apart.
STATEMENT_SUPPORTED = {
    "causal": False,
    "describe": True,
    "fair": False,
    "uncertain": True,
    # Reserve statements, removed to fit the 35-minute route. To reinstate, uncomment these and
    # the matching entries in bringing_people.py:
    # "safe": False,
    # "relied": True,
}

# The Stage 2 "could the model use this on a real patient?" questions, one of each kind:
# known before admission, built up during the stay (so available at discharge), and recorded
# only after discharge.
LEAKAGE_QUESTIONS = [
    "gp_contacts_since_discharge",  # after discharge: No
    "age",  # known before admission: Yes
    "length_of_stay_days",  # built up during the stay, available at discharge: Yes
    # Reserve questions, removed to fit the 35-minute route. Reinstate by uncommenting:
    # "outpatient_followup_attended",  # after discharge: No (the appointment itself is weeks later)
    # "emergency_admissions_prev_12m",  # known before admission: Yes
]

YES_NO = {0: "No", 1: "Yes"}
DAY_ORDER = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def display_value(feature: str, value) -> str:
    if feature == "lives_alone":
        return YES_NO[int(value)]
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def pick_patients(preds: pd.DataFrame, shap: pd.DataFrame) -> dict:
    """Example patients from the SHAP sample. high / typical / low follow the slides' choices:
    the highest predicted risk, the one closest to the median, and the lowest predicted risk
    among patients who were not readmitted. elevated is the one used in the exercise (see below)."""
    d = preds.set_index("row_id").loc[shap["row_id"]]
    p = d["p_v2"]
    high = int(p.idxmax())
    low = int(p[d["readmitted_30d"] == 0].idxmin())
    mid = int((p - p.median()).abs().idxmin())
    # A patient with a clearly elevated risk (40-50%) who was not readmitted and has at least one
    # strong factor pushing risk down, so the waterfall shows both red and blue bars.
    # Chosen as the one with the largest single downward contribution.
    contribs = shap.set_index("row_id").drop(columns=[c for c in shap.columns if c == "row_id"], errors="ignore")
    biggest_down = contribs.min(axis=1)
    mask = (p >= 0.40) & (p <= 0.50) & (d["readmitted_30d"] == 0)
    elevated = int(biggest_down[mask.to_numpy()].idxmin())
    return {"elevated": elevated, "high": high, "typical": mid, "low": low}


def patient_explanation(row_id: int, preds, shap, values, features, base_pp: float, top: int = 6) -> dict:
    """Contributions in percentage points for one patient. base + sum(contributions) = f(x)."""
    s = shap.set_index("row_id").loc[row_id]
    v = values.set_index("row_id").loc[row_id]
    fx = float(preds.set_index("row_id").loc[row_id, "p_v2"]) * 100
    items = [
        {
            "feature": k,
            "label": f"{features[k]['display']} = {display_value(k, v[k])}",
            "value": float(s[k]),
        }
        for k in s.index
    ]
    items.sort(key=lambda i: abs(i["value"]), reverse=True)
    shown, rest = items[:top], items[top:]
    other = {"label": f"{len(rest)} other factors", "value": float(sum(i["value"] for i in rest))} if rest else None
    return {
        "row_id": row_id,
        "base": base_pp,
        "fx": fx,
        "shown": shown,
        "other": other,
        "all": items,
        "readmitted": int(preds.set_index("row_id").loc[row_id, "readmitted_30d"]),
    }
