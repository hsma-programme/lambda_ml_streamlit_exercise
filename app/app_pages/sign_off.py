import pandas as pd
import streamlit as st

import interventions as iv
import memo
import ui

meta = ui.load_meta()
features = ui.load_features()
state = st.session_state
g = memo.gather(state, features)

ui.stage_header(
    "6. Sign-off: Do we put it into use?",
    "Time to decide. Your group's earlier answers are gathered below, so you can see what you have "
    "found before you commit.",
    minutes="stage6",
)
ui.task_box(
    "Review what your group decided, record your final verdict and the conditions you would attach, "
    "then download the sign-off memo for the debrief."
)

# Missing decisions are listed first, so a partial journey is visible rather than silently summarised.
if g["missing"]:
    st.warning(
        "**Some decisions haven't been made yet.** You can still sign off, but the memo will say these are missing:\n\n"
        + "\n".join(f"- {m}" for m in g["missing"])
    )

st.subheader("What your group found")
left, right = st.columns(2, gap="large")
with left:
    v1, v2 = meta["models"]["v1"], meta["models"]["v2"]
    st.markdown(
        f"""
- **The submitted model (v1):** AUC {v1['auc_test']:.2f}, {v1['accuracy_at_50pct']:.1%} accurate on held-out patients.
- **Without the leaked information (v2):** AUC {v2['auc_test']:.2f}, {v2['accuracy_at_50pct']:.1%} accurate.
- **Capacity:** {g['capacity'] or 'not recorded'} calls per 1,000 discharges.
- **Trade-off accepted:** {g['tradeoff'] or 'not recorded'}
"""
    )
with right:
    leak = (
        f"{g['leakage_right']} of {g['leakage_total']} 'same information in real use?' questions right"
        if g["leakage_total"]
        else "not recorded"
    )
    stm = (
        f"{g['statements_right']} of {g['statements_total']} explanation statements judged correctly"
        if g["statements_right"] is not None
        else "not recorded"
    )
    st.markdown(
        f"""
- **Leakage check:** {leak}
- **Explanation statements:** {stm}
- **Uses reviewed:** {len(g['uses'])} of {len(iv.INTERVENTIONS)}
"""
    )

if g["uses"]:
    st.markdown("**The uses your group reviewed**")
    st.dataframe(
        pd.DataFrame(
            [
                {
                    "Use": iv.BY_KEY[k]["title"],
                    "Support?": r["support"],
                    "Harms to investigate": "; ".join(r["harms"]) or "none chosen",
                    "Medical device?": r["device"],
                }
                for k, r in g["uses"].items()
            ]
        ),
        hide_index=True,
        width="stretch",
    )

st.divider()
state_box = st.container()  # filled in below, once the verdict widgets have updated

st.subheader("Your final verdict")
# Seed keyed widgets from the saved plain keys: widget state is dropped when this page isn't rendered.
if g["final_verdict"]:
    state.setdefault("final_verdict_widget", g["final_verdict"])
if g["conditions"]:
    state.setdefault("conditions_widget", g["conditions"])
if g["owner"]:
    state.setdefault("owner_widget", g["owner"])
if g["pause_criteria"]:
    state.setdefault("pause_widget", g["pause_criteria"])
if g["final_reason"]:
    state.setdefault("final_reason_widget", g["final_reason"])

verdict = st.radio("What does your group decide?", memo.VERDICTS, index=None, key="final_verdict_widget")
reason = st.text_input("Optional: one line on why", key="final_reason_widget")
conditions = st.multiselect(
    "Conditions your group would attach",
    memo.CONDITIONS,
    key="conditions_widget",
    help="Things that should be true before the model goes into use, or while it is in use.",
)
owner = st.text_input(
    "Accountable owner, by role (optional)",
    key="owner_widget",
    placeholder="e.g. Director of Operations",
    help="The model was built in-house, so someone inside the organisation owns it.",
)
pause = st.text_area(
    "What would make you pause or stop using it? (optional)",
    key="pause_widget",
    placeholder="e.g. predicted risks stop matching what actually happens, or calls are going to a narrower group of patients",
)

state["final_verdict"] = verdict
state["final_reason"] = reason.strip() or None
state["conditions"] = conditions
state["owner"] = owner.strip() or None
state["pause_criteria"] = pause.strip() or None

if verdict == "Approve" and not conditions:
    st.info(
        "Your group has approved with no conditions. Is that what you intend? The questions raised in Stages 2 to 5 "
        "would normally become conditions."
    )
elif verdict == "Approve with conditions" and not conditions:
    st.info("You have chosen 'approve with conditions' but haven't listed any. Which conditions would you attach?")
elif verdict == "Reject" and conditions:
    st.info("Conditions apply to an approval. If you are rejecting, what would have to change for you to reconsider?")

# Re-gather so the memo reflects what has just been entered.
g = memo.gather(state, features)

with state_box:
    st.subheader("Where did your view end up?")
    j1, j2, j3 = st.columns(3)
    for col, label, value in (
        (j1, "First impression (Stage 0)", g["initial_verdict"]),
        (j2, "After seeing v2 (Stage 2)", g["stage2_verdict"]),
        (j3, "Final verdict (now)", g["final_verdict"]),
    ):
        with col.container(border=True):
            st.markdown(f"**{label}**\n\n{value or 'not recorded yet'}")
    if g["initial_verdict"] and g["final_verdict"]:
        if g["initial_verdict"] == g["final_verdict"]:
            st.caption("Your final verdict is the same as your first impression. What, if anything, did the evidence add?")
        else:
            st.caption(
                f"Your view moved from **{g['initial_verdict']}** to **{g['final_verdict']}**. "
                "What did you see that changed it?"
            )
st.divider()
st.subheader("Sign-off memo")
st.markdown("A one-page record of your group's decisions, for the debrief.")
text = memo.build_memo(g, meta)
st.download_button(
    "Download the sign-off memo",
    text,
    file_name="readmitrisk-sign-off-memo.md",
    mime="text/markdown",
    type="primary",
)
with st.expander("Preview the memo"):
    st.markdown(text)

st.divider()
with st.expander("Extension: more to discuss if you have time"):
    st.markdown(
        "These are not part of the main route and are not timed. Pick the one or two your group would "
        "most like to talk about."
    )
    for stage, prompt in ui.DISCUSSION:
        st.markdown(f"**{stage}**\n\n{prompt}")

ui.synthetic_notice()
