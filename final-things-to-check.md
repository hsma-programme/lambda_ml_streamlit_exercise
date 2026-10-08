# Pre-delivery checklist

Use this checklist before delivering the Model Sign-off exercise. The design concerns behind these checks are recorded in [PLAN-CRITIQUE.md](PLAN-CRITIQUE.md). Leave items unchecked until verified against the final app and teaching materials; record the date and any outstanding issue alongside each completed check.

## Teaching flow and audience

- [ ] Confirm exactly where the exercise sits in the deck. Ensure learners have seen the required metrics, SHAP, causality and regulation material before questions that depend on it.
- [ ] Define the compulsory route and optional activities. Aim for about 35 minutes of group work, with the facilitator debrief separately allocated.
- [ ] Allocate time to all six stages, including briefing, navigation and final sign-off. Pilot with someone unfamiliar with ML and revise the workload using their actual completion time.
- [ ] Keep all required tasks possible with clicks, radio buttons or checkboxes. Free text is optional; no learner needs to read or write code.
- [ ] Explain technical terms on first use, favour counts out of 1,000, and match terminology and chart conventions to the preceding slides.
- [ ] Record the initial verdict before revealing evidence. Preserve it for comparison with the final verdict.
- [ ] Use factual feedback for factual questions. For capacity, intervention and sign-off decisions, record the group's judgment before revealing considerations and allow defensible disagreement.
- [ ] Separate intervention acceptability, potential harms/fairness and medical-device assessment. Split transport support and pharmacy review into distinct examples.
- [ ] Include an explicit question about how to evaluate whether support calls help, compared with usual care or random allocation of limited calls. Avoid implying that high predicted risk establishes benefit from an intervention.
- [ ] Make stakeholder communication cover limitations, uncertainty and scrutiny as well as explanation of predictions.
- [ ] Prepare facilitator prompts, reveal timings and a debrief that links the exercise to commissioning decisions. Keep the answer page out of the normal learner route.

## Data, metrics and explanations

- [ ] Clearly label all data as synthetic in the briefing, relevant charts and downloaded memo. Check that no real patient data has been included.
- [ ] Regenerate the data and final model exports using the documented environment. Record dependency versions and seed so the build can be reproduced.
- [ ] Verify the base rate is 11–13%, leaky v1 AUC is at least 0.93 and clean v2 AUC is 0.68–0.75 on held-out data. Do not present the generator's training-set AUC as validation evidence.
- [ ] Derive vendor headline figures, baseline accuracy and all displayed metrics from the exported evidence. State the cut-off or call capacity associated with accuracy, precision and recall.
- [ ] Define call capacity against a clear discharge volume and time period. Check that changing capacity selects the intended number of patients and that ties and extreme settings behave sensibly.
- [ ] Ensure the four confusion-grid counts add to 1,000, using an explicit and consistent sampling or rounding method. Match the green/amber/red/grey labels to the slides.
- [ ] Describe confusion-grid outcomes as historical readmissions. Do not label correctly flagged patients as readmissions prevented by a call.
- [ ] Verify the leakage reveal against the prediction moment: the three post-discharge features are unavailable at discharge and are excluded from v2.
- [ ] Check that the raw Friday association is visible and that stratifying by specialty largely removes it. Explain residual sampling variation; do not claim every observed within-specialty gap is exactly zero.
- [ ] Reconcile deprivation wording with the generator's direct deprivation term. Teach that predictive association does not establish which intervention would help.
- [ ] Verify patient records, predictions and SHAP exports refer to the same rows and model version. Confirm base value plus contributions equals predicted risk within numerical tolerance.
- [ ] Use percentage points for SHAP contributions, with red increasing and blue decreasing predicted readmission risk. Explain that the baseline is the explainer's reference expectation.
- [ ] Check that local waterfalls and global importance are distinguished, and that neither is presented as evidence of causality or fairness.
- [ ] Explain calibration in plain English if it appears as a sign-off condition. Avoid implying that good AUC establishes accurate risk percentages or readiness to deploy.

## Intended use and governance wording

- [ ] Define what the post-discharge support call involves, who makes it and what actions follow. Assess the readmission use case on its own intended purpose rather than copying the appointment-reminder classification.
- [ ] Recheck medical-device and related governance wording against current authoritative guidance before delivery. Record the source and review date; resolve ambiguous examples before assigning categorical feedback.
- [ ] Ensure medical-device status is not presented as equivalent to acceptability, and that administrative uses still require appropriate governance and consideration of harms.
- [ ] Check references to DCB0129/DCB0160, clinical safety roles, DPIA, DTAC and data protection for accuracy and relevant jurisdiction. Keep detail proportionate to the workshop.
- [ ] Make final sign-off conditions concrete: intended use, local validation, calibration, subgroup/equity checks, intervention evaluation, accountable owner, ongoing monitoring and criteria for pausing use.

## App and browser delivery

- [ ] Run the local app and complete every compulsory stage. Confirm answers persist across navigation and that initial and final verdicts remain distinct.
- [ ] Check incomplete journeys, returning to earlier stages, changing answers and resetting. The summary must reflect current answers and identify missing decisions.
- [ ] Download and inspect the sign-off memo. Check that it includes the group's actual decisions, conditions and synthetic-data label.
- [ ] Build the stlite artifact and repeat the walkthrough in the browser. Confirm the browser runtime needs no build-only packages such as XGBoost or SHAP.
- [ ] Test the deployed URL from a fresh browser session on a representative NHS network/device where possible. Check loading time, data files, banner, fonts and downloads.
- [ ] Check layout at typical laptop width and enlarged text/zoom. Confirm instructions, controls, charts and navigation remain readable without clipping.
- [ ] Check keyboard navigation, visible focus, readable contrast and chart labels that remain interpretable without colour alone.
- [ ] Document local run, data regeneration and browser build commands in the README, with compatible dependency versions.
- [ ] Confirm the learner URL and prepare a practical fallback, such as screenshots and printable decision prompts, for network or browser problems.

## Final rehearsal

- [ ] Cross-check final app wording and numbers against the slides and facilitator notes. Resolve contradictory or unfinished material used immediately before the exercise.
- [ ] Rehearse the complete learner route and debrief, including the v1-to-v2 reveal and explanation of why good prediction alone does not justify deployment.
- [ ] Record the tested build/version, review date and remaining issues. Resolve issues affecting correctness or delivery before the session.
