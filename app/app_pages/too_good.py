import streamlit as st

import charts
import explain
import ui

VERDICTS = ["Approve", "Approve with conditions", "Reject"]
# Both must keep starting "Yes" / "No": the memo scores answers on that.
YES = "Yes: at discharge we'd have the same information the model learnt from"
NO = "No: at discharge this would be missing, or would mean something different"

# Option -> how the (unmarked) response opens. Community nursing isn't listed first, so the
# question doesn't point at it. Every response then leads to the top of the chart.
CHART_QUESTIONS = {
    "Why does deprivation matter so little?": (
        "A fair question, and fairness comes back later in the exercise. For now, it's also worth looking at "
        "the top of the chart. "
    ),
    "Why is community nursing the biggest factor, far ahead of age or long-term conditions?": "A good question to ask. ",
    "Nothing stands out: these all sound like sensible things to predict readmission": (
        "Worth a second look at the top of the chart. "
    ),
}

meta = ui.load_meta()
features = ui.load_features()
shap_summary = ui.load_shap_summary()
preds = ui.load_predictions()
imp_v1 = shap_summary["mean_abs_shap_pp"]["v1"]
imp_v2 = shap_summary["mean_abs_shap_pp"]["v2"]

ui.stage_header("2. Issues: Too good to be true?", "What is the model actually relying on?", minutes="stage2")
ui.task_box(
    "Look at what ReadmitRisk v1 leans on most, and decide for each factor whether we would "
    "really have the same information at the moment a patient leaves hospital."
)

st.subheader("What the model relies on")
st.plotly_chart(charts.importance_bar(imp_v1, features, top=10), width="stretch")
st.caption(
    "Each bar is the average amount that factor moves a patient's predicted risk up or down, "
    "in percentage points. It shows what the model *relied on*, not what would happen if we changed something."
)

# Not marked: the point is to notice the imbalance before being asked about timing.
if st.session_state.get("chart_question"):
    st.session_state.setdefault("chart_question_widget", st.session_state["chart_question"])
chart_q = st.radio(
    "Is there anything about this chart you'd want to ask the analytics team about?",
    list(CHART_QUESTIONS),
    index=None,
    key="chart_question_widget",
)
if chart_q:
    st.session_state["chart_question"] = chart_q
    top_key, top_pp = next(iter(imp_v1.items()))
    ratio = top_pp / imp_v1["age"]
    st.info(
        CHART_QUESTIONS[chart_q]
        + f"{features[top_key]['display']} moves predicted risk about {ratio:.0f} times as much as age. When one factor "
        "dominates far beyond what clinical experience would suggest, ask where its data comes from and when it is "
        "recorded. That is what the next questions do."
    )

# Kept as nested blocks rather than st.stop(), so the progress save at the end of the entry
# script still runs while this stage is unfinished.
answers = {key: None for key in explain.LEAKAGE_QUESTIONS}
if chart_q:
    st.subheader("When do we need the prediction?")
    st.markdown(
        "Before judging each factor, pin down **when the model would actually be used**. A factor is only "
        "any use if, at that moment, we'd have the same information the model learnt from."
    )
    # A timeline, not buttons: arrows between the steps, and the moment of prediction highlighted
    # (styles.css shades the .st-key-timeline_discharge box).
    t1, a1, t2, a2, t3 = st.columns([1, 0.12, 1, 0.12, 1], vertical_alignment="center")
    with t1.container(border=True):
        st.markdown("**:material/local_hospital: Admission**\n\nThe patient comes in.")
    a1.markdown(":material/arrow_forward:")
    with t2.container(border=True, key="timeline_discharge"):
        st.markdown(
            "**:material/home: Discharge**\n\n**The model is run here**, as the patient leaves, to decide who to phone."
        )
    a2.markdown(":material/arrow_forward:")
    with t3.container(border=True):
        st.markdown("**:material/event: 30 days later**\n\nWe find out who was readmitted.")

    st.subheader("Would the model get the same information in real use?")
    st.markdown(
        "In real use, the model would be run on a patient as they leave hospital, to decide who to phone. "
        "For each factor below, could we give it the same information at that point as it had in its training data? "
        "The analytics team's data dictionary says where each one comes from."
    )
    with st.expander("The analytics team's data dictionary", icon=":material/menu_book:"):
        st.markdown(
            "**ReadmitRisk training extract.** One row per discharge. Each patient's row was extracted "
            "**30 days after their discharge date**, once it was known whether they had been readmitted."
        )
        st.table(
            {
                "Factor": [f["display"] for f in features.values()],
                "Description": [f["description"] for f in features.values()],
                "Source": [f["source"] for f in features.values()],
            }
        )
    with st.expander("Need a hint?"):
        st.markdown(
            "Ask: *if I were looking at this patient's record on the day they went home, could I fill this in "
            "the same way the training data did?* Check each factor's **source** in the data dictionary, then "
            "compare it with when the extract was run. A field can have the same name at discharge and still "
            "hold different information."
        )
    # The questions asked are listed in explain.LEAKAGE_QUESTIONS (the reserve questions are
    # kept there as comments).
    # Widget keys are dropped when the page isn't rendered, so keep answers under a plain key.
    stored = st.session_state.setdefault("known_answers", {})
    for key in explain.LEAKAGE_QUESTIONS:
        f = features[key]
        options = [YES, NO]
        ans = st.radio(
            f"**{f['display']}**: {f['description']}",
            options,
            # Answers saved under older wording of the options are ignored.
            index=options.index(stored[key]) if stored.get(key) in options else None,
            horizontal=True,
            key=f"known_{key}",
        )
        if ans is not None:
            stored[key] = ans
        answers[key] = ans
        ui.factual_check(ans, YES if f["known_at_discharge"] else NO, f["why"])

all_answered = all(a is not None for a in answers.values())
if all_answered:
    st.divider()
    st.subheader("What this is called: data leakage")
    st.markdown(
        "The model is using **information it wouldn't have at the moment you actually need the prediction**. "
        "Here, each row was extracted 30 days *after* discharge, and columns such as 'GP contacts (last 30 days)' "
        "were counted back from that date. So in the training data they describe what happened *after* the "
        "patient went home: GP contacts, nursing visits and whether a follow-up was attended. Those are partly a "
        "*consequence* of becoming unwell again, so they give the answer away. At discharge the same fields would "
        "hold different information. That is why v1 looked so good. It is an easy mistake for a careful team to make, "
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

        st.info(
            "v2 is much more modest, and it is the honest picture. From here on the exercise uses v2. "
            "Next, you will decide how many patients it should put on the call list."
        )
        with st.expander("What v2 relies on"):
            st.plotly_chart(charts.importance_bar(imp_v2, features, top=8), width="stretch")

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
    "app_pages/who_would_we_phone.py",
    "3. Tradeoffs: Who would we phone?",
    ui.get_decision("stage2_verdict") is not None,
    "Record your group's view above, and a button to the next stage will appear here.",
)
ui.synthetic_notice()
