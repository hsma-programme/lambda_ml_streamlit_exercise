import streamlit as st

import ui

VERDICTS = ["Approve", "Approve with conditions", "Reject"]

meta = ui.load_meta()
v1 = meta["models"]["v1"]

ui.stage_header("0. Briefing: Model sign-off for ReadmitRisk v1", minutes="briefing")
ui.task_box(
    "You are the sign-off panel for a new risk model that our own analytics team has built. "
    "Read the team's summary, then "
    "record your group's **first impression** before you investigate anything. "
    "You will come back to it at the end."
)
st.info(
    "**There is no right or wrong answer on this page.** Your first impression is just a starting point, and "
    "you will compare it with your final verdict at the end. Most of this exercise is judgement calls like this "
    "one, and the app won't mark them. A few questions later on do have clearer answers, and they will say so."
)

left, right = st.columns([0.55, 0.45], gap="large")

with left:
    st.subheader("The analytics team's summary")
    st.markdown(
        f"""
**ReadmitRisk v1** predicts which patients will have an unplanned emergency
readmission within 30 days of leaving hospital.

- **{v1['accuracy_at_50pct']:.1%} accurate**
- **AUC {v1['auc_test']:.2f}** (on a scale from 0.5, no better than a coin toss, to 1.0, a perfect model)
- Tested on {meta['n_test']:,} patients the model had not seen during training

*"We propose using it to identify patients for a post-discharge support call."*
"""
    )
    with st.expander("What is AUC?", expanded=True):
        st.markdown(
            "Another way of scoring a model, which you'll often see quoted alongside accuracy. "
            "You'll try out what it measures in Stage 1."
        )
    st.caption(f"Accuracy is quoted at the usual 50% cut-off: a patient is flagged if the model gives them a risk of 50% or more.")

with right:
    st.subheader("Your role")
    st.markdown(
        """
Our in-house analytics team (analysts and data scientists) has built this model and wants
to put it into use. Your group must decide whether to
**approve** it, **approve with conditions**, or **reject** it.

**What the support call involves (working assumption):** a member of the community
discharge team (this could be a nurse or a care coordinator; the call stays a wellbeing check either
way) phones flagged patients within two working days of discharge for a **wellbeing
check only**. The call is limited to **signposting** the patient to support and **recording** the
conversation: it does not include any clinical assessment. The software only produces the list,
prioritising those flagged by the model as being at highest risk of being readmitted, based on the
likelihood threshold we choose.

Because we built it ourselves, there is no supplier to hold to account. If it goes into use,
responsibility for it, and for its safety, sits with us.
"""
    )
    st.caption(
        "The call's purpose is a working assumption for this exercise. "
        "Later stages test what changes if the use changes."
    )

ui.synthetic_notice()
st.divider()

st.subheader("Your first impression")
locked = ui.get_decision("initial_verdict")

if locked:
    st.success(f"First impression recorded: **{locked}**")
    reason = ui.get_decision("initial_reason")
    if reason:
        st.markdown(f"Reason given: *{reason}*")
    st.caption("This is kept as it is, and compared with your final verdict at sign-off.")
else:
    verdict = st.radio(
        "On the pitch alone, what would your group do?",
        VERDICTS,
        index=None,
        key="briefing_verdict_widget",
        help="There is no right answer yet. This is your starting position.",
    )
    reason = st.text_input(
        "Optional: one line on why",
        key="briefing_reason_widget",
        help="Free text is optional. Nothing else in the exercise needs typing.",
    )
    if st.button("Record our first impression", disabled=verdict is None, type="primary"):
        ui.record_decision("initial_verdict", verdict)
        ui.record_decision("initial_reason", reason.strip() or None)
        st.rerun()

ui.next_stage(
    "app_pages/is_it_any_good.py",
    "1. Performance: Is it any good?",
    ui.get_decision("initial_verdict") is not None,
    "Record your first impression, and a button to the next stage will appear here.",
)
