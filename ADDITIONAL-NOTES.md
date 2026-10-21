# Additional notes

Material that has been taken out of the learner route (or switched off) but kept, so it can be reinstated for a longer session, a second version of the exercise, or a facilitator who wants more depth.

For open design questions, see [ONGOING-QUESTIONS.md](ONGOING-QUESTIONS.md). For the history of decisions, see [PROGRESS.md](PROGRESS.md).

## Removed to fit the 35-minute route (2026-10-14)

The full build was estimated at roughly 47 to 53 minutes for novices (unpiloted). These items were removed or demoted to get to about 39 to 43 minutes plus debrief (recommended duration 40 minutes). All of them are still in the code.

### Stage 3: "Could the model use this on a real patient?" questions

Three questions are asked now. Two were removed.

| Removed question | Kind | Right answer | Why it was useful |
|---|---|---|---|
| Outpatient follow-up attended | After discharge | No | A subtler leak: the follow-up is *booked* around discharge, but whether it was *attended* is only known weeks later. Its "Covers" note says the appointment itself is a few weeks after discharge. |
| Emergency admissions in previous 12 months | Known before admission | Yes | A second plain "yes", useful for balancing the list so "yes to everything" doesn't score well. |

**Questions asked now:** GP contacts (after discharge: no), age (known before admission: yes), length of stay (built up during the stay, available at discharge: yes).

**Where it lives:** `LEAKAGE_QUESTIONS` in [app/explain.py](app/explain.py). Uncomment the two commented entries to reinstate. The Stage 3 page, the sign-off missing-decisions list and the memo all read from this list, so nothing else needs changing.

**Also not asked:** community nursing visits (still on the importance chart as the top bar). It was dropped earlier because it duplicates GP contacts.

### Stage 4: follow-up / medication review is now optional

The use "A clinician brings forward follow-up, or reviews medication, for flagged patients" was compulsory and is now in the optional expander. It was the clearest example of "guiding clinical care, so likely a medical device", with the DCB0129/DCB0160 and Clinical Safety Officer content attached. Delay discharge covers the same lesson in the compulsory route.

**Compulsory now:** the support phone call (organising a service, probably not a device), delay discharge (clinical care, likely a device) and ban Friday discharges (misreading a pattern as a cause, with the data reveal).

**Friday was briefly optional and was reinstated as compulsory** (2026-10-14): it is the only place the "a prediction is not the effect of an action" lesson is shown with data, and that was judged too important to skip. The recommended duration was set at 40 minutes to allow for it.

**Where it lives:** the `"compulsory"` flag on each entry in [app/interventions.py](app/interventions.py). Set `followup` back to `True` to reinstate it. The Stage 4 progress bar, next-stage button and sign-off check all follow the flag.

**Optional uses now (Stage 4 expander):** follow-up / medication review, transport support, pharmacist medicines review, deprioritise "frequent readmitters" for elective care.

### Stage 5: two explanation statements removed

Four statements are asked now (two supported, two over-claims). Two were removed:

| Removed statement | Supported? | What it taught |
|---|---|---|
| "Because we can see why the model predicts what it does, it is safe to put into use." | No (over-claim) | An explanation is not evidence of accuracy, calibration, safety or fairness in your setting. That takes local validation and governance. The sign-off conditions and the "what an explanation can't tell you" panel cover the same point. |
| "These bars describe what the model relied on to reach its prediction for this patient. They do not show what would happen if we changed one of the factors." | Yes | The careful way to describe an explanation, and a model for what a good statement looks like. Largely duplicated by the causal over-claim and the "describe" statement. |

**Statements asked now:** describe the prediction and the biggest contributions (supported), the model is only moderately accurate (supported), reducing medications will prevent a readmission (over-claim), deprivation moves the prediction by only X points so it is fair (over-claim).

**Where it lives:** commented out in the `STATEMENTS` list in [app/app_pages/bringing_people.py](app/app_pages/bringing_people.py) and in `STATEMENT_SUPPORTED` in [app/explain.py](app/explain.py). To reinstate, uncomment both. The page asserts the two lists match exactly, so it will fail loudly if only one is changed.

### Discussion prompts on the stage pages

Each stage page used to end with a "Discuss:" prompt. They were removed from the stage pages because they risked derailing groups on the main route, and now live in an "Extension" expander at the end of the sign-off page (`DISCUSSION` in [app/ui.py](app/ui.py)).

| Stage | Prompt |
|---|---|
| 1. Is it any good? | The numbers look very strong. What would you want to ask the analytics team before signing this off? |
| 2. Who would we phone? | How would you find out how many calls the team can really make, and who should decide what the number is? |
| 3. Too good to be true? | v2 can still find some readmissions. Is that enough to justify a service, and what else would you need to know? |
| 4. What will we do with it? | Which use would you be most comfortable going ahead with first, and what would you need to see before you allowed a use that guides individual clinical care? |
| 5. Bringing people with you | What is the most useful question a sceptical consultant could ask about this model, and what evidence would you want before answering it? |
| 6. Sign-off | What changed your group's mind between your first impression and your final verdict, and which one condition would you most want to see in place? |

The Stage 5 prompt is the one discussed in [ONGOING-QUESTIONS.md](ONGOING-QUESTIONS.md); the same options (open, shortlist, two steps) apply to it in its new place.

**To put one back on its page:** add a `st.markdown("**Discuss:** ...")` line before the `ui.next_stage(...)` call for that stage.

## Switched off earlier

### Stage 5: the other two patients

Stage 5 shows one patient: a 46% predicted-risk patient who was not readmitted, with a strong blue bar (age 53). Three other patients are kept but switched off, along with the picker.

| Key | Patient | Notes |
|---|---|---|
| `high` | Highest predicted risk (66%) | Not readmitted; every bar is red, which is why it was replaced. |
| `typical` | A typical patient (9%) | Deprivation is the largest single contributor, which illustrates the fairness statement. |
| `low` | Lowest predicted risk (1%) | Mostly blue bars. |

**Where it lives:** `SHOW_OTHER_PATIENTS = False` near the top of [app/app_pages/bringing_people.py](app/app_pages/bringing_people.py). Set it to `True` to bring back the picker.

**The suggested one-line caption (not added):** "This is one patient with an elevated risk. Most patients are far lower (the median is about 9%), and for them many factors push the risk down." It heads off the misreading that a waterfall always looks like this.

### Stage 4 considerations: prediction timing

The "When is the prediction made?" note appears only for the follow-up, transport, pharmacy and delay-discharge items. With follow-up optional, only delay discharge shows it on the compulsory route.

## Ideas mentioned but not built

- **Stage 1:** a shortlist or "set the threshold yourself" variant of the "how accurate would a model be if it predicted nobody was readmitted?" guess. The current predict-then-reveal is the only "do" in that section.
- **Stage 5:** the closing "most useful question a sceptical consultant could ask" prompt as a shortlist of candidate questions. See ONGOING-QUESTIONS.md.
- **Stage 5:** a facilitator prompt asking whether the shown patient would be on the call list at the group's chosen capacity (cut-off about 23% at 100 calls per 1,000, so yes) and under the usual 50% cut-off (no). It links Stages 2, 3 and 5.
- **Stage 4:** making "N/A" in the harms multiselect clear the other choices, or warn when chosen together with a specific harm.
