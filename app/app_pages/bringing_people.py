import streamlit as st

import charts
import explain
import ui

meta = ui.load_meta()
features = ui.load_features()
preds = ui.load_predictions()
shap = ui.load_shap("v2")
values = ui.load_patient_values()
summary = ui.load_shap_summary()
base = summary["base_value_pp"]["v2"]
auc = meta["models"]["v2"]["auc_test"]

PATIENT_LABELS = {
    "elevated": "Elevated predicted risk",
    "high": "Highest predicted risk",
    "typical": "A typical patient (optional)",
    "low": "Lowest predicted risk (optional)",
}

ui.stage_header(
    "4. Bringing people with you",
    "To use a model, other people have to understand it well enough to trust it where it deserves trust, "
    "and to question it where it doesn't.",
)
ui.task_box(
    "Look at how the model reached its prediction for one patient, then decide which statements your group "
    "would be comfortable saying to a ward manager or a sceptical consultant."
)
st.markdown(
    "From here on we look at **v2**, the version without the leaked information, since that is the one "
    "that could actually be used."
)

picks = explain.pick_patients(preds, shap)
# One patient is enough for the exercise: one with a clearly elevated risk (about 45%) and a
# strong factor pushing it down, so both red and blue bars show. The others (and the picker)
# are kept, switched off: set SHOW_OTHER_PATIENTS = True to bring them back.
SHOW_OTHER_PATIENTS = False
if SHOW_OTHER_PATIENTS:
    choice = st.radio(
        "Which patient would you like to look at?",
        list(PATIENT_LABELS),
        format_func=PATIENT_LABELS.get,
        horizontal=True,
        key="patient_pick",
    )
else:
    choice = "elevated"
expl = explain.patient_explanation(picks[choice], preds, shap, values, features, base)

local_tab, global_tab = st.tabs(["This patient (local)", "All patients (global)"])

with local_tab:
    st.markdown(
        f"**The model predicts a {expl['fx']:.0f}% risk of readmission for this patient**, "
        f"compared with about **{expl['base']:.0f}%** for the average patient."
    )
    st.plotly_chart(charts.waterfall(expl), width="stretch")
    st.caption(
        "Read from the top. Each bar is how much one factor moves *this* patient's predicted risk from the average, "
        "in percentage points. Red pushes towards readmission, blue pushes away. The bars add up to this "
        "patient's prediction."
    )
    top = expl["shown"][:2]
    st.markdown(
        f"The biggest contributions are **{top[0]['label']}** ({top[0]['value']:+.1f} points) and "
        f"**{top[1]['label']}** ({top[1]['value']:+.1f} points)."
    )
    outcome = "was" if expl["readmitted"] else "was not"
    st.info(
        f"In the data, this patient **{outcome}** readmitted within 30 days. A predicted risk is a probability "
        "based on similar patients in the past. It is not a forecast of what will happen to this one person."
    )

with global_tab:
    st.plotly_chart(
        charts.importance_bar(summary["mean_abs_shap_pp"]["v2"], features, top=8), width="stretch"
    )
    st.markdown(
        "**Local** shows what drove the prediction for *one* patient. **Global** shows, on average across many "
        "patients, how much each factor contributes. A factor can matter a lot for one patient and little on "
        "average, or the other way round."
    )

st.divider()
st.subheader("What would we say?")
st.markdown(
    f"Imagine you are explaining this patient's prediction to a ward manager, or to a consultant who is "
    f"sceptical of the model. **For each statement, would your group be happy to say it?**"
)

a, b = expl["shown"][0], expl["shown"][1]
dep = next(i["value"] for i in expl["all"] if i["feature"] == "deprivation_decile")
STATEMENTS = [
    {
        "id": "causal",
        "text": "The model takes this patient's number of medications into account in their prediction, so "
        "reducing their medications will prevent a readmission.",
        "ok": False,
        "why": "Goes further than the explanation. SHAP shows what the model *relied on*, not what would happen if we "
        "changed something. A patient on more medicines may simply be sicker, and reducing them might help, "
        "do nothing or cause harm.",
    },
    {
        "id": "describe",
        "text": f"The model predicts about a {expl['fx']:.0f}% risk of readmission for this patient, compared with "
        f"about {expl['base']:.0f}% for the average patient. The biggest contributions come from {a['label']} "
        f"({a['value']:+.1f} points) and {b['label']} ({b['value']:+.1f} points).",
        "ok": True,
        "why": "Supported. It says what the model predicts and which factors contributed most, without claiming "
        "that those factors are the whole story or that they cause the outcome.",
    },
    {
        "id": "fair",
        "text": f"Deprivation moves this patient's prediction by only {dep:+.1f} percentage points, so we can be "
        "confident the model is fair to patients from deprived areas.",
        "ok": False,
        "why": "Goes further than the explanation. A small contribution from one factor does not show a model is "
        "fair: other factors can act as stand-ins, and accuracy can differ between groups. Fairness needs its "
        "own checks.",
    },
    {
        "id": "uncertain",
        "text": f"The model is only moderately accurate (AUC {auc:.2f}), so this is an estimate based on similar "
        "patients in past data, not a forecast of what will happen to this patient.",
        "ok": True,
        "why": "Supported, and worth saying. An AUC around 0.7 means the model separates readmitted from "
        "not-readmitted patients only moderately well. Being open about that helps people use it sensibly.",
    },
    {
        "id": "safe",
        "text": "Because we can see why the model predicts what it does, it is safe to put into use.",
        "ok": False,
        "why": "Goes further than the explanation. Being able to explain a model is not evidence that it is "
        "accurate, well calibrated, safe or fair in your setting. That takes local validation and governance.",
    },
    {
        "id": "relied",
        "text": "These bars describe what the model relied on to reach its prediction for this patient. They do not "
        "show what would happen if we changed one of the factors.",
        "ok": True,
        "why": "Supported. This is the careful way to describe an explanation.",
    },
]

st.caption(
    "Unlike the earlier judgement calls, this one has clearer answers: it is about what an explanation can and "
    "cannot support."
)
YES_SAY = "Yes, we'd be happy to say this"
NO_SAY = "No, we wouldn't say this"
# group's answers, kept under a plain key (widget state is dropped when the page isn't rendered)
locked = st.session_state.get("stage4_statements")

if locked is None:
    answers = {}
    for n, s in enumerate(STATEMENTS, start=1):
        with st.container(border=True):
            st.markdown(f"**Statement {n}**\n\n> {s['text']}")
            answers[s["id"]] = st.radio(
                "Would we be happy to say this?",
                [YES_SAY, NO_SAY],
                index=None,
                horizontal=True,
                key=f"say_{s['id']}",
            )
    ready = all(a is not None for a in answers.values())
    if st.button("Check our answers", type="primary", disabled=not ready):
        st.session_state["stage4_statements"] = {k: v == YES_SAY for k, v in answers.items()}
        st.rerun()
    if not ready:
        st.caption("Answer all six to see how they compare with the evidence.")
else:
    n_ok = sum(1 for s in STATEMENTS if locked[s["id"]] == s["ok"])
    st.info(
        f"**Your group got {n_ok} of {len(STATEMENTS)} right.** A statement is right to say only if the "
        "explanation really supports it."
    )
    for n, s in enumerate(STATEMENTS, start=1):
        said_yes = locked[s["id"]]
        correct = said_yes == s["ok"]
        said = "you'd be happy to say this" if said_yes else "you wouldn't say this"
        if s["ok"]:
            badge = ":green-badge[:material/check: Supported by the explanation]"
            detail = "and the explanation does support it" if said_yes else "but the explanation does support it"
        else:
            badge = ":red-badge[:material/close: Goes further than the evidence]"
            detail = "but it goes further than the evidence" if said_yes else "and it goes further than the evidence"
        with st.container(border=True):
            st.markdown(f"**Statement {n}**\n\n> {s['text']}")
            st.markdown(f"**The statement itself:** {badge}")
            if correct:
                st.success(f"**Your answer: correct.** You said {said}, {detail}.")
            else:
                st.error(f"**Your answer: not quite.** You said {said}, {detail}.")
            st.markdown(s["why"])
    if st.button("Change our answers"):
        st.session_state["stage4_statements"] = None
        st.rerun()

st.divider()
st.subheader("What an explanation can't tell you")
st.markdown(
    """
- **It is not a cause.** It shows what the model relied on, not what would happen if we changed something.
- **It is not proof of fairness.** Small contributions for a factor such as deprivation do not show that a
  system is fair.
- **It is not proof of readiness.** A model can be explained and still be inaccurate, badly calibrated or unsafe
  in your hospital.
- **It is a way to ask better questions.** It helps you spot things that look wrong, as the leaked
  information did in Stage 2.
"""
)
st.markdown(
    "**Discuss:** what is the most useful question a sceptical consultant could ask about this model, and "
    "what evidence would you want before answering it?"
)
ui.synthetic_notice()
