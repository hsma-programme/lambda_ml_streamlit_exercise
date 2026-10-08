# Progress

Tracks work against [PLAN.md](PLAN.md). Last updated 2026-10-08.

## Status

| Chunk | Description | Status | Issues identified / points to address |
|---|---|---|---|
| 1 | Scaffold + synthetic data generation | Done (committed) | Within-specialty Friday gaps are printed but not asserted; allow sampling variation in the check. Generator gives deprivation a direct effect, conflicting with the plan's "proxy, not cause" wording. Build dependencies are unpinned and currently rely on the slides repo's environment. |
| 2 | XGBoost v1/v2, SHAP, export to `app/data/` | Not started | Generator AUCs are measured on training data; final assertions and displayed metrics need held-out evaluation. Derive headline figures from exports, and verify row alignment and SHAP additivity in probability units. Exploratory held-out results support feasibility but do not replace the final pipeline checks. |
| 3 | App shell, shared helpers, Stage 0 (Briefing) | Not started | Hard-coded vendor figures may disagree with final results. Define the support call's intended purpose and fix the exercise's position in the deck. Preserve the initial verdict before reveals; distinguish factual feedback from feedback on judgment. Accessibility and navigation/state persistence remain untested. |
| 4 | Stages 1–2 (is it any good? / too good to be true?) | Not started | Probability cut-off and call-capacity controls are conflated; define the selection rule, denominator and time period. Make counts out of 1,000 consistent and describe historical readmissions, not prevented readmissions. Capacity choices should allow reasoned disagreement. |
| 5 | Stages 3–4 (interventions / bringing people with you) | Not started | Acceptability, fairness and medical-device categories overlap; assess them separately and split transport from pharmacy review. Do not assume appointment-reminder classifications transfer to readmission. Distinguish prediction from intervention benefit, explain residual Friday variation, and use SHAP to support scrutiny. Reduce compulsory examples to fit the time available. |
| 6 | Stage 5, facilitator page, `pack.py`, README | Not started | Sign-off needs explicit intervention evaluation and concrete ownership/monitoring conditions. Timings do not clearly cover all six stages and transitions; pilot with a novice and allocate debrief time separately. Browser delivery, memo download and accessibility remain unverified; deployment URL, reproducible instructions and workshop fallback are outstanding. |

These are review findings and implementation concerns, not changes to completion status. See [PLAN-CRITIQUE.md](PLAN-CRITIQUE.md) for the reasoning and [final-things-to-check.md](final-things-to-check.md) for delivery verification.

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

Chunk 2: write `build/train_and_explain.py` (v1 all columns, v2 discharge-time only; XGBoost config and SHAP explainer as in PLAN.md), assert v1 AUC at least 0.93 and v2 AUC 0.68–0.75, and export predictions, a ~2,000-row SHAP sample, base values, mean |SHAP| and feature metadata to `app/data/`.
