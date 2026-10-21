import numpy as np
import streamlit as st

import charts
import metrics
import ui

GUESSES = [
    "About half (50%)",
    "About three quarters (75%)",
    "About nine in ten (90%)",
    "About the same as the model (97%)",
]

AUC_CHECK = [
    "It correctly predicts half of patients",
    "It finds half of the patients who are readmitted",
    "It puts a readmitted patient above one who wasn't readmitted no more often than tossing a coin",
]

meta = ui.load_meta()
preds = ui.load_predictions()
v1 = meta["models"]["v1"]
base = metrics.baseline_accuracy(preds["readmitted_30d"])

ui.stage_header(
    "1. Performance: Is it any good?",
    "We are testing our analytics team's model, ReadmitRisk v1, on patients it never saw during training.",
    minutes="stage1",
)
ui.task_box(
    "Check what the two headline numbers in the team's summary, accuracy and AUC, really tell you."
)

st.subheader("The headline accuracy")
with st.container(border=True):
    st.metric("ReadmitRisk v1 at the usual 50% cut-off", f"{v1['accuracy_at_50pct']:.1%} accurate")
    st.caption(
        f"It flags {v1['n_flagged_at_50pct']} of {meta['n_test']:,} patients "
        "(a patient is flagged if their predicted risk is 50% or more)."
    )
st.markdown(
    "Someone on the panel asks: **\"How accurate would a model be if it simply predicted that nobody "
    "would be readmitted?\"**"
)
if st.session_state.get("baseline_guess"):
    st.session_state.setdefault("guess_widget", st.session_state["baseline_guess"])
guess = st.radio("What would your group guess?", GUESSES, index=None, key="guess_widget")
# The rest of the page waits for the guess, so the answer isn't given away before the group commits.
if guess:
    st.session_state["baseline_guess"] = guess
    with st.container(border=True):
        st.metric("A 'model' that predicts *nobody* is readmitted", f"{base:.0%} accurate")
        st.caption("It never finds a single readmission, and still scores this well, on this data.")
    st.markdown(
        f"That {base:.0%} isn't a fixed score for a 'model' that does nothing. It is simply the share of patients "
        f"here who were **not** readmitted. Only about **{meta['base_rate_test']:.0%}** of our patients are readmitted, "
        f"so saying \"nobody\" is right {base:.0%} of the time. If half of patients were readmitted, the same 'model' "
        "would score only 50%. When what you are predicting is rare, **accuracy mostly tells you how rare it is**. "
        "A better question is how well the model finds the patients who are readmitted, and what it costs us in calls."
    )

    st.divider()
    st.subheader("Another number you'll hear: AUC")
    st.markdown(
        "Because accuracy can mislead when the outcome is rare, teams often quote **AUC** as well. Ours did: "
        f"**{v1['auc_test']:.2f}**. It asks a different question: does the model put the patients who are readmitted "
        "**higher up the list** than the patients who aren't?"
    )
    st.markdown(
        "**Test it yourself.** Press **Pick a random pair** below. The app picks one patient who was readmitted "
        "and one who wasn't, at random, and shows you which one the model gave the higher risk. Try a few."
    )

    y = preds["readmitted_30d"].to_numpy()
    p1 = preds["p_v1"].to_numpy()
    # Plain keys, so the tally survives page switches and a refresh (see persistence.py).
    # auc_pairs holds the random draws behind the tally; auc_shown is the pair on screen,
    # which may be a deliberately wrong one that is kept out of the tally.
    pairs = st.session_state.setdefault("auc_pairs", [])

    # Callbacks run before the page is drawn, so the button labels below already reflect the new pick.
    def pick_pair():
        pair = list(metrics.draw_pair(p1, y, np.random.default_rng()))
        pairs.append(pair)
        st.session_state["auc_shown"] = pair

    def pick_wrong_pair():
        st.session_state["auc_shown"] = list(metrics.misordered_pair(p1, y, np.random.default_rng()))

    with st.container(horizontal=True):
        # The label changes after the first pick, so the key keeps the button's identity stable.
        label = "Pick another pair" if pairs else "Pick a random pair"
        st.button(label, type="primary", icon=":material/casino:", key="auc_pick", on_click=pick_pair)
        if pairs:
            st.button("Show me one it gets wrong", icon=":material/help:", key="auc_wrong", on_click=pick_wrong_pair)
    shown = st.session_state.get("auc_shown")

    # Nothing to look at until a pair is picked: an empty chart only invites clicking on it.
    if shown:
        i, j = shown
        left, right = st.columns([0.4, 0.6], gap="large")
        with left:
            with st.container(border=True):
                c1, c2 = st.columns(2)
                c1.metric("Was readmitted: predicted risk", f"{p1[i]:.1%}")
                c2.metric("Wasn't readmitted: predicted risk", f"{p1[j]:.1%}")
                if p1[i] > p1[j]:
                    st.markdown(":green[:material/check_circle:] **Right way round.** The patient who was readmitted had the higher risk.")
                elif p1[i] < p1[j]:
                    st.markdown(":red[:material/cancel:] **Wrong way round.** The patient who wasn't readmitted had the higher risk.")
                else:
                    st.markdown("**A tie.** Both patients had the same risk, which counts as half right.")
            right_way = sum(p1[a] > p1[b] for a, b in pairs)
            st.markdown(f"Right way round in **{right_way} of {len(pairs)}** pairs you've picked.")
            if shown not in pairs:
                st.caption(
                    f"This pair was picked *because* the model gets it wrong, so it isn't in your count. "
                    f"Pairs like this exist, but for v1 they're rare: about {1 - v1['auc_test']:.0%} of all pairs."
                )
        with right:
            st.plotly_chart(charts.risk_strip(p1, y, pair=shown), width="stretch")
            st.caption(
                "Each dot is one of the test patients, placed by the risk ReadmitRisk v1 gave them. "
                "Your pair is the two large amber dots, joined by a dotted line: it is the right way round when "
                "the top one is further right. To pick a new pair, use the button above; clicking the chart does nothing."
            )

    if pairs:
        with st.container(border=True):
            st.metric(
                f"Across every possible pair ({metrics.n_pairs(y):,} of them), v1 puts the readmitted patient higher",
                f"{v1['auc_test']:.0%} of the time",
            )
            st.markdown(
                f"**That is what AUC {v1['auc_test']:.2f} means.** An AUC of 0.5 is no better than tossing a coin, "
                "and 1.0 means every pair is the right way round."
            )

        if st.session_state.get("auc_check"):
            st.session_state.setdefault("auc_check_widget", st.session_state["auc_check"])
        check = st.radio(
            "Quick check: another model has an AUC of 0.5. What does that tell you?",
            AUC_CHECK,
            index=None,
            key="auc_check_widget",
        )
        if check:
            st.session_state["auc_check"] = check
        ui.factual_check(
            check,
            AUC_CHECK[2],
            "AUC isn't a percentage of patients got right, or of readmissions found. It only says how often the model "
            "puts a readmitted patient above one who wasn't. At 0.5, that ordering is no better than chance.",
        )
        st.markdown(
            "AUC scores how well the model **orders** patients, and by that measure v1 is close to perfect. "
            "Before you trust that, the next stage looks at what the model is relying on."
        )

    # Moving on needs the guess (above) and at least one pair, so AUC isn't skipped.
    ui.next_stage(
        "app_pages/too_good.py",
        "2. Issues: Too good to be true?",
        bool(pairs),
        "Pick at least one pair above, and a button to the next stage will appear here.",
    )
else:
    st.caption("Choose your group's guess above to carry on.")
ui.synthetic_notice()
