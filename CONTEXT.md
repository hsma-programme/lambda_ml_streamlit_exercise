# Context for building the ML sign-off exercise

This file holds everything an agent needs to carry out [PLAN.md](PLAN.md) without re-exploring the related repositories. It was written on 2026-10-08.

## 1. The workshop and audience

- **Programme:** HSMA lambda, a series of standalone workshops spun off from the Health Service Modelling Associates (HSMA) programme. HSMA itself teaches the "doing" (analysts, clinicians, Python). Lambda teaches **mid-level to senior NHS leaders** to *commission* data science / OR projects and *critically interpret* their outputs.
- **Audience for this exercise:** senior NHS leaders with **no ML experience beyond what they've been taught that day**. Many work in organisations with little or no data science capacity.
  - The slides repo's `key-session-details.md` also has a leftover template paragraph saying students are "analysts, clinicians and managers… received training in Python". **Ignore it.** The course lead confirmed the no-code, no-prior-ML audience.
- **Implications for the app:**
  - no code shown to learners
  - plain English throughout
  - every technical term explained the first time it appears
  - natural frequencies ("out of 1,000 patients…") preferred over rates
  - no maths beyond percentages
- **Delivery:** 30–40 minutes in small groups, then a facilitator-led debrief. It runs in the browser via stlite, so there's no install and no server.
- **Course lead:** Sammi Rosser (s.j.rosser@exeter.ac.uk). Co-author of the slides: Dr Dan Chalk.

## 2. What learners have seen before the exercise

### Earlier deck (Google Slides, not readable by agents)
https://docs.google.com/presentation/d/1-exK-YwVmVKaq7ptvbh_WG9ULVnZ2GHu76T36yNli9g/edit?usp=sharing

According to the session brief, it covers:
- the HSMA programme and how lambda differs
- OR vs data science
- what AI and ML are
- classification problems
- the pros and cons of ML
- HSMA ML projects
- features, training sets and feature weighting
- overfitting and underfitting
- **performance metrics: accuracy, precision, recall**
- tree-based models vs neural networks

You can assume learners have heard of precision and recall. This section's deck now also introduces, briefly and on the DNA example, the accuracy trap with a rare outcome, AUC in plain words, and a capacity-based cut-off with a per-1,000 confusion grid (see section 3). **Don't rely on the AUC slide:** the course lead found groups reached the app without understanding AUC, so Stage 1 now teaches it itself (2026-10-21). You cannot assume they know sensitivity/specificity or calibration, so introduce these gently if they're used at all.

### This section's deck
The Quarto revealjs deck lives at `C:\Users\Sammi\lambda_ml_explainability_ethics_slides`. Its order (from `slides.qmd`) is:
1. `_SECTION_what_is_explainability.qmd`: black boxes, why explainability matters, and the claim that it helps spot **data leakage**.
2. `_SECTION_shap_demo.qmd`: the worked SHAP example on missed appointments (DNA).
3. `_SECTION_causality.qmd`: prediction vs causation.
4. `_SECTION_legality_and_regulations.qmd`: medical devices, DCB0129/0160, data protection, sharing models.

The exercise most naturally runs **after the SHAP demo**, either alongside or just after the causality and regulation content.

### After this section (delivered by Dan)
The following content comes later, so the exercise can *raise* fairness questions but shouldn't try to teach them fully:
- what could go wrong
- representation and transparency in training sets
- real-world harm examples

## 3. The DNA example in the slides

The exercise deliberately uses a *different* scenario so that learners transfer what they learned. They will have seen the following:
- **Data:** about 50,000 therapy appointments (2016–2022) in southern Brazil, covering speech therapy, psychotherapy, physiotherapy and occupational therapy. Patients are mostly children with an intellectual or motor disability. "About **1 in 10** appointments were missed." It is real open data (Salazar 2023, Mendeley, doi 10.17632/wm6w2fvkfj.1).
- **Model:** "A tree-based model (XGBoost)" that "Predicts who will **not attend** (1 = did not attend)". Its features cover the patient (age, sex, disability, distance from clinic), the appointment (specialty, time, day of week) and the weather (rain, temperature).
- **Performance:** the speaker notes say it "ranks a random non-attender above a random attender about 64% of the time" (that is, an AUC of about 0.64) and "you wouldn't deploy it as it is". **Modest performance is realistic.** The exercise's clean model (v2) should land in a similar range (AUC about 0.68–0.75).
- **"Is it any good?" slides** (straight after the dataset slide, before the SHAP plots; numbers are computed at render time from the test set):
  - "**Before we explain it: is it any good?**" A "model" that says everyone attends is **90% accurate**. The real model at the usual 50% cut-off flags only 10 of 7,440 appointments and is *also* 90% accurate. Key line: "When the thing you're predicting is rare, **accuracy mostly tells you how rare it is**." AUC is explained as "pick one patient who missed and one who attended. How often does the model give the one who missed the higher risk?" (64%; 50% = coin toss, 100% = perfect; "AUC or C-statistic").
  - "**Who gets a call? Choosing a cut-off**": calling the 100 highest-risk patients per 1,000 appointments gives a 2×2 grid of value boxes. **23** were called and would have missed (green), **77** were called but would have attended anyway (amber), **74** were not called and missed (red), **826** were not called and attended (grey). Precision is 23% vs about 10% for random calling, recall is 23 of 97, and accuracy *drops* to 85% while the model becomes more useful. Wording: "The model gives a **risk**, not a yes/no. Someone has to choose the **cut-off**, often based on capacity." The speaker notes say "The exercise lets you move this cut-off yourself."
  - **Implication for Stage 1:** learners have seen these ideas once. Stage 1 is *practice and transfer* on the readmission scenario, not a first introduction. Reuse the same wording and the same box colours and labels (green / amber / red / grey) so the link is obvious.
- **SHAP plots shown:** global bar, beeswarm, waterfall plots and force plots for the highest-, lowest- and median-risk patients.
  - Units are **percentage points** of predicted risk.
  - Waterfall plots show "*f(x)* is the final prediction… *E[f(X)]* is the average across all patients".
  - **Red pushes towards the outcome (not attending) and blue pushes away.**
  - The beeswarm note says: "Colours represent ACTUAL DATA VALUE (not SHAP value)".
- **Global vs local:** "**On average**, how much does each **feature** contribute…" vs "**For this one specific patient**…".
- **Leakage in the slides:** an ED story in the speaker notes. A model predicting admission at triage leans on "time in department", which is "a *consequence* of admission". The definition given is that "the model is using information it wouldn't have at the moment you actually need the prediction". The DNA model also left out `no_show_reason` because it "only exists for people who missed it". *This is why the exercise uses readmission, not ED admission, so learners discover leakage rather than recognise the slide example.*

## 4. Wording to reuse (match the slides)

- "SHAP explains **what the model relied on**, not **what would happen if we changed something**."
- Contrast the **prediction question** with the **effect of an action**.
- A good statement: "The model predicts this patient will [be readmitted], and it's basing its prediction on these factors". Not: "…and it's saying we should change these factors".
- "Always check yourself before making a causal claim from a non-causal model."
- Causality slide example: "distance → open a closer centre?", with age as the confounder. The exercise's Friday-discharge confounder plays the same role.
- "Small SHAP contributions for ethnicity or deprivation do not prove that a system is fair."
- Interventions such as "**overbooking slots** when patients are flagged as a high risk of not attending risk further widening health inequalities."
- Uplift framing from the "Who should we phone?" slide: **Sure things / Sleeping dogs / Persuadables / Lost causes**. Also: "Ranking by risk can still beat calling at random… you may want to test this against random calling".
- Units: "percentage points", "predicted risk of …".

## 5. Medical device and governance content (legality section)

- **Law:** the "**UK Medical Devices Regulations 2002 (UK MDR 2002)**", noted as "up to date at the time of writing (September 2026)". The slides repo's `final-things-to-check.md` flags rechecking for regulatory updates before delivery, and the same caveat applies to the app's wording.
- **Definition:** software is a device when "**intended to inform or carry out a medical purpose**", namely diagnosis, prevention, monitoring, or treatment or alleviation.
  - "You can't get around it by just labelling it 'do not use for clinical purposes'."
  - "It doesn't *need* AI". An if/else risk script can be a device. The same rules printed in "a laminated table" would not be.
  - "**Moving from organising services to guiding individual clinical care?** Check whether medical-device regulation now applies."
- **"Is it a medical device?" examples for DNA (do NOT assume these map onto readmission; reassess on the readmission intended purpose, see PLAN-CRITIQUE.md §5):**
  - A call-list of likely non-attenders: "No - this **wouldn't** be a medical device".
  - Changing **access** ("automatically offering them an online appointment instead", "free patient transport"): "*probably still wouldn't* be". These are "a **fairness** question".
  - Changing **clinical care** ("prioritising based on the predicted **clinical impact on them**", "automatically flagging high-risk non-attenders for a clinician to review or bring forward their follow-up"): "*would* be".
- **Health Institution Exemption:** applies only if the software is not transferred, is used on the same premises, follows leading practice, and has a designated responsible officer.
- **Clinical safety standards:**
  - "**DCB0129** - for whoever builds it (the manufacturer, which could be you)". In this exercise the model is built in-house, so it *is* you.
  - "**DCB0160** - for the organisation deploying it"
  - both need "a named **Clinical Safety Officer**, a hazard log and a safety case"
- **Also covered:** DPIA, DTAC, UK GDPR Article 6/9, data minimisation, and "**Fairness and non-discrimination are legal obligations too.**"
- **Sharing or receiving a trained model** (relevant here as local validation, since the data the model was built on may differ from live data): "validate locally", "check calibration - do predicted risks match observed rates? Recalibrate if not", "revisit decision thresholds for their setting", and monitor drift. These become the sign-off conditions in Stage 5.
- The slides never use the term "SaMD", so stick to "medical device".

## 6. Styling source: `C:\Users\Sammi\nhs_oa_vidigi_streamlit`

The app has no helper module and no palette. Its look comes from the following:
- **`.streamlit/config.toml`:**
  ```toml
  [server]
  enableStaticServing = true
  [theme]
  base="light"
  ```
- **`styles.css`** (shared). Pages inject it with `st.html(f"<style>{css}</style>")`. It sets:
  - the Google Font **Lexend** (200/300/700); body text is 18px, weight 200, colour **`#091747`** (navy)
  - Lexend for headings, with `h1` padding `0.25rem 0 1rem`
  - **tab styling** (lines 34–71):
    - tabs are bold, slate `#64748b` on `#f4f7fc`, with a `#8c9bb5` border and 0.4rem radius
    - hover border is `#091747`
    - the selected tab is `#091747` on `#fff5f5`, with a `#ff4b4b` border
    - the highlight bar is hidden
    - focus outline is `#be185d`
  - `.block-container { width:100%; padding: 4rem 2rem 2rem; max-width:initial; }`
  - Dead rules targeting `.st-emotion-cache-*` class names. Drop these.
- **Entry point `streamlit_app.py`:**
  - `st.set_page_config(page_title=..., layout="wide")` and `st.navigation([...], position="top")`, with no `pages/` directory.
  - The header banner CSS (lines 58–151) gives `header[data-testid="stHeader"]` a height of 5rem and a background of a dark gradient overlay over `banner.png`. Header text and icons are white, and the active top-nav link is highlighted.
  - Banner URL (lines 11–16): `/app/static/banner.png` locally, and the GitHub raw URL under stlite (`sys.platform == "emscripten"`).
  - Top-right icon links (GitHub, hsma.co.uk) use CSS mask SVGs, because the sanitiser strips inline SVG. They're built by `_svg_data_uri()` (lines 22–27) and inserted by a separate `st.html` block (lines 155–168). A styles-only `st.html` applies globally, so content and styles are kept in separate blocks.
- **Patterns for explaining things to non-technical users:**
  - A two-column title intro (`page_generate_animation.py:183-192`).
  - `st.info("**TASK:** …")` at the top of each tab.
  - Expanders for optional depth ("Interested in how … ? Click here").
  - Faded "ADVANCED" sections.
  - `st.columns([0.38, 0.62])` for controls next to output.
  - `st.caption` under each chart explaining how to read it.
  - `st.toast` after a reset.
  - A plain-English `help=` on every widget.
- **Quiz helpers** in `page_code_reorder_exercise.py`:
  - `choice(label, options, key)`: a selectbox with no default and the placeholder "Choose an answer".
  - `feedback(checks)`: shows `st.warning(hint)` for the first wrong answer, otherwise `st.success("Correct — well done!")`.
- **Charts:** plotly via `st.plotly_chart(fig, width="stretch")`, with no custom template.
- **stlite build:** `pack.py` uses `stlitepack` to produce `docs/index.html` (stlite 1.8.1, bundling Streamlit 1.57.0). It **pins `plotly==6.0.1`** because newer versions fail under stlite (see the comment at `pack.py:27-32`). It vendors a component rather than installing a wheel that needs Streamlit 1.58 or later. Copy this approach.
- **Update (2026-10-15, user-reported, unverified):** stlite 1.10.0 (React release) reportedly bundles Streamlit up to 1.65, which would relax the 1.57 limit below. Check when packing. Hosting on Streamlit Community Cloud is now the main plan, with stlite as a fallback.
- **Local environment there:** Streamlit 1.63 on Python 3.13. Target features that exist in Streamlit 1.57 so that stlite works:
  - `st.navigation(position="top")`
  - `st.container(key=...)`, which produces `.st-key-*` classes
  - `width="stretch"`
  - `st.html`

## 7. Reusable code from the slides repo

- `_SECTION_shap_demo.qmd`, lines 3–161, holds the full pipeline: feature engineering, the XGBoost config, a `TreeExplainer` with `model_output="probability"` and interventional perturbation, SHAP values rescaled ×100 into a new `shap.Explanation`, and selection of the high-, low- and median-risk patients (`idx_high`, `idx_low`, `idx_mid`).
- The slides repo's `pyproject.toml` (Python ≥ 3.12) lists pandas, numpy, scikit-learn, xgboost, shap, matplotlib and plotly[express]. A `.venv` exists there and could run the offline build scripts if this repo doesn't get its own environment.
- SHAP and XGBoost do **not** run reliably under Pyodide. They are build-time only, and the app reads precomputed files.

## 8. Rules for working in this repo

- **No sycophancy.** Give honest, objective feedback, and push back on weak ideas while staying friendly.
- **Never run `git commit`** unless explicitly asked in that turn. Drafting and staging changes are fine.
- Every commit needs a `Co-Authored-By: <model-name> <email>` trailer (via HEREDOC), one per contributing model.
- Label the data as **synthetic** in the app. No real patient data.
- Keep the app usable in about 35 minutes. Every stage must work with only clicks and radio buttons. Free text is optional.

## 9. Open items

- Banner image: reuse the vidigi `static/banner.png` unless the course lead supplies another.
- Deployment URL / GitHub Pages repository: not decided yet.
- Where exactly the exercise sits in the deck, and whether a slide introduces it: the slides don't say yet.
- The slides repo has a copy error on its first waterfall slide, which says "most likely to attend" for the *least* likely. It doesn't affect this repo, but don't copy that wording.
