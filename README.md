# Model sign-off: a readmission-risk exercise

A browser-based group exercise for senior NHS leaders with no ML background. An in-house analytics team has built a model that predicts 30-day readmission, and each group is the panel deciding whether it goes into use. Over about 42 minutes they work through seven stages: a first impression, whether the headline numbers mean what they seem, who the model would have you phone, data leakage, what the list would be used for, explaining a prediction, and a final sign-off with conditions.

**All data is synthetic.** There are no real patients, and the analytics team is fictional.

## Running it

From the repository root:

```
pip install -r requirements.txt
streamlit run app/streamlit_app.py
```

The data the app reads (`app/data/`) is already built. To rebuild it, install `requirements-build.txt` and run `build/generate_data.py`, then `build/train_and_explain.py`. If you rebuild, check the numbers in the facilitator notes below, which are written in by hand.

---

# Facilitator notes

**Not for learners: these notes include the answers.** The figures below match the current exports in `app/data/` (held-out test set of 3,000 patients).

## Timings

The route takes about 42 minutes, then there is a debrief. The times are estimates for a small group of novices and **have not been piloted**. Treat them as a plan to adjust after the first run. Group discussion, not clicking, is what takes the time.

| Stage | Minutes | Should be finished by |
|---|---|---|
| 0. Briefing | 3 | 3 min |
| 1. Performance | 4 | 7 min |
| 2. Tradeoffs | 5 | 12 min |
| 3. Issues | 8 | 20 min |
| 4. Usage | 10 | 30 min |
| 5. Communication | 7 | 37 min |
| 6. Sign-off | 5 | 42 min |
| Debrief (facilitator-led) | 10 to 15 | after the exercise |

The extension discussion prompts at the end of the sign-off page are not timed. Each page shows its own "About N minutes" badge, taken from `STAGE_MINUTES` in `app/ui.py`. If you change the times there, update this table.

### If a group is behind

Cut in this order, so the main lessons survive:

1. **Skip the optional text boxes** (reason for the first impression, owner, pause criteria). Nothing else needs typing.
2. **Stage 4:** do the phone call and Friday discharges, and take delay discharge as a whole-room discussion.
3. **Stage 5:** skip the global tab; stay with the one patient and the four statements.
4. **Stage 6:** pick the conditions and the verdict, and read the memo rather than discussing the journey.

**Don't cut** the Stage 3 reveal (v1 to v2), or the Friday data in Stage 4. They carry the two main lessons: *leakage*, and *a prediction is not the effect of an action*.

## Before you run it

- **Check the wording against current guidance.** The device and governance readings in Stage 4 apply the slides' framework to a readmission use, as a working reading. Have them reviewed (ideally by a Clinical Safety Officer) and recheck the regulatory wording against current MHRA guidance. Record the source and date.
- **Confirm what the support call is.** The exercise assumes a nurse or care coordinator makes the call within two working days. It is a wellbeing check only, limited to signposting and recording, with no clinical assessment. If your real service differs, the device reading changes.
- **Groups of three to five** around one screen each. One person drives; the rest argue.
- **Prior teaching assumed:**
  - accuracy, precision and recall;
  - what a prediction model is;
  - the SHAP demo (percentage points, red and blue);
  - prediction versus causation;
  - the medical-device boundary and DCB0129/DCB0160.

  The app introduces confusion matrices, thresholds, AUC and calibration gently. AUC is taught from scratch in Stage 1, so it doesn't depend on the slide.
- **No code and no install for learners.** It runs in the browser. Have a fallback ready (screenshots and the printed prompts) in case of network trouble.
- **Remind them it is synthetic.** There are no real patients, and the analytics team is fictional.
- **Progress is saved in each browser.** A refresh or dropped connection returns a group to where they were, with their answers. Nothing is sent to or stored on the server. It doesn't follow them to another device or browser.
- **Press "Start over" (top right) between groups** on a shared laptop, or the next group will see the previous group's answers. It asks for confirmation, then clears everything and returns to the Briefing.
- **One tab per group.** Two tabs on the same device share one saved copy, and whichever changes last wins.
- **Open the app a few minutes before the session.** Hosted apps go to sleep when nobody has used them for a while, and take a minute to wake.
- **Tell them up front** that most of the exercise is judgement and will not be marked. Stage 3's "could the model use this?" questions and Stage 5's statements do have clearer answers, and the app says so.

## Stage by stage

### 0. Briefing: Model sign-off for ReadmitRisk v1 (about 3 minutes)

**Aim:** record a first impression *before* any evidence, so the change in view is visible later.

**What groups do:** read the team's summary (AUC 0.99, 97.6% accurate). The AUC line carries only its anchors (0.5 = coin toss, 1.0 = perfect); what it measures is left to Stage 1. Then record approve, approve with conditions, or reject.

**Listen for:** most groups approve, or approve with conditions, on the headline alone. That is the point. There is no right answer.

### 1. Performance: Is it any good? (about 4 minutes)

**Aim:**
- Accuracy mostly tells you how rare the outcome is.
- AUC is how often the model ranks a readmitted patient above one who wasn't readmitted. It is about ordering, not a percentage of patients got right.

**Numbers:**
- **Baseline:** about 12% of patients are readmitted, so predicting nobody is readmitted scores **88%**. The rest of the page stays hidden until the group has guessed.
- **v1 at the 50% cut-off:** 97.6% accurate, flagging 344 of 3,000.
- **AUC pairs:** 361 readmitted × 2,639 not = 952,679 pairs. v1 gets about 99% the right way round (about 1 in 100 wrong). Groups press "Pick a random pair" (then "Pick another pair") a few times; the dot chart only appears after the first pick, and "Show me one it gets wrong" picks a misordered pair, which is kept out of their tally. The next-stage button appears once they have picked at least one pair.

**Draw out:**
- The 88% belongs to this data, not to do-nothing models in general: it is the share of patients not readmitted.
- The AUC quick check: an AUC of 0.5 means ranking no better than a coin toss, not "right about half the patients". If groups picked a wrong answer, this is the misreading to correct.
- AUC says nothing about where to draw the line. That is Stage 2.

### 2. Tradeoffs: Who would we phone? (about 5 minutes)

**Aim:**
- The cut-off follows from capacity.
- Precision and recall trade off against each other.

**Numbers:**
- **v1 at 100 calls per 1,000 discharges:**
  - the cut-off is about 72%;
  - it reaches 97 of 120 readmissions (81%);
  - 97% of calls reach someone who was readmitted, against about 12% for random calling.

**Draw out:**
- Moving the slider moves the *cut-off*. The learner doesn't set the cut-off directly.
- The grid describes who was readmitted anyway, not readmissions a call prevented.
- The third trade-off option ("we can't settle this until we know whether the calls actually help") is a legitimate stance, and sets up Stage 6.

**Common misreading:** "called" patients are not calls that happened. The grid is a thought experiment on past data.

### 3. Issues: Too good to be true? (about 8 minutes)

**Aim:** data leakage is information the model would not have at the moment you need the prediction, and the moment of prediction decides what counts.

**Answers:**

- **GP contacts** (the 30 days beginning on the day of discharge): **No.** This counts GP contacts in the 30 days after the patient left hospital, so it doesn't exist at discharge. Patients who go on to be readmitted tend to have more of them.
- **Age** (the patient's age at admission): **Yes.** This is recorded during the admission, so we have it at the moment of discharge.
- **Length of stay (days)** (this admission): **Yes.** A stay isn't over until the patient leaves, so you couldn't know this at admission. But the model is run as the patient leaves, and by then we do have it. The moment the model is run decides what counts.

**The reveal:** the extract was pulled 30 days after discharge. So v1 leans on GP contacts, follow-up attendance and nursing visits, which are partly *consequences* of readmission. Without them, in v2:
- AUC falls from 0.99 to **0.70**. The page shows v1 and v2 side by side on the same dot chart as Stage 1: v1's two rows barely overlap, and v2's overlap a lot. It then gives a benchmark: published readmission models usually score around 0.6 to 0.75 (Kansagara et al., JAMA 2011). The benchmark is held back until here so the Briefing and Stage 1 don't give away that 0.99 is suspicious;
- at the 50% cut-off, v2 flags only 16 patients;
- at 100 calls per 1,000, v2 reaches 33 of 120 readmissions (28%), with 33% precision, against about 12% for random calling.

**Draw out:**
- The length-of-stay answer: it isn't known at admission, but it is at discharge, so *when the model is run* matters.
- v2 is modest, and that is the honest picture. Ranking by risk still beats random calling, but that needs testing.
- 0.99 was itself a warning sign. A headline AUC far above what similar published models achieve is a reason to ask how it was tested.

### 4. Usage: What will we do with it? (about 10 minutes)

| Compulsory use | Reading of the device question | Main point |
|---|---|---|
| A support phone call | Probably not a medical device, as described | Whether the calls *help* is a separate question from whether the model can rank patients. Ranking by risk can still beat calling at random, but you would want to test that, ideally against usual care or random allocation of limited calls. |
| Ban Friday discharges | Probably not on its own | A prediction or an association is not the effect of an action. Look at where Friday discharges come from before deciding. |
| Delay discharge for high-risk patients | Likely a medical device | A use like this would need strong evidence that it prevents harm before it could be justified. |

**Aim:** the same list can be used in very different ways, with very different governance. Support, harms and device assessment are three separate questions.

**Nothing is marked.** Groups will disagree, and that is fine. These are working readings, not a ruling.

**Friday data:**

| | Friday discharges | Other days |
|---|---|---|
| Readmission rate | 15.8% | 11.0% |
| Share that are elderly care | 60% | 9% |
| Readmission rate within elderly care | 19.9% | 19.9% |

The difference comes from who is discharged on a Friday, not from the day itself. A ban would not change the patients.

**Draw out:**
- What is the *intended purpose* of the call, and what would make it drift? Function creep is the hazard.
- Because this model was built in-house, the organisation is the manufacturer.

**If asked about "clinician":** it means any registered health professional, including nurses.

### 5. Communication: Bringing people with you (about 7 minutes)

**Aim:** an explanation says what the model relied on. It doesn't say what would happen if we changed something, and it isn't evidence of fairness or readiness.

**The patient:** predicted risk **46%**, against an average of 13%.
- **Biggest contributions:**
  - Long-term conditions = 3 (+11.0);
  - Discharge destination = Care home (+8.5);
  - Emergency admissions in previous 12 months = 2 (+6.5).
- **Pushes the risk down:** Age = 53 (−6.3).
- **Outcome:** the patient was **not** readmitted. A risk is not a forecast.

**Statement answers:**

- Describes the prediction and the biggest contributions: **supported**.
- Only moderately accurate (AUC 0.70), so an estimate, not a forecast: **supported**.
- Reducing medications will prevent a readmission: **goes further than the evidence** (a prediction is not the effect of an action).
- Deprivation moves it by only a few points, so it is fair: **goes further than the evidence** (small contributions don't show fairness).

**Draw out:**
- A patient could be at 46% and not be readmitted.
- Ask whether this patient would be on the call list:
  - at 100 calls per 1,000 (cut-off about 23%): yes;
  - under the usual 50% cut-off: no.

### 6. Sign-off: Do we put it into use? (about 5 minutes)

**Aim:** a verdict with concrete conditions, and an honest comparison with the first impression.

**There is no right verdict.** Look for conditions that follow from what the group found:
- local validation;
- calibration;
- an equity check;
- **evaluating whether the calls help** (against usual care, or random allocation of limited calls);
- a named owner;
- monitoring;
- criteria for pausing.

**Gentle prompts built into the page:**
- approving with no conditions;
- choosing "with conditions" but listing none;
- rejecting with conditions.

**Use the memo in the debrief:** groups can read their own verdict journey back.

## Debrief

Pick three or four. The first five are also in the "Extension" expander at the end of the sign-off page (`DISCUSSION` in `app/ui.py`).

- **1. Is it any good?** The numbers look very strong. What would you want to ask the analytics team before signing this off?
- **2. Too good to be true?** v2 can still find some readmissions. Is that enough to justify a service, and what else would you need to know?
- **3. What will we do with it?** Which use would you be most comfortable going ahead with first, and what would you need to see before you allowed a use that guides individual clinical care?
- **4. Bringing people with you:** What is the most useful question a sceptical consultant could ask about this model, and what evidence would you want before answering it?
- **5. Sign-off:** What changed your group's mind between your first impression and your final verdict, and which one condition would you most want to see in place?

Further prompts:

- Who changed their view, and what did it? Who didn't, and why?
- The model that looked best was the one that would have failed in practice. How would we have caught that if nobody had asked?
- A prediction can be good and the service still not help. What would we need to show that it does?
- Who in our organisation is accountable for this model if it goes into use?

### What groups tend to say to the sceptical-consultant question

| Likely question | What it is really asking | Evidence they might name |
|---|---|---|
| "Is it accurate?" or "How often is it wrong?" | Performance and uncertainty | Held-out results; how many calls would be wasted or missed |
| "Does it work for our patients?" | Local validation and calibration | Testing on our own recent discharges; whether predicted risks match what happens here |
| "Do the calls actually reduce readmissions?" | Effect of the action | A trial against usual care, or random allocation of limited calls |
| "Is it fair? Who does it miss?" | Fairness across groups | Performance by age, deprivation and ethnicity; who is on and off the list |
| "Why is this patient flagged, and can I overrule it?" | Explanation and judgement | The waterfall; a route for staff to disagree |
| "What happens when it is wrong, and who is accountable?" | Safety and governance | A named owner, a hazard log, monitoring, criteria for pausing |
| "Has anything leaked, and when does it run?" | Data and timing | A check of every input against the moment of prediction |

The most common first answer is "Is it accurate?". Push with: accurate for whom, measured how, and compared with what? The most valuable answer ("do the calls help?") is the least likely to come up unprompted. See [ONGOING-QUESTIONS.md](ONGOING-QUESTIONS.md) for whether this prompt works as written.

## Reserve material

Some content was taken off the main route to fit 40 minutes. It is still in the code, and [ADDITIONAL-NOTES.md](ADDITIONAL-NOTES.md) describes it.

| Where | What is held in reserve | How to bring it back |
|---|---|---|
| Stage 3 | Outpatient follow-up and emergency admissions questions | Uncomment them in `explain.LEAKAGE_QUESTIONS` |
| Stage 4 | Optional uses: follow-up or medication review, transport, pharmacist review, deprioritising | Already in the page's optional section; set `compulsory` in `interventions.py` to promote one |
| Stage 5 | Two extra statements ("explainable means safe", "what the model relied on") | Uncomment them in `bringing_people.py` and `explain.STATEMENT_SUPPORTED` |
| Stage 5 | The typical and lowest-risk patients, and the picker | Set `SHOW_OTHER_PATIENTS = True` in `bringing_people.py` |
| Sign-off | Extension discussion prompts | Already in the expander at the end of the sign-off page |

### Things to be open about with learners

- The data is synthetic and the team is fictional, but the mistakes are real and common: leakage, over-claiming from explanations, and stretching a use beyond its purpose.
- v2 is modest on purpose. Real models for this problem are rarely much better.
- The device readings apply the framework as a working reading. They are not legal advice. Governance questions go to the Clinical Safety Officer.
