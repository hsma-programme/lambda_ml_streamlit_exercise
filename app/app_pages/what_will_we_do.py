import streamlit as st

import charts
import interventions as iv
import ui

ui.stage_header(
    "3. What will we do with it?",
    "A list of patients is only useful if someone acts on it. What we do with the list changes everything "
    "about how it should be governed.",
)
ui.task_box(
    "For each proposed use of the list, answer three **separate** questions: would we support it, what harms "
    "should we investigate, and does it need medical-device assessment? Record your answers, then compare them "
    "with the considerations."
)

st.info(
    "**This stage won't mark you right or wrong.** These are judgement calls, and it's not wrong or unusual "
    "for groups to disagree. Record what your group thinks first, then use the considerations to test your reasoning "
    "and to see what you might have missed."
)

st.caption(
    "'Clinician' here means any registered health professional involved in a patient's care, such as a nurse, "
    "doctor, pharmacist or therapist."
)

st.markdown(
    "**The model's output is a ranked list of patients.** Phoning the people on it is the use that the analysts "
    "were originally asked to build the model for, but now that it's ready, there are conversations happening "
    "about other ways it could be used to have the most positive impact on readmission rates. "
    "Each of the uses below is a different action, with a different purpose, so it raises different questions."
)
st.caption(
    "A useful tool can still raise fairness concerns, and a tool that is not a medical device still needs "
    "governance. That is why these are three questions, not one."
)

records = st.session_state.setdefault("interventions", {})


def render(item: dict) -> None:
    key = item["key"]
    with st.container(border=True):
        st.subheader(item["title"])
        st.markdown(item["what"])
        rec = records.get(key)

        if rec is None:
            support = st.radio(
                "1. Would we support this use?", iv.SUPPORT_OPTIONS, index=None, key=f"sup_{key}"
            )
            harms = st.multiselect(
                "2. Which harms or fairness issues would we want to investigate?",
                iv.HARM_OPTIONS,
                key=f"harm_{key}",
                help="Choose as many as apply.",
            )
            device = st.radio(
                "3. Is the software likely to be a medical device in this use?",
                iv.DEVICE_OPTIONS,
                index=None,
                key=f"dev_{key}",
            )
            ready = support is not None and device is not None
            if st.button("Record our answers", key=f"rec_{key}", disabled=not ready, type="primary"):
                records[key] = {"support": support, "harms": harms, "device": device}
                st.rerun()
            return

        st.success("Recorded.")
        c1, c2, c3 = st.columns(3)
        c1.markdown(f"**Support?**\n\n{rec['support']}")
        c2.markdown("**Harms to investigate**\n\n" + ("\n".join(f"- {h}" for h in rec["harms"]) or "None chosen"))
        c3.markdown(f"**Medical device?**\n\n{rec['device']}")

        st.markdown("**Considerations**")
        st.markdown(f"- **Medical device ({item['device_lean'].lower()}):** {item['device']}")
        st.markdown(f"- **Harms and fairness:** {item['harms']}")
        st.markdown(f"- **Does it help?** {item['support']}")
        if item.get("timing"):
            st.markdown(f"- **When is the prediction made?** {item['timing']}")
        st.caption(
            "These are a reading of the slides' framework for a readmission use, not a regulatory ruling. "
            "Regulation changes, so check current MHRA guidance and ask your Clinical Safety Officer."
        )

        if key == "friday":
            render_friday()

        if st.button("Change our answers", key=f"chg_{key}"):
            del records[key]
            st.rerun()


def render_friday() -> None:
    f = ui.load_friday()
    st.markdown("**What the data shows**")
    st.plotly_chart(charts.friday_bars(f), width="stretch")
    st.markdown(
        f"- **Overall**, Friday discharges are readmitted more often: **{f['friday']['rate']:.1%}** against "
        f"**{f['other_days']['rate']:.1%}**.\n"
        f"- But **{f['share_of_friday_discharges_elderly_care']:.0%}** of Friday discharges come from elderly care "
        f"wards, against **{f['share_of_other_day_discharges_elderly_care']:.0%}** on other days. Those patients "
        "are older and frailer, and more likely to be readmitted whatever day they leave.\n"
        f"- **Within** elderly care wards, Friday and other days are about the same "
        f"({f['elderly_care']['friday']['rate']:.1%} vs {f['elderly_care']['other_days']['rate']:.1%}), and so "
        f"are all other wards ({f['other_wards']['friday']['rate']:.1%} vs {f['other_wards']['other_days']['rate']:.1%})."
    )
    st.info(
        "A prediction, or an association, is not the effect of an action. Friday looks risky because of *who* is "
        "discharged on Fridays. Banning Friday discharges would not change who the patients are. "
        "Always check yourself before making a causal claim from a non-causal pattern."
    )
    st.caption(
        "Synthetic data. Small differences within groups are sampling noise, and these figures cannot prove "
        "that a ban would have no effect, only that this pattern gives no reason to expect a benefit."
    )
    with st.expander("Show these rates as a table"):
        st.dataframe(
            {
                "Group": ["All patients", "Elderly care wards", "All other wards"],
                "Friday": [
                    f"{f['friday']['rate']:.1%}",
                    f"{f['elderly_care']['friday']['rate']:.1%}",
                    f"{f['other_wards']['friday']['rate']:.1%}",
                ],
                "Other days": [
                    f"{f['other_days']['rate']:.1%}",
                    f"{f['elderly_care']['other_days']['rate']:.1%}",
                    f"{f['other_wards']['other_days']['rate']:.1%}",
                ],
            },
            hide_index=True,
            width="stretch",
        )


compulsory = [i for i in iv.INTERVENTIONS if i["compulsory"]]
optional = [i for i in iv.INTERVENTIONS if not i["compulsory"]]

done = sum(1 for i in compulsory if i["key"] in records)
st.progress(done / len(compulsory), text=f"{done} of {len(compulsory)} compulsory uses recorded")

for item in compulsory:
    render(item)

with st.expander(f"More uses to consider (optional, {len(optional)})"):
    st.caption("Do these if your group has time, or pick the ones you disagree about most.")
    for item in optional:
        render(item)

st.divider()
st.subheader("Because we built it ourselves")
st.markdown(
    "When a model is bought, the supplier carries the manufacturer's responsibilities. Here **we** are the "
    "manufacturer. If the model is used in the delivery of care, clinical safety standards are likely to apply "
    "to us as the builder (**DCB0129**) and as the organisation deploying it (**DCB0160**). Both expect a "
    "named **Clinical Safety Officer**, a hazard log and a safety case."
)
with st.expander("In-house models and the Health Institution Exemption"):
    st.markdown(
        "Software built and used within a health institution may be covered by an exemption from some "
        "medical-device requirements, **only if** it is not transferred to another organisation, is used on "
        "the same premises, follows leading practice, and has a designated responsible officer. "
        "Treat this as something to check with your Clinical Safety Officer and current guidance, not as a way "
        "round assessment."
    )

st.markdown(
    "**Watch for drift.** Each answer above describes a use *as designed*. In practice a list that is easy to "
    "act on tends to get used for more over time. If the use changes, the assessment has to be revisited: a "
    "documented intended purpose, and someone accountable for noticing when it is being stretched, are part of "
    "the safeguard."
)

st.markdown(
    "**Discuss:** which use would you be most comfortable going ahead with first, and what would you need to "
    "see before you allowed a use that guides individual clinical care?"
)
ui.synthetic_notice()
