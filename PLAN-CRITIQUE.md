# Critique of the Model Sign-off exercise plan

Reviewed on 2026-10-08, at the scaffold and synthetic-data stage. This review informs [PLAN.md](PLAN.md); [final-things-to-check.md](final-things-to-check.md) translates the findings into delivery checks.

## Overall assessment

The core concept fits the audience, and the synthetic data supports the intended teaching story. The main weaknesses are in the design of the decision questions rather than the existing code. Retain the readmission scenario and staged reveal, but revise those questions before building the pages.

At review time, the repository contained the planning documents, scaffold, banner/configuration and synthetic-data generator. The model/SHAP pipeline, app and browser deployment were not implemented, so usability and delivery readiness could not be assessed.

## What is working well

- **The sign-off panel role fits NHS leaders.** It practises commissioning and questioning evidence rather than asking learners to become analysts.
- **The staged reveal has a clear purpose.** Recording an initial verdict and revisiting it makes changes in judgment visible as evidence accumulates.
- **The scenario encourages transfer.** Readmission differs from the preceding missed-appointment example while reusing metrics, explanation and causal reasoning.
- **The data supports the reveal.** Regeneration reproduced the saved CSV exactly. The readmission rate was 12.05%; Friday rates were 15.8% versus 11.0%, with almost identical Friday/non-Friday rates within elderly care.
- **The clean model is usefully imperfect.** An exploratory held-out XGBoost check produced approximately 0.99 AUC for the leaky model and 0.72 for the clean model, supporting the intended contrast.
- **The proposed browser architecture is sensible.** Keeping model training and SHAP offline avoids requiring those packages in the learner's browser. This remains an architectural choice to verify through an actual stlite build.

## Priority revisions

### 1. Separate acceptability, fairness and regulation

Stage 3 proposes classifying interventions as acceptable, a fairness concern or a likely medical device. These categories overlap: a useful and regulated tool can also raise fairness concerns.

Ask separately whether the group supports the use, which harms need investigation and whether regulatory assessment is needed. Split transport support and pharmacy review into separate examples because they involve different actions and potential clinical purposes.

### 2. Make intervention effectiveness a central sign-off question

Removing leakage and identifying high-risk patients does not establish that support calls improve outcomes. The current flow risks leaving learners with that inference.

Include a decision about evaluating the service against usual care or random allocation of limited calls. Distinguish risk prediction from benefit from an action. Describe confusion-grid outcomes as historical readmissions, rather than suggesting correctly flagged patients are readmissions prevented by calls.

This is a particularly valuable commissioning lesson: a prediction model is only one part of a proposed service change.

### 3. Reconsider immediate right/wrong feedback

Immediate correct/incorrect feedback suits factual questions, such as whether a feature is available at discharge. It is less suitable for capacity choices, interventions and final verdicts, which require reasoned judgment.

Record the group's decision first and then reveal considerations. Allow defensible disagreement and reserve categorical feedback for questions with objectively correct answers. Otherwise the exercise may become a quiz about the author's preferred answer rather than a panel discussion.

### 4. Reduce the compulsory workload and pilot the timing

Six stages cover metrics, leakage, causality, regulation, fairness, SHAP and governance. This is ambitious for novices in about 35 minutes. The facilitator timings already total 35 minutes without clearly allocating time to all six stages and transitions.

Keep one patient waterfall and three intervention examples compulsory; offer the remaining examples as optional depth. Allocate time explicitly to the briefing and final sign-off, and distinguish group-work time from debrief time. Pilot with someone unfamiliar with ML before polishing the interface.

### 5. Assess the readmission intended purpose separately

CONTEXT.md says the appointment-reminder regulatory examples map directly onto readmission. That assumption needs revision. Administrative reminders and calls intended to prevent clinical deterioration may have different intended purposes.

Define what the call involves, who makes it and what actions follow before assigning regulatory feedback. MHRA guidance emphasises the software's function, intended user actions and position in the clinical pathway. Applying that guidance here is a review recommendation, not a definitive classification of the proposed tool. See [MHRA: crafting an intended purpose](https://www.gov.uk/government/publications/crafting-an-intended-purpose-in-the-context-of-software-as-a-medical-device-samd/crafting-an-intended-purpose-in-the-context-of-software-as-a-medical-device-samd).

Regulatory wording should be rechecked against current authoritative guidance before delivery; this critique does not constitute a complete regulatory audit.

### 6. Keep teaching claims consistent with generated evidence

The vendor pitch specifies 96% accuracy and AUC 0.95, but these are hard-coded before the final model pipeline exists. The exploratory leaky model achieved about 98% accuracy and 0.99 AUC. Derive headline figures from the final exported evidence, and state the cut-off associated with accuracy.

The generator's logistic AUC checks evaluate the same data used to fit the models. That is acceptable as a generation sanity check, but not evidence of generalisation. Use held-out data for the final model assertions and displayed performance.

The generator prints the largest within-specialty Friday gap but does not assert that it remains small. Add an appropriate check for the intended confounding story, allowing sampling variation. Avoid claiming that every observed gap vanishes exactly: the current largest gap is about 1.8 percentage points.

## Further conceptual corrections

### Deprivation: reconcile the teaching wording with the generator

The generator explicitly includes a direct deprivation term in the outcome equation, while PLAN.md describes the lesson as "proxy, not cause". Those descriptions are inconsistent.

Use the more defensible lesson: a predictive association does not establish which intervention would help. A known synthetic mechanism should not be presented as proof about deprivation's causal role in real patient populations.

### SHAP: support scrutiny as well as understanding

"Bringing people with you" should include communicating uncertainty, limitations and reasons to question a model. SHAP should not be presented primarily as a way to persuade stakeholders to approve it.

Retain the distinction between local and global explanations, explain contributions in percentage points, and reinforce that explanation does not establish causality, fairness or readiness to deploy.

### Capacity: make the denominator and selection rule explicit

The plan combines a probability-threshold slider with a weekly call-capacity framing and a grid out of 1,000 patients. Decide whether the learner controls a probability cut-off or the number of highest-risk patients selected. State the discharge volume and time period so capacity and counts can be interpreted together.

## Delivery and maintenance gaps

- Populate the standing checklist with novice timing, browser delivery, accessible chart labels, state persistence and memo download checks.
- Fix the exercise's place in the deck: regulation and causality questions depend on whether learners have already encountered those sections.
- Provide reproducible build/run instructions and dependency versions. No app walkthrough or stlite verification was possible at review time.
- Update stale planning statements as implementation proceeds, including the instruction to initialise Git when the repository is already initialised.
- Define the deployment URL and a practical workshop fallback for browser/network problems.

## Evidence and limits of the review

The review covered PLAN.md, CONTEXT.md, key-session-details.md, PROGRESS.md, the generator and accompanying local causality/regulation slides. The Google Slides deck could not be accessed, so the session brief supplied the earlier teaching context. No repository files were changed during the original review.

The additional diagnostic used 20,000 seeded rows, a stratified 85/15 train/test split and XGBoost with 250 estimators, maximum depth 3, learning rate 0.05 and random state 42. It was a feasibility check, not the planned final train/validation/test pipeline or a SHAP verification.

| Diagnostic | Result |
|---|---|
| Readmission prevalence | 12.05% |
| Friday vs other-day readmission rate | 15.84% vs 10.99% |
| Largest absolute within-specialty Friday gap | 1.79 percentage points |
| Leaky v1 held-out AUC | 0.9906 |
| Clean v2 held-out AUC | 0.7161 |
| Leaky v1 accuracy at a 50% cut-off | 97.67% |
| Clean v2 accuracy at a 50% cut-off | 88.23% |
| Clean v2 precision / recall when selecting the top 10% | 32.7% / 27.1% |
| Regenerated data matches saved CSV | Yes |

These results support the synthetic teaching setup. They do not validate an intervention or a real-world readmission model.
