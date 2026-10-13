import pandas as pd
import streamlit as st

import charts
import metrics
import ui

TRADEOFFS = [
    "Reach as many readmissions as we can, even if more calls are wasted",
    "Keep wasted calls low, even if we miss more readmissions",
    "Stay within what the team can actually phone, whatever the numbers say",
]

meta = ui.load_meta()
preds = ui.load_predictions()
v1 = meta["models"]["v1"]
base = metrics.baseline_accuracy(preds["readmitted_30d"])

ui.stage_header(
    "1. Is it any good?",
    "We are testing the vendor's model, ReadmitRisk v1, on patients it never saw during training.",
)
ui.task_box(
    "Check the vendor's headline number, then decide how many patients per 1,000 discharges "
    "your team could realistically phone and what you would trade off."
)

st.subheader("The headline accuracy")
c1, c2 = st.columns(2)
with c1:
    with st.container(border=True):
        st.metric("A 'model' that predicts *nobody* is readmitted", f"{base:.0%} accurate")
        st.caption("It never finds a single readmission, and still scores this well.")
with c2:
    with st.container(border=True):
        st.metric("ReadmitRisk v1 at the usual 50% cut-off", f"{v1['accuracy_at_50pct']:.1%} accurate")
        st.caption(
            f"It flags {v1['n_flagged_at_50pct']} of {meta['n_test']:,} patients "
            "(a patient is flagged if their predicted risk is 50% or more)."
        )
st.markdown(
    f"Only about **{meta['base_rate_test']:.0%}** of patients are readmitted, so doing nothing already scores "
    f"{base:.0%}. When what you are predicting is rare, **accuracy mostly tells you how rare it is**. "
    "A better question is how well the model finds the patients who are readmitted, and what it costs us in calls."
)

st.divider()
st.subheader("Who would we phone?")
st.markdown(
    "The model gives each patient a **risk**, not a yes or no. Someone has to choose a cut-off, "
    "and in practice that is set by **how many calls the team can make**. Out of every **1,000 discharges**, "
    "how many of the highest-risk patients can you phone?"
)

cap = st.slider(
    "Patients we can phone per 1,000 discharges",
    20,
    300,
    ui.capacity(),
    step=10,
    help="Out of every 1,000 discharges, the number of highest-risk patients your team could phone.",
)
st.session_state["capacity_choice"] = cap

out = metrics.call_outcomes(preds["p_v1"], preds["readmitted_30d"], cap)

left, right = st.columns([0.62, 0.38], gap="large")
with left:
    st.plotly_chart(charts.icon_array(out), width="stretch")
    st.caption(
        "Each marker is one of 1,000 discharges. The grid shows what actually happened to patients in the "
        "held-out test data: who we would have phoned, and who was in fact readmitted."
    )
    with st.expander("Show these counts as a table"):
        st.dataframe(
            pd.DataFrame(
                {
                    "Group": [label for _, label in metrics.GROUPS],
                    "Per 1,000 discharges": [out[k] for k, _ in metrics.GROUPS],
                }
            ),
            hide_index=True,
            width="stretch",
        )
with right:
    st.markdown(
        f"""
**Calling the {cap} highest-risk patients** (anyone with a predicted risk of {out['cutoff']:.0%} or more):

- **Precision:** {out['called_readmitted']} of our {cap} calls reach someone who was readmitted
  (**{out['precision']:.0%}**). Calling at random would manage about **{out['random_precision']:.0%}**.
- **Recall:** we reach **{out['called_readmitted']} of the {out['readmitted_total']}** patients who were readmitted
  (**{out['recall']:.0%}**).
- **Accuracy** is now {out['accuracy']:.0%}, a different number from the vendor's headline.
"""
    )
    st.caption(
        f"Counts are scaled from {meta['n_test']:,} test patients to 1,000, so they can be out by a few patients. "
        "They describe who *was* readmitted, not readmissions a call would have prevented."
    )

st.divider()
st.subheader("Your group's decision")
st.markdown("There is no single right answer here. Discuss, then record where your group lands.")
locked = ui.get_decision("tradeoff_choice")
if locked:
    st.success(
        f"Recorded: capacity of **{ui.get_decision('capacity_recorded')} calls per 1,000**; priority: **{locked}**"
    )
    st.markdown("**Things to weigh, whichever way you chose**")
    st.markdown(
        """
- **Staff time:** each call takes time away from something else. Is the team's real capacity the number you chose?
- **Wasted calls:** a call to someone who would have been fine still costs time, and may worry them.
- **Missed readmissions:** patients who were readmitted but never phoned are the ones a service like this exists for.
- **Who is on the list?** A list built from past use of services may under-represent people who use them less.
"""
    )
else:
    choice = st.radio("Which trade-off would your group accept?", TRADEOFFS, index=None, key="tradeoff_widget")
    if st.button("Record our decision", disabled=choice is None, type="primary"):
        ui.record_decision("tradeoff_choice", choice)
        ui.record_decision("capacity_recorded", cap)
        st.rerun()

st.markdown("**Discuss:** the numbers look very strong. What would you want to ask the vendor before signing this off?")
ui.synthetic_notice()
