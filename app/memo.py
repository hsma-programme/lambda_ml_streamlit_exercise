"""Gather the group's decisions and build the sign-off memo (no Streamlit, so it can be tested)."""
import explain
import interventions as iv

CONDITIONS = [
    "Local validation: test it on our own recent discharges before it goes live",
    "Calibration check: do the predicted risks match what actually happens here?",
    "Equity check: performance, and who gets on the call list, by age, deprivation and ethnicity",
    "Evaluate whether the calls help: compare with usual care, or random allocation of limited calls",
    "A written intended purpose, with reassessment if the use changes",
    "Clinical safety management: a named Clinical Safety Officer, hazard log and safety case",
    "An accountable owner, named by role",
    "Ongoing monitoring for drift, with criteria for pausing or stopping use",
    "Staff can see why a patient is flagged and can overrule it",
    "Review the cut-off and call capacity at set intervals",
]

VERDICTS = ["Approve", "Approve with conditions", "Reject"]


def gather(state, features: dict) -> dict:
    """Pull the group's decisions out of session state into one plain dict."""
    known = {k: v for k, v in (state.get("known_answers") or {}).items() if k in explain.LEAKAGE_QUESTIONS}
    leakage_total = len(known)
    leakage_right = sum(
        1 for k, a in known.items() if k in features and a.startswith("Yes") == features[k]["known_at_discharge"]
    )
    uses = state.get("interventions") or {}
    statements = state.get("stage4_statements")
    compulsory = [i["key"] for i in iv.INTERVENTIONS if i["compulsory"]]

    missing = []
    if not state.get("initial_verdict"):
        missing.append("Stage 0: your first impression")
    if not state.get("tradeoff_choice"):
        missing.append("Stage 2: the call capacity trade-off")
    if leakage_total < len(explain.LEAKAGE_QUESTIONS):
        missing.append("Stage 3: the 'could the model use this?' questions")
    if not state.get("stage2_verdict"):
        missing.append("Stage 3: your view after seeing v2")
    done = [k for k in compulsory if k in uses]
    if len(done) < len(compulsory):
        missing.append(f"Stage 4: {len(done)} of {len(compulsory)} compulsory uses recorded")
    if statements is None:
        missing.append("Stage 5: the explanation statements")

    return {
        "initial_verdict": state.get("initial_verdict"),
        "initial_reason": state.get("initial_reason"),
        "stage2_verdict": state.get("stage2_verdict"),
        "final_verdict": state.get("final_verdict"),
        "final_reason": state.get("final_reason"),
        "capacity": state.get("capacity_recorded") or state.get("capacity_choice"),
        "tradeoff": state.get("tradeoff_choice"),
        "leakage_right": leakage_right,
        "leakage_total": leakage_total,
        "uses": uses,
        "statements": statements,
        "statements_total": len(explain.STATEMENT_SUPPORTED),
        "statements_right": (
            None
            if statements is None
            else sum(1 for k, ok in explain.STATEMENT_SUPPORTED.items() if statements.get(k) == ok)
        ),
        "conditions": state.get("conditions") or [],
        "owner": state.get("owner"),
        "pause_criteria": state.get("pause_criteria"),
        "missing": missing,
    }


def build_memo(g: dict, meta: dict) -> str:
    v1, v2 = meta["models"]["v1"], meta["models"]["v2"]
    L = []
    add = L.append
    add("# Sign-off memo: ReadmitRisk v1")
    add("")
    add("> **Synthetic exercise.** This memo records a training exercise. All data is synthetic, no real patients "
        "are involved, and nothing here is a real approval decision.")
    add("")
    add("## Verdict")
    add("")
    add(f"- **First impression:** {g['initial_verdict'] or 'not recorded'}"
        + (f" ({g['initial_reason']})" if g.get("initial_reason") else ""))
    add(f"- **After seeing the model without the leaked information:** {g['stage2_verdict'] or 'not recorded'}")
    add(f"- **Final verdict:** {g['final_verdict'] or 'not recorded'}"
        + (f" ({g['final_reason']})" if g.get("final_reason") else ""))
    add("")
    add("## What we found")
    add("")
    add(f"- The submitted model (v1) scored AUC {v1['auc_test']:.2f} and {v1['accuracy_at_50pct']:.1%} accuracy on "
        f"held-out patients. Without the information it would not have at discharge (v2), AUC was "
        f"{v2['auc_test']:.2f} and accuracy {v2['accuracy_at_50pct']:.1%}.")
    add(f"- Call capacity considered: {g['capacity'] or 'not recorded'} per 1,000 discharges. "
        f"Trade-off our group would accept: {g['tradeoff'] or 'not recorded'}.")
    if g["leakage_total"]:
        add(f"- Data leakage: we identified which factors the model could and could not use at the moment of "
            f"prediction ({g['leakage_right']} of {g['leakage_total']} correct).")
    if g.get("statements_right") is not None:
        add(f"- Explanation statements: {g['statements_right']} of {g['statements_total']} judged correctly.")
    add("")
    add("## Uses considered")
    add("")
    if g["uses"]:
        add("| Use | Support? | Harms to investigate | Medical device? |")
        add("|---|---|---|---|")
        for key, rec in g["uses"].items():
            title = iv.BY_KEY[key]["title"]
            harms = "; ".join(rec["harms"]) if rec["harms"] else "none chosen"
            add(f"| {title} | {rec['support']} | {harms} | {rec['device']} |")
    else:
        add("No uses recorded.")
    add("")
    add("## Conditions of approval")
    add("")
    if g["conditions"]:
        for c in g["conditions"]:
            add(f"- {c}")
    else:
        add("None chosen.")
    add("")
    add(f"- **Accountable owner (role):** {g['owner'] or 'not recorded'}")
    add(f"- **Criteria for pausing or stopping use:** {g['pause_criteria'] or 'not recorded'}")
    add("")
    if g["missing"]:
        add("## Decisions not yet made")
        add("")
        for m in g["missing"]:
            add(f"- {m}")
        add("")
    return "\n".join(L)
