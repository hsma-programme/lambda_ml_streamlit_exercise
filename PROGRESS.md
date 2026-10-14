# Progress

Tracks work against [PLAN.md](PLAN.md). Last updated 2026-10-08.

## Framing change (2026-10-13)

The model is now presented as built **in-house by analysts and data scientists**, with the group as the panel deciding whether it goes into use (previously a vendor's model the organisation was considering buying). Updated: Briefing and Stage 1–2 wording (no vendor; "ask the analytics team"; a line that responsibility for safety sits with the organisation), PLAN.md, CONTEXT.md (DCB0129 manufacturer is us), the build script docstring and the checklist wording. Leakage is framed as an easy mistake that sign-off exists to catch. PLAN-CRITIQUE.md is a dated review and was left as written; its "vendor" references predate this change.

Consequences to carry into chunk 5: the in-house case makes DCB0129 and the Health Institution Exemption directly relevant to Stage 3 (check the exact conditions against current guidance before delivery), and the "accountable owner" sign-off condition is now about a named internal owner.

## Status

| Chunk | Description | Status | Issues identified / points to address |
|---|---|---|---|
| 1 | Scaffold + synthetic data generation | Done (committed) | **Addressed:** generator now asserts within-specialty Friday gaps are consistent with sampling noise (max abs z below 3.5, pooled gap under 1 point; current max z 1.3, pooled -0.22%); deprivation wording in PLAN.md and the generator docstring now says it has a direct effect; build dependencies pinned in `requirements-build.txt` (still run via the slides repo's `.venv`, Python 3.14.3; a standalone venv and README instructions remain for chunk 6). |
| 2 | XGBoost v1/v2, SHAP, export to `app/data/` | Done (committed) | **Addressed:** AUC assertions are now on the held-out test split; headline figures are in `meta.json`; row alignment and SHAP additivity (in probability units) are asserted. Still to do in the app: read displayed metrics from the exports rather than hard-coding. |
| 3 | App shell, shared helpers, Stage 0 (Briefing) | Done (committed) | **Addressed:** headline figures read from `meta.json`; initial verdict stored under plain session-state keys, locked once recorded, and no right/wrong feedback; state persistence across pages tested with `AppTest`. **Still open:** the call's intended purpose is a draft needing the course lead's confirmation; position in the deck undecided; accessibility (keyboard, contrast, zoom) and the visual check not done; stlite run is chunk 6. |
| 4 | Stages 1–2 (is it any good? / too good to be true?) | Done (uncommitted) | **Addressed:** capacity is one control (patients phoned per 1,000 discharges) with the risk cut-off shown as a consequence; counts always sum to 1,000; outcomes described as historical readmissions; the trade-off decision is recorded before considerations are shown, with no right answer. **Still open:** discharge volume and time period are left to the facilitator; visual/screenshot and keyboard/contrast checks not done. |
| 5 | Stages 3–4 (interventions / bringing people with you) | Stages 3 and 4 done (Stage 4 uncommitted) | Acceptability, fairness and medical-device categories overlap; assess them separately and split transport from pharmacy review. Do not assume appointment-reminder classifications transfer to readmission. Distinguish prediction from intervention benefit, explain residual Friday variation, and use SHAP to support scrutiny. Reduce compulsory examples to fit the time available. |
| 6 | Stage 5, facilitator page, `pack.py`, README | Not started | Sign-off needs explicit intervention evaluation and concrete ownership/monitoring conditions. Timings do not clearly cover all six stages and transitions; pilot with a novice and allocate debrief time separately. Browser delivery, memo download and accessibility remain unverified; deployment URL, reproducible instructions and workshop fallback are outstanding. |

Chunk 2–6 items are carried into the design: [PLAN.md](PLAN.md) was updated on 2026-10-08 to separate acceptability / harms / device assessment, add intervention evaluation to sign-off, record judgement answers before feedback, define capacity as number called, derive headline figures from exports, and mark compulsory vs optional content. Timings, the deck position, the support call's intended purpose and the deployment URL still need decisions from the course lead.

These are review findings and implementation concerns, not changes to completion status. See [PLAN-CRITIQUE.md](PLAN-CRITIQUE.md) for the reasoning and [final-things-to-check.md](final-things-to-check.md) for delivery verification.

## Chunk 5, Stage 4: what exists

[app/app_pages/bringing_people.py](app/app_pages/bringing_people.py), with `app/explain.py` (patient selection and per-patient contributions) and `charts.waterfall`.

- v2 only (the model that could be used). One patient only: an **elevated-risk** patient (46%, not readmitted) chosen by rule in `explain.pick_patients` as the not-readmitted patient with a predicted risk of 40 to 50% who has the largest single downward contribution (Age = 53, -6.3 points), so the waterfall shows both red and blue bars and the top two factors are not dominant (long-term conditions +11.0, care home +8.5, emergency admissions +6.5; 5 other factors +5.6 in total). The earlier choice, the highest-risk patient (66%, all bars red), plus the typical (9%) and lowest-risk (1%) patients and the picker are kept in the code but switched off (`SHOW_OTHER_PATIENTS = False` in `bringing_people.py`). The statement about what the model is "basing" its prediction on was reworded to "the biggest contributions come from X (+a points) and Y (+b points)", because the top two factors are well under half of the movement from the average, chosen as the slides do: highest predicted risk, closest to the median, lowest among patients who were not readmitted.
- **Local / global tabs.** Waterfall in percentage points (red towards readmission, blue away; top six contributions plus "n other factors"; additivity asserted to 0.01 points), and the v2 global bar with a local vs global explanation.
- **Outcome shown:** the page states whether the patient was in fact readmitted. The shown patient (46%) was not readmitted, which makes the point that a predicted risk is not a forecast.
- **Statement choice (revised at your request):** each of the six statements is its own card with a Yes / No radio ("we'd be happy to say this" / "we wouldn't say this"), replacing the first multiselect version; the check button unlocks only when all six are answered. The feedback separates two things that were previously blurred: a green/red badge says whether the *statement* is supported by the explanation, and a separate green "correct" / red "not quite" box says whether the *group's answer* matched, with a summary count at the top. Six statements for a ward manager or sceptical consultant (three supported: description, uncertainty/AUC, "what the model relied on"; three overreach: causal medication claim, deprivation-means-fair, explainable-means-safe). The group answers each one, then each statement is marked supported or goes further than the evidence with an explanation. This deliberately has clearer answers than the Stage 3 judgement calls, and the page says so.
- "What an explanation can't tell you" (not a cause, not proof of fairness, not proof of readiness, a way to ask better questions) and a discussion prompt about scrutiny.
- Choices are stored in `st.session_state["stage4_statements"]`.

Verification: `AppTest` (renders for all three patients, choices recorded and persist across navigation, no exceptions) and a unit check that base + contributions equals f(x) for each patient.

Open points: the statement wording is mine and should be reviewed; the fairness statement uses the patient's actual deprivation contribution so it stays truthful; not checked in a browser (waterfall layout, label lengths); only one patient is compulsory, as the review recommended.

## Chunk 5, Stage 3: what exists

**Intended purpose confirmed (2026-10-13):** the call is a wellbeing check only, limited to signposting and recording, with no clinical assessment, made by a member of the community discharge team within two working days of discharge; the software only produces the prioritised list. The Briefing and Stage 3's phone-call item use this wording, and the device reading for the phone call changed from "depends on the intended purpose" to "probably not a medical device, as described", with the caveat about what would change it. The Briefing now says the caller could be a nurse or a care coordinator and the call stays a wellbeing check either way. Stage 3 defines "clinician" (any registered health professional, including nurses) and has a "watch for drift" note: a use is assessed as designed, and function creep needs a documented intended purpose and someone accountable for noticing it.

[app/app_pages/what_will_we_do.py](app/app_pages/what_will_we_do.py), with content in [app/interventions.py](app/interventions.py) and `friday_bars` in `charts.py`.

- Seven candidate uses of the list: **compulsory** support phone call, clinician brings forward follow-up / reviews medication, and delay discharge for high-risk patients; **optional** (in an expander) transport support, pharmacist medicines review (split from transport, as the review asked), ban Friday discharges (with the data reveal), and deprioritise "frequent readmitters" for elective care. (Friday was originally compulsory and was swapped for delay discharge at your request; the pedagogical trade-off is noted below.)
- A banner says the app won't mark answers right or wrong at this stage. Where relevant (follow-up/medication review, transport, pharmacist review, delay discharge) the considerations note that the model could be rebuilt to predict earlier, e.g. the day before discharge, with the cost that it could use less information and would need re-testing.
- For each, three separate questions (support? harms to investigate? likely a medical device?), recorded before any considerations are shown, with no correct/incorrect banner. Considerations give a device reading, harms/fairness and "does it help?", plus a caveat to check current MHRA guidance and the Clinical Safety Officer. Answers can be changed.
- Friday: after the group records its answers, a grouped bar chart and text show Friday vs other days overall (15.8% vs 11.0%), the elderly-care share of Friday discharges (60% vs 9%), and the near-equal rates within elderly care (19.9% vs 19.9%) and other wards (9.6% vs 10.1%), with the slides' "prediction is not the effect of an action" point and a caveat that the figures can't prove a ban would have no effect.
- "Because we built it ourselves": DCB0129 / DCB0160 and the Clinical Safety Officer, plus an expander on the Health Institution Exemption (conditions as listed in the slides).
- Decisions are held in `st.session_state["interventions"]` (a plain dict keyed by use) for the Stage 5 summary.

Verification: `AppTest` walkthrough (page renders; three compulsory uses recorded; Friday section appears; progress reads 3 of 3; answers persist across navigation; no exceptions).

Open points for review:
- **The device readings are mine**, applied from the slides' framework to a readmission use. They need your (and ideally a Clinical Safety Officer's) review, especially "support phone call: depends on intended purpose", and the exemption wording, before delivery. The phone-call reading rests on the confirmed wellbeing-check description above.
- Wording avoids claims about what "most groups" conclude.
- **Pedagogical trade-off of the Friday swap:** the Friday item is the only place the causal-confounding lesson is shown with data, and with it optional many groups will skip it. Delay discharge and the follow-up item are both "clinical care, likely a device", so the compulsory set now has two similar answers and no causal-reading example. Alternative: make Friday compulsory and move follow-up to optional.
- Whether three compulsory uses fit the time available is untested; the optional four may be too many.
- Not checked in a browser; keyboard/contrast checks outstanding.

## Chunk 4: what exists

**Stage 2 factor list varied (2026-10-13):** the three post-discharge columns were near-duplicates (same 30-day window), so the exercise now asks five of the eight factors on the chart, one of each kind: before admission (age, emergency admissions in the previous 12 months), **built up during the stay so available at discharge but not at admission** (length of stay), and after discharge (GP contacts; outpatient follow-up attended, whose "Covers" note now refers to the appointment itself a few weeks after discharge). Community nursing visits stay on the chart but aren't asked. The length-of-stay explanation makes the point that the moment the model is run decides what counts (at admission it would be leakage). 3 "yes" and 2 "no", so "yes to everything" scores 3 of 5.

**Stage 2 exercise made fair (2026-10-13):** the "known at discharge?" question gave its own answer away: the feature names ended "since discharge" and the descriptions said "only known afterwards". Names and descriptions are now neutral (e.g. "GP contacts", "Number of contacts with the patient's GP practice recorded in the extract"), the page states that the extract was produced 30 days after discharge (the fact learners need to reason from) with an optional hint. A first neutral version was too vague ("GP contacts" could be read as all prior contacts, a general frailty marker), so each factor now also shows a data-dictionary style **Covers** note (e.g. "the 30 days beginning on the day of discharge" vs "the 12 months before this admission"); learners still have to compare that with the moment of prediction. The two answer options were also reworded from "known at discharge" / "only known later" to "Yes: the model would have this when it is run on a real patient" / "No: this wouldn't exist yet when the model is run on a real patient", and the question now says the model would be run as the patient leaves hospital, and the explanation of each answer (`why` in `features.json`) is shown only after the learner answers.

**SHAP background bug fixed (2026-10-13):** shap silently subsamples a background set to 100 rows (warning: "Background dataset has 500 samples but max_samples=100"), so the earlier "500 background" note was wrong; the improved base values came from a different 100-row draw. `explain()` now passes a masker with `max_samples` raised, so 500 rows are really used. SHAP exports regenerated: base values are now 12.5% (v1) and 12.8% (v2) against a true average of about 12%; AUCs and predictions are unchanged; v2's third and fourth features swapped places (deprivation now ahead of discharge specialty).

**Label wording, second pass (2026-10-13):** grid labels now read "Model would recommend a call, and in reality they were readmitted" (and the three other combinations), with the same "model would recommend" / "in reality" framing in the thought-experiment box, caption, cut-off note and Stage 2 text. The icon-array legend is now vertical (the labels are long) and the chart a little taller.

**Cut-off made prominent (2026-10-13):** Stage 1 now shows two large figures above the grid (calls per 1,000, and "phone anyone with a predicted risk of at least X%") with a note that the cut-off follows from capacity and the change in percentage points each time the slider moves. **Bug fixed along the way:** the slider's default was passed as a changing `value=`, which changes the widget's identity on every move and could reset it; it is now a keyed widget seeded once from the plain `capacity_choice` key. The bug was in the committed chunk 4 version.

**Wording fix (2026-10-13):** the grid labels used "Called", which read as calls that had actually happened. They are now "Would be called …" (the model's list, applied retrospectively; no calls were made) with "was readmitted" as the real outcome. Stage 1 also has a "thought experiment" box stating that nobody was actually phoned, and the precision/recall text uses "would" throughout.

- [app/metrics.py](app/metrics.py): `call_outcomes(p, y, calls_per_1000)` (the slides' method: scale held-out test set to 1,000, round so the four counts sum to exactly 1,000, stable sort for ties) and `baseline_accuracy`. numpy only.
- [app/charts.py](app/charts.py): `icon_array` (1,000 markers, 40 x 25, four groups with different marker shapes) and `importance_bar` (mean |SHAP| in percentage points, one navy hue).
- [app/app_pages/is_it_any_good.py](app/app_pages/is_it_any_good.py): Stage 1 on v1. Accuracy check (88% for "nobody" vs 97.6%), capacity slider (20 to 300 per 1,000), icon array, precision/recall in plain English, a table view, then the recorded trade-off decision followed by things to weigh.
- [app/app_pages/too_good.py](app/app_pages/too_good.py): Stage 2. v1 importance bar, discharge timeline, five "could the model use this on a real patient?" questions with immediate feedback (the only categorical feedback), leakage reveal gated on all six, v1 to v2 rebuild with side-by-side metrics and icon arrays at the group's capacity, v2 importance, then a recorded "has this changed your view?" (`stage2_verdict`).
- `ui.py` gained `factual_check`, `load_shap_summary` and `capacity`.

Numbers shown (held-out, per 1,000 discharges, 100 calls):

| | v1 | v2 |
|---|---|---|
| Model would recommend a call; readmitted | 97 | 33 |
| Model would recommend a call; not readmitted | 3 | 67 |
| Model would not recommend a call; readmitted | 23 | 87 |
| Model would not recommend a call; not readmitted | 877 | 813 |
| Precision / recall | 97% / 81% | 33% / 28% (random calling about 12%) |

Verification done: unit checks that the four counts sum to 1,000 for every capacity 0 to 1,000 and that precision at 100 per 1,000 matches an independent calculation; `AppTest` walkthrough (slider changes counts, decision recorded, factual feedback fires, reveal gated until all five answered, v2 view renders, state survives navigation); the dataviz palette validator was run on the icon-array colours.

Palette validation: light-mode green / amber / red / grey pass lightness, CVD separation (worst adjacent 8.2) and normal-vision floors. The grey fails the chroma floor and is below 3:1 contrast. This is intentional (it is the large "nothing happens" group and should recede), relieved by a distinct marker shape, a labelled legend with counts, hover text and the table view. The app is light-theme only, so dark mode was not validated (the amber and red steps would need re-stepping for a dark surface).

Notes and caveats:
- **v1 really does beat the "nobody" baseline** (97.6% vs 88%), so the accuracy trap is gentler than in the DNA slides; the page leans on base rate and precision/recall, and Stage 2 explains why v1 is so good.
- Answers to the five factual questions are kept under a plain session key so they survive navigation.
- Per-1,000 counts are scaled from 3,000 test patients and can be out by a few patients; the page says so.
- Not covered by `AppTest`: how the charts actually look in a browser.

## Chunk 3: what exists

Run from the repo root: `streamlit run app/streamlit_app.py` (root `.streamlit/config.toml` enables static serving for the banner).

- [app/streamlit_app.py](app/streamlit_app.py): page config, banner and top-bar CSS (from the vidigi app), `st.navigation(position="top")` over seven pages, shared state init. Only the hsma.co.uk icon is linked; the GitHub icon waits for a repository URL.
- [app/styles.css](app/styles.css): vidigi stylesheet trimmed (Lexend, navy, tab styling, block container); dead `st-emotion-cache-*` and exercise-specific rules dropped.
- [app/ui.py](app/ui.py): `load_css`, `init_state`, `record_decision`/`get_decision`, cached loaders for `meta.json`, `features.json`, `test_predictions.csv`, `task_box`, `stage_header`, `synthetic_notice`, `stub`.
- [app/app_pages/briefing.py](app/app_pages/briefing.py): analytics team's summary (97.6% accurate, AUC 0.99, from `meta.json`, 50% cut-off stated), AUC explained once, panel role, draft call description, synthetic notice, first-impression radio (no default) with optional reason and a "Record" button. Once recorded it is shown read-only and not overwritten.
- Stub pages for stages 1–5 and the facilitator page, so navigation and state persistence can be exercised.
- [requirements.txt](requirements.txt): streamlit, pandas, numpy, plotly==6.0.1.

Verification done: `AppTest` run (no exceptions; verdict recorded; persists across a page switch; widget replaced by read-only message), and a headless `streamlit run` returning 200 for health and the banner. Not done: visual screenshot, keyboard/contrast checks.

Deviations and notes:
- **Pages folder is `app/app_pages/`, not `app/pages/`.** Streamlit's guidance is that `pages/` conflicts with legacy auto-discovery. PLAN.md's layout should be read accordingly.
- **`charts.py` is deferred to chunk 4**, where the first chart is built.
- **Plotly vs Streamlit's guidance:** Streamlit's bundled guidance prefers Vega-based charts, but PLAN.md specifies plotly (icon array, waterfall) and the stlite pin is already set. Keep plotly; revisit if a chart is awkward.
- **`persist_state` not used.** It exists in newer Streamlit but isn't guaranteed in the stlite-bundled 1.57. Plain session-state keys are used instead.
- The stlite banner URL points at the vidigi repo's raw file as a placeholder (flagged with a TODO).
- The Briefing AUC explanation says the figure is quoted at a 50% cut-off. Stage 1 will show that at this cut-off v2 flags only 16 of 3,000 patients.

## Chunk 2: what exists

[build/train_and_explain.py](build/train_and_explain.py) trains v1 (all columns) and v2 (discharge-time only), explains both, and writes to `app/data/`. Runs in about 20 seconds. Same 75/10/15 stratified split for both models (15,000 / 2,000 / 3,000 rows).

| Result (held-out test, 3,000 rows) | v1 (leaky) | v2 (clean) | Target |
|---|---|---|---|
| AUC | 0.990 | 0.699 | v1 at least 0.93; v2 0.68–0.75 |
| Accuracy at 50% cut-off | 97.6% | 88.0% | |
| Patients flagged at 50% | 344 | 16 | |
| Trees after early stopping | 156 | 70 | |
| SHAP additivity max error | 0.0000 pp | 0.0000 pp | base + contributions = predicted risk |
| Explainer base value E[f(X)] | 12.5% | 12.8% | Close to the 12% base rate |

Top features: v1 is led by the three post-discharge columns (community nursing visits, GP contacts, outpatient follow-up), then age; v2 is led by long-term conditions, age, discharge specialty and deprivation decile.

Exports in `app/data/`:
- `test_predictions.csv`: test-set outcomes, v1 and v2 probabilities, discharge day and specialty.
- `shap_v1.csv`, `shap_v2.csv`: SHAP in percentage points for the same 2,000 test rows, with one-hot categories summed back to one value per feature (so a waterfall shows "Discharge specialty", not six dummy columns).
- `shap_patient_values.csv`: those patients' feature values, for waterfall labels.
- `shap_summary.json`: base values and mean |SHAP| per feature, per model.
- `features.json`: display name, known-at-discharge flag and plain-English description.
- `friday.json`: Friday vs other days over the whole extract, overall and split elderly care / other wards.
- `meta.json`: seed, library versions, split sizes, base rates, metrics.

Notes and deviations:
- **Background sample is 500, not the slides' 100.** With 100 the v2 base value came out at 13.9% against a true 12% average, which would confuse the "E[f(X)] is the average across all patients" explanation. (Originally this note claimed 500 gave 11.7%, but shap was still subsampling to 100; fixed on 2026-10-13, base values are now 12.5% / 12.8%.)
- **v2 at the 50% cut-off flags only 16 of 3,000** and is 88.0% accurate, about the same as predicting nobody (88.0% of the test set is not readmitted). This mirrors the slides' DNA story, but Stage 1 must work through a capacity-based cut-off, not 50%.
- **v2 AUC is 0.699**, near the lower end of the 0.68–0.75 band, in line with the DNA model's 0.64 in the slides. The assertion holds, but if the dataset is regenerated with a different seed, check it.
- Friday (whole extract): 15.8% vs 11.0% overall; elderly care 19.9% Friday vs 19.9% other days; other wards 9.6% vs 10.1%. 60% of Friday discharges are elderly care vs 9% of other days.
- v2 gives discharge day small but non-zero contributions (std 0.49 pp, max 2.7 pp over the 2,000 patients), so the model does pick up some day-of-week signal (probably Friday standing in for elderly care where specialty is only partly captured). That is useful for Stage 3 ("the model uses Friday, but that isn't the effect of changing Friday"), but check the Friday-specific values before wording it.

## Chunk 1: what exists

- Git repo initialised. Commits: `089c5b9` (scaffold + generator), `134fff5` (stronger Friday confounder).
- Folder layout created: `build/`, `app/data`, `app/pages`, `app/static`, `.streamlit/`.
- Copied from the vidigi app: `.streamlit/config.toml`, `app/static/banner.png`.
- [build/generate_data.py](build/generate_data.py): seeded (42), 20,000 synthetic discharges, writes `build/out/discharges.csv` (git-ignored).
- [build/requirements-build.txt](build/requirements-build.txt).
- Build scripts run with the slides repo's `.venv` (`C:\Users\Sammi\lambda_ml_explainability_ethics_slides\.venv`), which already has pandas, scikit-learn, xgboost 3.4 and shap 0.52.

## Generator results (latest run)

| Check | Result | Target |
|---|---|---|
| Base readmission rate | 12.05% | 11–13% |
| Raw readmission rate, Friday vs other days | 15.8% vs 11.0% | Visible gap |
| Elderly care, Friday vs other days | 19.9% vs 19.9% | No gap within ward |
| Logistic AUC, all columns (incl. leaky) | 0.988 | v1 at least 0.93 |
| Logistic AUC, discharge-time only | 0.727 | v2 0.68–0.75 |

The AUCs are from a quick logistic check inside the generator. The binding AUC assertions go in `build/train_and_explain.py` (chunk 2) using XGBoost.

## Decisions and deviations from PLAN.md

- **Unobserved risk term** (`HIDDEN_SD = 2.4`) added to the outcome model. With only the listed features the clean model's AUC was 0.83, well above the target. The term represents real-world risk the data doesn't capture, and gives a realistically modest v2.
- **Friday confounder** driven by the elderly-care share of Friday discharges (65%, others 10–12%), because 40% gave only a ~3 point raw gap.
- No AUC or rate assertion has been loosened. The generator asserts the base rate range, and a raw Friday rate at least 15% above other days.

## Known issues and notes for later chunks

- Within-ward Friday gaps in the small wards (surgery, respiratory, orthopaedics) wobble by up to about 1.8 points from sampling noise. For the Stage 3 reveal, show raw Friday vs other days, then elderly care vs the other wards, rather than all six wards.
- [final-things-to-check.md](final-things-to-check.md) now contains the pre-delivery checklist; its checks remain to be completed against the final app and teaching materials.
- Git warns about LF→CRLF on commit. Harmless, but a `.gitattributes` would silence it.
- Open items from [CONTEXT.md](CONTEXT.md) §9 still stand: banner image (currently reusing the vidigi one), deployment URL / GitHub Pages repo, and where the exercise sits in the deck.

## Next

Chunk 6: Stage 5 sign-off (summary of the group's decisions, comparison of final verdict with the first impression and the Stage 2 view, concrete conditions including intervention evaluation and a named internal owner, markdown memo download), the facilitator page (answers, timings, debrief), `pack.py`, README. Still to decide: deployment URL, deck position, timings, and a pilot with someone unfamiliar with ML.
