# Plan: "Model Sign-off" ML playground (Streamlit + stlite)

> Read [CONTEXT.md](CONTEXT.md) first. It covers the audience, the slides this exercise accompanies, the exact wording to reuse, and where the styling and code to borrow come from.

> Before implementing the stages, read [PLAN-CRITIQUE.md](PLAN-CRITIQUE.md) for the review findings and recommended design revisions. Use [final-things-to-check.md](final-things-to-check.md) as the standing pre-delivery checklist. The critique records recommendations; the stage descriptions below have not yet been revised to incorporate them.

## Context
The explainability & ethics section of the HSMA lambda ML workshop needs a hands-on exercise for senior NHS leaders. They have no ML background beyond what they've been taught that day. The goal is an analogue of the HSMA DES/vidigi playground where learners act as the **approving panel** for a model and must question it before signing it off.

The exercise practises:
- interpreting metrics (accuracy, precision, recall)
- spotting **data leakage**
- deciding which **interventions are acceptable**
- applying the **medical-device boundary**
- using **SHAP** to bring stakeholders on board

It uses a fresh scenario, so the DNA example from the slides transfers rather than repeats.

The session brief asks for an exercise where learners "interpret outputs from a ML model and say what decisions they might make as a result, perhaps gradually giving them more information to get them to make questionable decisions initially". The staged design below does exactly that. Learners record a first-impression verdict on the vendor's headline claims, then revisit it as information is revealed.

**Decisions already made with the course lead (Sammi Rosser):**
- Scenario: **30-day emergency readmission**.
- Data: **synthetic, seeded**, clearly labelled as synthetic.
- Delivery: **in-browser via stlite**, with everything heavy precomputed. The shipped app imports only streamlit, pandas, numpy and plotly.
- Format: **30–40 minutes in small groups**, then a facilitator debrief.

**Metrics teaching:** the earlier deck teaches accuracy, precision and recall. The SHAP section of the slides now briefly introduces the accuracy trap, AUC in plain words, and a capacity-based cut-off with a per-1,000 confusion grid on the DNA example (see CONTEXT.md section 3). Stage 1 therefore **practises and transfers** these ideas to a new scenario rather than introducing them.

## Repo layout (`C:\Users\Sammi\lambda_ml_streamlit_exercise`)
```
build/                      # offline only, not shipped to stlite
  generate_data.py          # seeded synthetic discharges
  train_and_explain.py      # XGBoost v1 (leaky) + v2 (clean), SHAP → app/data/
  requirements-build.txt    # pandas numpy scikit-learn xgboost shap
app/
  streamlit_app.py          # entry: page config, banner CSS, st.navigation(position="top")
  styles.css                # copied/trimmed from vidigi app
  ui.py                     # load_css(), task_box(), stage_header(), decision-recording helpers
  charts.py                 # plotly confusion icon array, waterfall, global SHAP bar
  data/                     # precomputed CSV/JSON (predictions, SHAP, feature metadata)
  pages/ 0_briefing.py … 5_sign_off.py, facilitator.py
  static/banner.png
.streamlit/config.toml      # copied from vidigi app (enableStaticServing, base="light")
pack.py                     # stlitepack build → docs/index.html (pattern from vidigi pack.py)
requirements.txt            # streamlit, pandas, numpy, plotly==6.0.1 (stlite pin)
README.md, CLAUDE.md
```
Run `git init` (the folder isn't a git repo yet). Do not commit unless the user asks. See the commit rules in CONTEXT.md.

## Synthetic data (`build/generate_data.py`)
- About 20,000 discharges, generated with `numpy.random.default_rng(42)`.
- The outcome comes from a known logistic model. Tune its intercept so that about **12%** are readmitted.
- **Known at discharge:**
  - age, sex, deprivation decile
  - number of long-term conditions
  - emergency admissions in the previous 12 months
  - length of stay, number of medications
  - discharge destination (home / home with care package / care home)
  - lives alone, discharge specialty, discharge day
- **Planted leakage:** the extract was pulled 30 days *after* discharge. It therefore contains `GP contacts since discharge`, `Outpatient follow-up attended` and `Community nursing visits since discharge`, each generated *from* the outcome.
- **Planted confounder:** Friday discharges come disproportionately from frail elderly-care wards. Their raw readmission rate is higher, but the difference vanishes once frailty or ward is accounted for. This sets up the trap "ban Friday discharges?".
- **Fairness hook:** deprivation has a real effect in the data. This sets up "proxy, not cause" and whether an intervention widens or narrows inequality.
- **Sanity assertions:** the base rate falls between 11% and 13%, v1 AUC is at least 0.93, and v2 AUC falls between 0.68 and 0.75.

## Model + SHAP (`build/train_and_explain.py`)
Reuse the slides' pipeline pattern (setup cell of `_SECTION_shap_demo.qmd`, lines 3–161, in the slides repo):
- Model: `XGBClassifier(n_estimators=1000, learning_rate=0.05, early_stopping_rounds=50, eval_metric="logloss", random_state=42)`, with a 75/10/15 train/validation/test split.
- Explainer: `shap.TreeExplainer(model, data=shap.sample(X_train, 100, random_state=42), model_output="probability", feature_perturbation="interventional")`. Multiply the values by 100 so they're in **percentage points**, matching the slides.
- Train two versions:
  - **v1** uses all columns. This is what the vendor submits.
  - **v2** uses discharge-time features only.
- Export for each model:
  - test-set predicted probabilities and outcomes
  - per-patient SHAP values for a sample of about 2,000 rows
  - base values
  - mean |SHAP|
  - feature metadata (display name, whether it's known at discharge, plain-English description)
- The app computes all metrics live from these predictions using only numpy and pandas.

## App stages
The stages are guided. Decisions are stored in `st.session_state` and compiled at sign-off.

Every page follows the same pattern:
- It opens with an `st.info("**TASK:** …")` box.
- It ends with one or two group discussion prompts.
- Answers are recorded with radio buttons or checkboxes and get immediate `st.success`/`st.warning` feedback. This is the `choice`/`feedback` pattern from the vidigi app's `page_code_reorder_exercise.py`.

0. **Briefing.** The vendor pitches "ReadmitRisk v1" as "**96% accurate, AUC 0.95**", intended to "identify patients for a post-discharge support call". The group is the sign-off panel. **Before investigating**, they record a first-impression verdict (approve / approve with conditions / reject). It is revisited at the end.
1. **Is it any good?**
   - Accuracy trap: show a "model" that predicts nobody is readmitted and still scores 88% accurate.
   - A threshold slider drives a **1,000-patient confusion grid** (an icon array in plotly). The slider is framed as call capacity: "we can phone N patients a week".
   - The grid uses natural-frequency wording: readmissions caught, missed, and calls to people who wouldn't have been readmitted. Mirror the slides' "Who gets a call?" grid: the same four labels adapted to readmission, and the same green / amber / red / grey colours.
   - Keep the explanations short and refer back to the DNA slides ("as with the missed appointments…"), because learners have already seen these ideas once.
   - Link this back to the earlier deck's precision and recall.
   - Learners pick the trade-off they would accept.
2. **Too good to be true?**
   - Show the global SHAP bar for v1. Its top features are post-discharge.
   - Exercise: learners tick whether each feature is "known at the moment of discharge?", against a discharge-timeline graphic.
   - Reveal the leakage using the slides' definition: "information it wouldn't have at the moment you actually need the prediction".
   - Switch to v2. Performance drops to a realistic level, and the Stage 1 grid is shown again for v2.
3. **What will we do with it?**
   - Learners classify each candidate intervention as acceptable, a fairness concern, or a likely medical device:
     - support phone call
     - transport or pharmacy review
     - a clinician brings forward follow-up or reviews medications
     - delay discharge for high-risk patients
     - deprioritise "frequent readmitters" for elective lists
     - ban Friday discharges
   - Feedback uses the slides' wording: "intended medical purpose", "**access** to care vs **clinical care**", "a **fairness** question", DCB0129/DCB0160, Clinical Safety Officer.
   - Show the raw Friday rate, then the rates by ward, to make the point that a prediction is not the effect of an action.
4. **Bringing people with you.**
   - Show three patients (high, median and low predicted risk), each with a plotly waterfall:
     - red pushes towards readmission and blue pushes away
     - values are in percentage points
     - f(x) vs E[f(X)] is labelled as in the slides
   - Learners choose which statement to give a ward manager or a sceptical consultant. The options mix good statements with causal over-claims, such as "…so reducing their medications will prevent readmission".
   - Contrast the local and global views.
5. **Sign-off.**
   - An auto-filled summary of the group's decisions:
     - the metric trade-off they chose
     - the leakage they found
     - the uses they approved
     - device and governance actions
     - conditions: local validation, a calibration check, monitoring for drift, an equity audit
   - The group compares its final verdict with its Stage 0 first impression.
   - `st.download_button` produces a markdown "sign-off memo" for the debrief.
- **Facilitator page** (last in the nav, low-key): answers, timings (about 5 / 8 / 8 / 8 / 6 minutes) and debrief questions.

## Styling (from `C:\Users\Sammi\nhs_oa_vidigi_streamlit`)
- Copy `styles.css`: Lexend font, navy `#091747`, tab styling, pale `#f4f7fc` surfaces, `.block-container` width. Drop the dead `st-emotion-cache-*` rules.
- Copy the banner header CSS and the top-bar links block from `streamlit_app.py` (lines 11–16 and 58–168), including the stlite banner-URL switch (`sys.platform == "emscripten"`).
- Use the same `st.set_page_config(layout="wide")` and `st.navigation(position="top")`.
- Use the vidigi app's two-column title intro (`page_generate_animation.py:183-192`), with expanders for "want to know more?" detail.
- The vidigi app has no chart palette. For direction, use SHAP's red/blue convention; use a slate/navy neutral palette elsewhere. Load the `dataviz` skill when building charts and the `developing-with-streamlit` skill for the Streamlit work.
- Banner: reuse the vidigi app's `static/banner.png` unless the user supplies another image.

## Build / deploy
- `python build/generate_data.py && python build/train_and_explain.py` regenerates `app/data/`.
- `pack.py` uses stlitepack, following the vidigi app's `pack.py`. It includes the data files, pins `plotly==6.0.1` and outputs `docs/index.html` for GitHub Pages.

## Verification
1. Run the build scripts and make sure the base-rate and v1/v2 AUC assertions pass.
2. Run `streamlit run app/streamlit_app.py`. Click through every stage, check that decisions persist across pages, and check that the sign-off memo downloads.
3. Run `python pack.py`, open `docs/index.html` in a browser and repeat the walkthrough under stlite. Check load time and that the banner and fonts render.
4. Use screenshots to check the layout at laptop width.
5. Cross-check the wording against the slides: percentage points, the device-boundary phrasing, and "prediction vs effect of an action".
