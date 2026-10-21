import pandas as pd
import streamlit as st

import charts
import explain
import metrics
import ui

VERDICTS = ["Approve", "Approve with conditions", "Reject"]
YES = "Yes: the model would have this when it is run on a real patient"
NO = "No: this wouldn't exist yet when the model is run on a real patient"

meta = ui.load_meta()
features = ui.load_features()
shap_summary = ui.load_shap_summary()
preds = ui.load_predictions()
imp_v1 = shap_summary["mean_abs_shap_pp"]["v1"]
imp_v2 = shap_summary["mean_abs_shap_pp"]["v2"]

ui.stage_header("3. Issues: Too good to be true?", "What is the model actually relying on?", minutes="stage3")
ui.task_box(
    "Look at what ReadmitRisk v1 leans on most, and decide for each factor whether we would "
    "really know it at the moment a patient leaves hospital."
)

st.subheader("What the model relies on")
st.plotly_chart(charts.importance_bar(imp_v1, features, top=8), width="stretch")
st.caption(
    "Each bar is the average amount that factor moves a patient's predicted risk up or down, "
    "in percentage points. It shows what the model *relied on*, not what would happen if we changed something."
)

st.subheader("When do we need the prediction?")
t1, t2, t3 = st.columns(3)
with t1.container(border=True):
    st.markdown("**Admission**\n\nThe patient comes in.")
with t2.container(border=True):
    st.markdown("**Discharge**\n\n**This is the moment we need the prediction**, to decide who to phone.")
with t3.container(border=True):
    st.markdown("**30 days later**\n\nWe find out who was readmitted.")

st.subheader("Could the model use this on a real patient?")
st.markdown(
    "This is the model's training data: **an extract produced 30 days after each patient left hospital**. "
    "In real use, the model would be run on a patient as they leave hospital, to decide who to phone. "
    "For each of these factors from the chart, could the model actually be given that "
    "information at that point?"
)
with st.expander("Need a hint?"):
    st.markdown(
        "Ask: *if I were looking at this patient's record on the day they went home, could I fill this in?* "
        "Each factor says what period it **covers**. Compare that with the moment we need the prediction. "
        "The extract was produced a month later, so a column being in the data doesn't mean it was "
        "available when the patient left."
    )
# The questions asked are listed in explain.LEAKAGE_QUESTIONS (one of each kind; the reserve
# questions are kept there as comments).
top6 = explain.LEAKAGE_QUESTIONS
# Widget keys are dropped when the page isn't rendered, so keep answers under a plain key.
stored = st.session_state.setdefault("known_answers", {})
answers = {}
for key in top6:
    f = features[key]
    options = [YES, NO]
    ans = st.radio(
        f"**{f['display']}**: {f['description']} *(Covers: {f['covers']}.)*",
        options,
        index=options.index(stored[key]) if key in stored else None,
        horizontal=True,
        key=f"known_{key}",
    )
    if ans is not None:
        stored[key] = ans
    answers[key] = ans
    ui.factual_check(ans, YES if f["known_at_discharge"] else NO, f["why"])

# Kept as nested blocks rather than st.stop(), so the progress save at the end of the entry
# script still runs while this stage is unfinished.
all_answered = all(a is not None for a in answers.values())
if all_answered:
    st.divider()
    st.subheader("What this is called: data leakage")
    st.markdown(
        "The model is using **information it wouldn't have at the moment you actually need the prediction**. "
        "Here, the extract was pulled 30 days *after* discharge, so it includes what happened next: GP contacts, "
        "whether a follow-up was attended and nursing visits. Those are partly a *consequence* of being readmitted, "
        "so they give the answer away. That is why v1 looked so good. It is an easy mistake for a careful team to make, "
        "and catching it is exactly what a sign-off review is for."
    )

    st.subheader("Take away the leaked information")
    if not st.session_state.get("v2_shown"):
        if st.button("Rebuild the model without those factors (v2)", type="primary"):
            st.session_state["v2_shown"] = True
            st.rerun()
    else:
        v1, v2 = meta["models"]["v1"], meta["models"]["v2"]
        st.markdown("**v2** uses only what we know at discharge. Same test patients, same method.")
        m1, m2, m3 = st.columns(3)
        m1.metric("AUC (1.0 perfect, 0.5 coin toss)", f"{v2['auc_test']:.2f}", f"{v2['auc_test'] - v1['auc_test']:+.2f} vs v1", delta_color="off")
        m2.metric(
            "Accuracy at 50% cut-off",
            f"{v2['accuracy_at_50pct']:.1%}",
            f"{v2['accuracy_at_50pct'] - v1['accuracy_at_50pct']:+.1%} vs v1",
            delta_color="off",
        )
        m3.metric(
            "Patients flagged at 50%",
            f"{v2['n_flagged_at_50pct']}",
            f"{v2['n_flagged_at_50pct'] - v1['n_flagged_at_50pct']:+d} vs v1",
            delta_color="off",
        )

        # The same picture as the AUC pairs in Stage 1, now for both models.
        y = preds["readmitted_30d"].to_numpy()
        s1, s2 = st.columns(2, gap="large")
        s1.plotly_chart(charts.risk_strip(preds["p_v1"], y, title="v1 (with leaked information)"), width="stretch")
        s2.plotly_chart(charts.risk_strip(preds["p_v2"], y, title="v2 (discharge-time information only)"), width="stretch")
        st.markdown(
            f"Pick a pair of patients, one readmitted and one not, as you did in Stage 1: v2 puts them the right way round "
            f"**{v2['auc_test']:.0%}** of the time, against **{v1['auc_test']:.0%}** for v1. The two rows now overlap a lot."
        )
        st.caption(
            "For comparison, published models that predict readmission usually score somewhere around 0.6 to 0.75, "
            "and a widely cited review (Kansagara and colleagues, JAMA, 2011) found most of them performed poorly. "
            "v2 is in that range. An AUC of 0.99 for something as uncertain as readmission should have been a warning sign on its own."
        )

        cap = ui.capacity()
        o1 = metrics.call_outcomes(preds["p_v1"], preds["readmitted_30d"], cap)
        o2 = metrics.call_outcomes(preds["p_v2"], preds["readmitted_30d"], cap)
        st.markdown(f"**At your chosen capacity of {cap} calls per 1,000 discharges:**")
        a, b = st.columns(2)
        with a:
            st.plotly_chart(charts.icon_array(o1, title="v1 (with leaked information)"), width="stretch")
        with b:
            st.plotly_chart(charts.icon_array(o2, title="v2 (discharge-time information only)"), width="stretch")
        st.markdown(
            f"- Following v1's recommendations would have reached **{o1['called_readmitted']}** of the "
            f"{o1['readmitted_total']} patients who were readmitted; following v2's would reach **{o2['called_readmitted']}** ({o2['recall']:.0%}).\n"
            f"- **{o2['precision']:.0%}** of v2's calls would reach someone who was readmitted, against about "
            f"**{o2['random_precision']:.0%}** for calling at random."
        )
        st.info(
            "v2 is much more modest, and it is the honest picture. It would still beat random calling, but you would need to "
            "test it against random calling in your own hospital, because ranking by risk is not the same as knowing a "
            "call will help."
        )
        with st.expander("What v2 relies on"):
            st.plotly_chart(charts.importance_bar(imp_v2, features, top=8), width="stretch")
        with st.expander("Show the v1 and v2 counts as a table"):
            st.dataframe(
                pd.DataFrame(
                    {
                        "Group": [label for _, label in metrics.GROUPS],
                        "v1 per 1,000": [o1[k] for k, _ in metrics.GROUPS],
                        "v2 per 1,000": [o2[k] for k, _ in metrics.GROUPS],
                    }
                ),
                hide_index=True,
                width="stretch",
            )

        st.divider()
        st.subheader("Has this changed your view?")
        locked = ui.get_decision("stage2_verdict")
        if locked:
            initial = ui.get_decision("initial_verdict")
            st.success(f"Recorded: **{locked}**" + (f" (your first impression was: {initial})" if initial else ""))
        else:
            verdict = st.radio("Having seen v2, what would your group do?", VERDICTS, index=None, key="stage2_widget")
            if st.button("Record our view", disabled=verdict is None, type="primary"):
                ui.record_decision("stage2_verdict", verdict)
                st.rerun()

ui.next_stage(
    "app_pages/what_will_we_do.py",
    "4. Usage: What will we do with it?",
    ui.get_decision("stage2_verdict") is not None,
    "Record your group's view above, and a button to the next stage will appear here.",
)
ui.synthetic_notice()
