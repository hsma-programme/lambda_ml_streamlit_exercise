"""Per-patient explanations from the exported SHAP values (pandas only; no Streamlit)."""
import pandas as pd

YES_NO = {0: "No", 1: "Yes"}
DAY_ORDER = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def display_value(feature: str, value) -> str:
    if feature == "lives_alone":
        return YES_NO[int(value)]
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def pick_patients(preds: pd.DataFrame, shap: pd.DataFrame) -> dict:
    """High / typical / low-risk patients from the SHAP sample, following the slides' choices:
    the highest predicted risk, the one closest to the median, and the lowest predicted risk
    among patients who were not readmitted."""
    d = preds.set_index("row_id").loc[shap["row_id"]]
    p = d["p_v2"]
    high = int(p.idxmax())
    low = int(p[d["readmitted_30d"] == 0].idxmin())
    mid = int((p - p.median()).abs().idxmin())
    return {"high": high, "typical": mid, "low": low}


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
