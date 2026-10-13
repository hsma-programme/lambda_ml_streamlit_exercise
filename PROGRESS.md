# Progress

Tracks work against [PLAN.md](PLAN.md). Last updated 2026-10-08.

## Status

| Chunk | Description | Status | Issues identified / points to address |
|---|---|---|---|
| 1 | Scaffold + synthetic data generation | Done (committed) | **Addressed:** generator now asserts within-specialty Friday gaps are consistent with sampling noise (max abs z below 3.5, pooled gap under 1 point; current max z 1.3, pooled -0.22%); deprivation wording in PLAN.md and the generator docstring now says it has a direct effect; build dependencies pinned in `requirements-build.txt` (still run via the slides repo's `.venv`, Python 3.14.3; a standalone venv and README instructions remain for chunk 6). |
| 2 | XGBoost v1/v2, SHAP, export to `app/data/` | Done (uncommitted) | **Addressed:** AUC assertions are now on the held-out test split; headline figures are in `meta.json`; row alignment and SHAP additivity (in probability units) are asserted. Still to do in the app: read displayed metrics from the exports rather than hard-coding. |
| 3 | App shell, shared helpers, Stage 0 (Briefing) | Not started | Hard-coded vendor figures may disagree with final results. Define the support call's intended purpose and fix the exercise's position in the deck. Preserve the initial verdict before reveals; distinguish factual feedback from feedback on judgment. Accessibility and navigation/state persistence remain untested. |
| 4 | Stages 1–2 (is it any good? / too good to be true?) | Not started | Probability cut-off and call-capacity controls are conflated; define the selection rule, denominator and time period. Make counts out of 1,000 consistent and describe historical readmissions, not prevented readmissions. Capacity choices should allow reasoned disagreement. |
| 5 | Stages 3–4 (interventions / bringing people with you) | Not started | Acceptability, fairness and medical-device categories overlap; assess them separately and split transport from pharmacy review. Do not assume appointment-reminder classifications transfer to readmission. Distinguish prediction from intervention benefit, explain residual Friday variation, and use SHAP to support scrutiny. Reduce compulsory examples to fit the time available. |
| 6 | Stage 5, facilitator page, `pack.py`, README | Not started | Sign-off needs explicit intervention evaluation and concrete ownership/monitoring conditions. Timings do not clearly cover all six stages and transitions; pilot with a novice and allocate debrief time separately. Browser delivery, memo download and accessibility remain unverified; deployment URL, reproducible instructions and workshop fallback are outstanding. |

Chunk 2–6 items are carried into the design: [PLAN.md](PLAN.md) was updated on 2026-10-08 to separate acceptability / harms / device assessment, add intervention evaluation to sign-off, record judgement answers before feedback, define capacity as number called, derive vendor figures from exports, and mark compulsory vs optional content. Timings, the deck position, the support call's intended purpose and the deployment URL still need decisions from the course lead.

These are review findings and implementation concerns, not changes to completion status. See [PLAN-CRITIQUE.md](PLAN-CRITIQUE.md) for the reasoning and [final-things-to-check.md](final-things-to-check.md) for delivery verification.

## Chunk 2: what exists

[build/train_and_explain.py](build/train_and_explain.py) trains v1 (all columns) and v2 (discharge-time only), explains both, and writes to `app/data/`. Runs in about 20 seconds. Same 75/10/15 stratified split for both models (15,000 / 2,000 / 3,000 rows).

| Result (held-out test, 3,000 rows) | v1 (leaky) | v2 (clean) | Target |
|---|---|---|---|
| AUC | 0.990 | 0.699 | v1 at least 0.93; v2 0.68–0.75 |
| Accuracy at 50% cut-off | 97.6% | 88.0% | |
| Patients flagged at 50% | 344 | 16 | |
| Trees after early stopping | 156 | 70 | |
| SHAP additivity max error | 0.0000 pp | 0.0000 pp | base + contributions = predicted risk |
| Explainer base value E[f(X)] | 11.5% | 11.7% | Close to the 12% base rate |

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
- **Background sample is 500, not the slides' 100.** With 100 the v2 base value came out at 13.9% against a true 12% average, which would confuse the "E[f(X)] is the average across all patients" explanation. 500 gives 11.7%.
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

Chunk 3: app shell and shared helpers (`streamlit_app.py`, `styles.css`, `ui.py`, `charts.py`, `requirements.txt`) and the Stage 0 Briefing page with the first-impression verdict. Before building Stage 1, decide the call-capacity framing (number called per 1,000 discharges) and check the Friday-specific SHAP values.
