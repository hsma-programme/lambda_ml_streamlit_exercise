import pandas as pd
import streamlit as st

import charts
import metrics
import ui

TRADEOFFS = [
    "Reach as many of the patients who would be readmitted as we can, accepting more wasted calls",
    "Make sure most calls reach someone who would be readmitted, accepting that we miss more patients",
    "We can't settle this until we know whether the calls actually help",
]

meta = ui.load_meta()
preds = ui.load_predictions()
v2 = meta["models"]["v2"]

ui.stage_header(
    "3. Tradeoffs: Who would we phone?",
    "From here on we use the honest model, v2, which only uses what we know at discharge. AUC tells you how well "
    "it puts patients in order, but not where to draw the line.",
    minutes="stage3",
)
ui.task_box(
    "Decide how many patients per 1,000 discharges your team could realistically phone, "
    "and what you would trade off."
)

st.markdown(
    "The model gives each patient a **risk**, not a yes or no. Someone has to choose a cut-off, "
    "and in practice that is set by **how many calls the team can make**. Out of every **1,000 discharges**, "
    "how many of the highest-risk patients can you phone?"
)
st.info(
    "**This is a thought experiment.** Nobody in this data was actually phoned. Imagine we had run the service "
    "on these past patients: the model ranks them, and for the highest-risk ones it **would have recommended a call**. "
    "We can then check its recommendations against what really happened to each patient afterwards."
)

# Seed the keyed widget from the plain key (widget state is dropped when the page isn't
# rendered). Passing a changing default via value= would change the widget's identity on
# every move and reset it.
st.session_state.setdefault("capacity_slider", ui.capacity())
cap = st.slider(
    "Patients we can phone per 1,000 discharges",
    20,
    300,
    step=10,
    key="capacity_slider",
    help="Out of every 1,000 discharges, the number of highest-risk patients your team could phone.",
)
st.session_state["capacity_choice"] = cap

out = metrics.call_outcomes(preds["p_v2"], preds["readmitted_30d"], cap)

# The cut-off is the key idea: capacity sets it. Show it large, with how far it just moved.
prev_cutoff = st.session_state.get("_prev_cutoff")
cutoff_delta = None
if prev_cutoff is not None and abs(out["cutoff"] - prev_cutoff) >= 0.0005:
    cutoff_delta = f"{(out['cutoff'] - prev_cutoff) * 100:+.0f} percentage points since you last moved the slider"
st.session_state["_prev_cutoff"] = out["cutoff"]

with st.container(border=True):
    k1, k2 = st.columns([0.35, 0.65], gap="large")
    k1.metric("Calls we can make, per 1,000 discharges", f"{cap}")
    k2.metric(
        "So the cut-off is: phone anyone with a predicted risk of at least",
        f"{out['cutoff']:.0%}",
        cutoff_delta,
        delta_color="off",
    )
    st.markdown(
        "**This is the cut-off.** It isn't chosen directly: it follows from how many calls you can make. "
        "More calls means a lower bar for the model to recommend a call, so more patients are included, "
        "and more of them are people who would have been fine. **Move the slider and watch it change.**"
    )

left, right = st.columns([0.62, 0.38], gap="large")
with left:
    st.plotly_chart(charts.icon_array(out), width="stretch")
    st.caption(
        "Each marker is one of 1,000 past discharges. \"Model would recommend a call\" is its recommendation (no calls were made). "
        "\"In reality\" is what actually happened to the patient."
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
**If we followed v2 and phoned the {cap} highest-risk patients** (anyone with a predicted risk of {out['cutoff']:.0%} or more):

- **Precision:** {out['called_readmitted']} of those {cap} calls would reach someone who was readmitted
  (**{out['precision']:.0%}**). Calling at random would manage about **{out['random_precision']:.0%}**.
- **Recall:** we would reach **{out['called_readmitted']} of the {out['readmitted_total']}** patients who were readmitted
  (**{out['recall']:.0%}**).
- **Accuracy** is now {out['accuracy']:.0%}, a different number from v2's {v2['accuracy_at_50pct']:.0%} at the usual 50% cut-off.
"""
    )
    st.caption(
        f"Counts are scaled from {meta['n_test']:,} test patients to 1,000, so they can be out by a few patients. "
        "They describe who was readmitted anyway, not readmissions that a call would have prevented. "
        "Ranking by risk beats calling at random here, but you would need to test that in your own hospital: "
        "ranking by risk is not the same as knowing a call will help."
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
- **Do the calls help at all?** Everything above is about who the model would pick, not whether a call changes what happens next. That is a separate question, and it comes back at sign-off.
- **Wasted calls:** a call to someone who would have been fine still costs time, and may worry them.
- **Missed readmissions:** patients who were readmitted but never phoned are the ones a service like this exists for.
- **Who does the model recommend?** A list built from past use of services may under-represent people who use them less.
"""
    )
else:
    choice = st.radio("Which trade-off would your group accept?", TRADEOFFS, index=None, key="tradeoff_widget")
    if st.button("Record our decision", disabled=choice is None, type="primary"):
        ui.record_decision("tradeoff_choice", choice)
        ui.record_decision("capacity_recorded", cap)
        st.rerun()

ui.next_stage(
    "app_pages/what_will_we_do.py",
    "4. Usage: What will we do with it?",
    ui.get_decision("tradeoff_choice") is not None,
    "Record your group's decision above, and a button to the next stage will appear here.",
)
ui.synthetic_notice()
