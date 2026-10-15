import pandas as pd
import streamlit as st

import explain
import interventions as iv
import metrics
import ui

meta = ui.load_meta()
features = ui.load_features()
preds = ui.load_predictions()
friday = ui.load_friday()
v1m, v2m = meta["models"]["v1"], meta["models"]["v2"]
o1 = metrics.call_outcomes(preds["p_v1"], preds["readmitted_30d"], 100)
o2 = metrics.call_outcomes(preds["p_v2"], preds["readmitted_30d"], 100)
base = metrics.baseline_accuracy(preds["readmitted_30d"])

shap = ui.load_shap("v2")
values = ui.load_patient_values()
base_pp = ui.load_shap_summary()["base_value_pp"]["v2"]
picks = explain.pick_patients(preds, shap)
patient = explain.patient_explanation(picks["elevated"], preds, shap, values, features, base_pp)

st.title("Facilitator notes")
st.warning(
    "**Not part of the learner route.** These notes include the answers. All data in the exercise is "
    "synthetic, and every number below comes from the same exports the learner pages use."
)

timings_tab, before_tab, stages_tab, debrief_tab, reserve_tab = st.tabs(
    ["Timings", "Before you run it", "Stage by stage", "Debrief", "Reserve material"]
)

# ---------------------------------------------------------------- timings
with timings_tab:
    st.subheader("A 40-minute route, then debrief")
    st.markdown(
        "The times below are estimates for a small group of novices and **have not been piloted**. "
        "Treat them as a plan to adjust after the first run. Group discussion, not clicking, is what takes the time."
    )
    names = [
        ("briefing", "0. Briefing"),
        ("stage1", "1. Is it any good?"),
        ("stage2", "2. Too good to be true?"),
        ("stage3", "3. What will we do with it?"),
        ("stage4", "4. Bringing people with you"),
        ("stage5", "5. Sign-off"),
    ]
    rows, elapsed = [], 0
    for key, label in names:
        m = ui.STAGE_MINUTES[key]
        elapsed += m
        rows.append({"Stage": label, "Minutes": str(m), "Should be finished by": f"{elapsed} min"})
    rows.append({"Stage": "Debrief (facilitator-led)", "Minutes": "10 to 15", "Should be finished by": "after the exercise"})
    st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
    st.caption(
        f"The route adds up to {sum(ui.STAGE_MINUTES.values())} minutes. The extension discussion prompts at the end "
        "of the sign-off page are not timed."
    )

    st.subheader("If a group is behind")
    st.markdown(
        """
Cut in this order, so the main lessons survive:

1. **Skip the optional text boxes** (reason for the first impression, owner, pause criteria). Nothing else needs typing.
2. **Stage 3:** do the phone call and Friday discharges, and take delay discharge as a whole-room discussion.
3. **Stage 4:** skip the global tab; stay with the one patient and the four statements.
4. **Stage 5:** pick the conditions and the verdict, and read the memo rather than discussing the journey.

**Don't cut** the Stage 2 v1 to v2 reveal, or the Friday data in Stage 3. They carry the two main lessons: *leakage*, and *a prediction is not the effect of an action*.
"""
    )

# ---------------------------------------------------------------- before
with before_tab:
    st.subheader("Before you run it")
    st.markdown(
        """
- **Check the wording against current guidance.** The device and governance readings in Stage 3 are a working
  application of the slides' framework to a readmission use. Have them reviewed (ideally by a Clinical Safety
  Officer) and recheck the regulatory wording against current MHRA guidance. Record the source and date.
- **Confirm what the support call is.** The exercise assumes a wellbeing check only, limited to signposting and
  recording, with no clinical assessment, made by a nurse or care coordinator within two working days. If your
  real service differs, the device reading changes.
- **Groups of three to five** around one screen each. One person drives; the rest argue.
- **Prior teaching assumed:** accuracy, precision and recall; what a prediction model is; the SHAP demo
  (percentage points, red and blue); prediction versus causation; the medical-device boundary and DCB0129/DCB0160.
  Confusion matrices, thresholds, AUC and calibration are introduced gently in the app.
- **No code and no install.** It runs in the browser. Give groups a fallback (screenshots and the printed prompts)
  in case of network trouble.
- **Remind them it is synthetic.** No real patients; the 'analytics team' is fictional.
- **Tell them up front** that most of the exercise is judgement and will not be marked. Stage 2's
  'could the model use this?' questions and Stage 4's statements do have clearer answers and say so.
"""
    )

# ---------------------------------------------------------------- stages
with stages_tab:
    st.subheader("0. Briefing (about 3 minutes)")
    st.markdown(
        f"""
**Aim:** record a first impression *before* any evidence, so the change in view is visible later.

**What groups do:** read the team's summary (AUC {v1m['auc_test']:.2f}, {v1m['accuracy_at_50pct']:.1%} accurate),
record approve / approve with conditions / reject.

**Listen for:** most groups approve or approve with conditions on the headline alone. That is the point.
There is no right answer.
"""
    )

    st.subheader("1. Is it any good? (about 7 minutes)")
    st.markdown(
        f"""
**Aim:** accuracy mostly tells you how rare the outcome is; the cut-off follows from capacity; precision and
recall trade off.

**Numbers:** about {meta['base_rate_test']:.0%} of patients are readmitted, so predicting nobody scores
**{base:.0%}**. v1 scores {v1m['accuracy_at_50pct']:.1%} at the 50% cut-off, flagging {v1m['n_flagged_at_50pct']} of
{meta['n_test']:,}. At **100 calls per 1,000 discharges** the cut-off is about {o1['cutoff']:.0%}; v1 reaches
{o1['called_readmitted']} of {o1['readmitted_total']} readmissions ({o1['recall']:.0%}) with
{o1['precision']:.0%} of calls reaching someone who was readmitted (random calling: about
{o1['random_precision']:.0%}).

**Draw out:** moving the slider moves the *cut-off*, and the learner doesn't set it directly. The grid describes
who was readmitted anyway, not readmissions a call prevented. The third trade-off option ("we can't settle this
until we know whether the calls help") is a legitimate stance and sets up Stage 5.

**Common misreading:** "called" patients are not calls that happened. The grid is a thought experiment on past data.
"""
    )

    st.subheader("2. Too good to be true? (about 8 minutes)")
    answers = []
    for key in explain.LEAKAGE_QUESTIONS:
        f = features[key]
        answers.append(
            f"- **{f['display']}** ({f['covers']}): "
            f"**{'Yes' if f['known_at_discharge'] else 'No'}.** {f['why']}"
        )
    st.markdown(
        "**Aim:** data leakage is information the model would not have at the moment you need the prediction, "
        "and the moment of prediction decides what counts.\n\n**Answers:**\n\n"
        + "\n".join(answers)
        + f"""

**The reveal:** the extract was pulled 30 days after discharge, so v1 leans on GP contacts, follow-up attendance
and nursing visits, which are partly *consequences* of readmission. Without them (v2) AUC falls from
{v1m['auc_test']:.2f} to **{v2m['auc_test']:.2f}**, and at the 50% cut-off v2 flags only {v2m['n_flagged_at_50pct']} patients.
At 100 calls per 1,000, v2 reaches {o2['called_readmitted']} of {o2['readmitted_total']} readmissions
({o2['recall']:.0%}) with {o2['precision']:.0%} precision, against about {o2['random_precision']:.0%} for random
calling.

**Draw out:** the length-of-stay answer. It is not known at admission but is at discharge, so *when the model is
run* matters. v2 is modest, and that is the honest picture. Ranking by risk still beats random calling, but test it.
"""
    )

    st.subheader("3. What will we do with it? (about 10 minutes)")
    compulsory = [i for i in iv.INTERVENTIONS if i["compulsory"]]
    rows = [
        {
            "Compulsory use": i["title"],
            "Reading of the device question": i["device_lean"],
            "Main point": i["support"],
        }
        for i in compulsory
    ]
    st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
    st.markdown(
        f"""
**Aim:** the same list can be used in very different ways, with very different governance. Support, harms and
device assessment are three separate questions.

**Nothing is marked.** Groups will disagree, and that is fine. These readings are working readings, not a ruling.

**Friday data:** the raw Friday rate is {friday['friday']['rate']:.1%} against {friday['other_days']['rate']:.1%}.
{friday['share_of_friday_discharges_elderly_care']:.0%} of Friday discharges are elderly care, against
{friday['share_of_other_day_discharges_elderly_care']:.0%} on other days. Within elderly care the rates are
{friday['elderly_care']['friday']['rate']:.1%} (Friday) and {friday['elderly_care']['other_days']['rate']:.1%}
(other days). It is who is discharged, not the day. A ban would not change the patients.

**Draw out:** what is the *intended purpose* of the call, and what would make it drift? Function creep is the hazard.
Because this model was built in-house, the organisation is the manufacturer.

**If asked about 'clinician':** any registered health professional, including nurses.
"""
    )

    st.subheader("4. Bringing people with you (about 7 minutes)")
    top = patient["shown"]
    st.markdown(
        f"""
**Aim:** an explanation says what the model relied on, not what would happen if we changed something, and it is not
evidence of fairness or readiness.

**The patient:** predicted risk **{patient['fx']:.0f}%** against an average of {patient['base']:.0f}%. Biggest
contributions: {top[0]['label']} ({top[0]['value']:+.1f}), {top[1]['label']} ({top[1]['value']:+.1f}) and
{top[2]['label']} ({top[2]['value']:+.1f}). {next(i['label'] for i in patient['shown'] if i['value'] < 0)} pushes
the risk *down* ({next(i['value'] for i in patient['shown'] if i['value'] < 0):+.1f}). The patient was **not**
readmitted: a risk is not a forecast.

**Statement answers:**

- Describes the prediction and the biggest contributions: **supported**.
- Only moderately accurate (AUC {v2m['auc_test']:.2f}), so an estimate, not a forecast: **supported**.
- Reducing medications will prevent a readmission: **goes further than the evidence** (a prediction is not the
  effect of an action).
- Deprivation moves it by only a few points, so it is fair: **goes further than the evidence** (small
  contributions don't show fairness).

**Draw out:** a patient could be at 46% and not be readmitted. Ask whether this patient would be on the call list
at 100 per 1,000 (cut-off about {o2['cutoff']:.0%}, so yes) and under the usual 50% cut-off (no).
"""
    )

    st.subheader("5. Sign-off (about 5 minutes)")
    st.markdown(
        """
**Aim:** a verdict with concrete conditions, and an honest comparison with the first impression.

**There is no right verdict.** Look for conditions that follow from what the group found: local validation,
calibration, an equity check, **evaluating whether the calls help** (against usual care or random allocation of
limited calls), a named owner, monitoring, and criteria for pausing.

**Gentle prompts built into the page:** approving with no conditions; "with conditions" but none listed;
rejecting with conditions.

**Use the memo in the debrief:** groups can read their own verdict journey back.
"""
    )

# ---------------------------------------------------------------- debrief
with debrief_tab:
    st.subheader("Debrief questions")
    st.markdown("Pick three or four. These are the discussion prompts moved off the stage pages.")
    for stage, prompt in ui.DISCUSSION:
        st.markdown(f"- **{stage}:** {prompt}")
    st.markdown(
        """
Further prompts:

- Who changed their view, and what did it? Who didn't, and why?
- The model that looked best was the one that would have failed in practice. How would we have caught that if
  nobody had asked?
- A prediction can be good and the service still not help. What would we need to show that it does?
- Who in our organisation is accountable for this model if it goes into use?
"""
    )

    st.subheader("What groups tend to say to the sceptical-consultant question")
    st.dataframe(
        pd.DataFrame(
            [
                ("'Is it accurate?' / 'How often is it wrong?'", "Performance and uncertainty", "Held-out results; how many wasted or missed calls"),
                ("'Does it work for our patients?'", "Local validation and calibration", "Testing on our own recent discharges; do predicted risks match what happens here?"),
                ("'Do the calls actually reduce readmissions?'", "Effect of the action", "A trial against usual care, or random allocation of limited calls"),
                ("'Is it fair? Who does it miss?'", "Fairness across groups", "Performance by age, deprivation and ethnicity; who is on and off the list"),
                ("'Why is this patient flagged, and can I overrule it?'", "Explanation and judgement", "The waterfall; a route for staff to disagree"),
                ("'What happens when it is wrong, and who is accountable?'", "Safety and governance", "A named owner, a hazard log, monitoring, pause criteria"),
                ("'Has anything leaked, and when does it run?'", "Data and timing", "A check of every input against the moment of prediction"),
            ],
            columns=["Likely question", "What it is really asking", "Evidence they might name"],
        ),
        hide_index=True,
        width="stretch",
    )
    st.caption(
        "The most common first answer is 'Is it accurate?'. Push with: accurate for whom, measured how, compared with "
        "what? The most valuable answer ('do the calls help?') is the least likely to appear unprompted."
    )

# ---------------------------------------------------------------- reserve
with reserve_tab:
    st.subheader("Reserve material")
    st.markdown(
        """
Some content was taken off the main route to fit 40 minutes. It is still in the code and described in
`ADDITIONAL-NOTES.md`.

| Where | What is held in reserve | How to bring it back |
|---|---|---|
| Stage 2 | Outpatient follow-up and emergency admissions questions | Uncomment in `explain.LEAKAGE_QUESTIONS` |
| Stage 3 | Optional uses: follow-up / medication review, transport, pharmacist review, deprioritising | Already in the page's optional section; set `compulsory` in `interventions.py` to promote one |
| Stage 4 | Two extra statements ("explainable means safe", "what the model relied on") | Uncomment in `bringing_people.py` and `explain.STATEMENT_SUPPORTED` |
| Stage 4 | The typical and lowest-risk patients, and the picker | Set `SHOW_OTHER_PATIENTS = True` in `bringing_people.py` |
| Sign-off | Extension discussion prompts | Already in the expander at the end of the sign-off page |
"""
    )
    st.subheader("Things to be open about with learners")
    st.markdown(
        """
- The data is synthetic and the 'team' is fictional, but the mistakes (leakage, over-claiming from explanations,
  stretching a use) are real and common.
- v2 is modest on purpose. Real models for this problem are rarely much better.
- The device readings are a working application of the framework, not legal advice. Governance questions go
  to the Clinical Safety Officer.
"""
    )
