"""Candidate uses of the readmission list, and the considerations shown after a group has decided.

These are discussion aids, not a regulatory determination. The device readings follow the
slides' framework (software is a device when intended to inform or carry out a medical
purpose; organising services vs guiding individual clinical care) applied to a readmission
use. Recheck against current MHRA guidance and the Clinical Safety Officer before delivery.
"""

SUPPORT_OPTIONS = [
    "Yes, we would support this",
    "Only with conditions",
    "No, we would not support this",
]

HARM_OPTIONS = [
    "Could widen health inequalities",
    "Could miss or under-serve some groups",
    "Could delay or deprioritise someone who needs care",
    "Adds worry or burden for patients",
    "Uses staff time that could help others",
    "N/A - We can't see a harm that needs investigating",
]

DEVICE_OPTIONS = [
    "Probably a medical device, so it needs assessment",
    "Probably not, but we would check with our Clinical Safety Officer",
    "Not sure, we would need to find out",
]

INTERVENTIONS = [
    {
        "key": "phone_call",
        "title": "A support phone call",
        "compulsory": True,
        "what": (
            "A member of the community discharge team phones each flagged patient within two working days "
            "of discharge, to check how they are coping and arrange any support they ask for. "
            "The software only produces the list, prioritising those flagged by the model as being at highest "
            "risk of being readmitted, based on the likelihood threshold we choose."
        ),
        "device_lean": "It depends on the intended purpose",
        "device": (
            "If the software only produces a list for a team to contact, that is organising a service, and it is "
            "less likely to be a medical device. If the score is used to decide *clinical* matters for an individual "
            "patient (for example, who gets assessed for deterioration), the picture changes. Calling it 'not for "
            "clinical use' does not get round the definition: what counts is the intended purpose."
        ),
        "harms": (
            "A list built from past use of services may under-represent people who use them less. Some patients "
            "may be hard to reach by phone. Calls to people who would have been fine cost time and may worry them."
        ),
        "support": (
            "Whether the calls *help* is a separate question from whether the model can rank patients. "
            "Ranking by risk can still beat calling at random, but you would want to test that, ideally against "
            "usual care or random allocation of limited calls."
        ),
    },
    {
        "key": "followup",
        "title": "A clinician brings forward follow-up, or reviews medication, for flagged patients",
        "compulsory": True,
        "what": (
            "For flagged patients, a clinician reviews the notes and may bring their follow-up appointment "
            "forward or review their medicines."
        ),
        "device_lean": "Likely a medical device",
        "device": (
            "Here the score is informing decisions about an individual patient's clinical care. That is guiding "
            "*clinical care*, not just *access* to a service, and it is the kind of use where medical-device "
            "regulation is likely to apply. Clinical safety standards (DCB0129 for whoever builds it, DCB0160 for "
            "the organisation deploying it) would also be expected, with a named Clinical Safety Officer, a hazard "
            "log and a safety case."
        ),
        "harms": (
            "Clinician time goes to flagged patients, possibly at the expense of others who are just as unwell "
            "but less visible to the model. If the model under-predicts for some groups, they are overlooked."
        ),
        "support": (
            "A prediction says who is likely to be readmitted, not who would *benefit* from earlier follow-up. "
            "Some flagged patients may be beyond help from this action, and others may need nothing."
        ),
        "timing": (
            "Arranging an earlier appointment or a medicines review takes time. We could build the model to make "
            "its prediction earlier, for example the day before discharge, so the flag arrives while there is still "
            "time to act."
        ),
    },
    {
        "key": "friday",
        "title": "Ban Friday discharges",
        "compulsory": False,
        "what": "Stop discharging patients on Fridays, because Friday discharges are readmitted more often.",
        "device_lean": "Probably not on its own",
        "device": (
            "A change to a service policy is not software informing an individual's care. The question is whether "
            "the *action* would help, which is a causal question, not a regulatory one."
        ),
        "harms": (
            "Longer stays and bed pressure, delays for patients who are ready to go, and a knock-on for weekend "
            "staffing. These are real costs, so the policy needs evidence of benefit."
        ),
        "support": (
            "A prediction or an association is not the effect of an action. Look at where Friday discharges come from "
            "before deciding."
        ),
    },
    {
        "key": "transport",
        "title": "Transport support to follow-up appointments",
        "compulsory": False,
        "what": "Offer flagged patients free transport so they can get to their follow-up appointment.",
        "device_lean": "Probably not a medical device",
        "device": (
            "Changing *access* to a service (such as transport) is more likely to be organising services than "
            "guiding clinical care, so it is probably not a device. It is still a **fairness** question."
        ),
        "harms": (
            "Who is offered transport, and does the offer reach people in more deprived areas? It could narrow "
            "inequalities or widen them, depending on who the list captures."
        ),
        "support": "Does transport actually remove the barrier for the people on the list?",
        "timing": (
            "Transport has to be booked in advance, so a flag raised as the patient leaves may be too late. "
            "We could build the model to predict the day before discharge instead."
        ),
    },
    {
        "key": "pharmacy",
        "title": "A pharmacist medicines review for flagged patients",
        "compulsory": False,
        "what": "Offer flagged patients a pharmacist review of their medicines shortly after discharge.",
        "device_lean": "Likely a medical device if the score drives who gets the review",
        "device": (
            "A medicines review is clinical care. If the score decides which individual patients get one, it is "
            "informing clinical care, which makes a device assessment more likely. A review offered to everyone "
            "in a group (with no individual score) is different."
        ),
        "harms": (
            "Pharmacist time is limited. Patients who aren't flagged may be just as much in need of a review."
        ),
        "support": "Is there evidence that a review lowers readmission for the kind of patients on the list?",
        "timing": (
            "A review before the patient leaves needs the flag earlier than the moment of discharge. We could "
            "build the model to predict the day before discharge, using only what is known by then."
        ),
    },
    {
        "key": "delay_discharge",
        "title": "Delay discharge for high-risk patients",
        "compulsory": True,
        "what": "Keep patients with a high predicted risk in hospital for longer before they go home.",
        "device_lean": "Likely a medical device",
        "device": (
            "This directly drives a clinical decision about an individual patient, so a device assessment is likely "
            "to be needed, along with clinical safety management."
        ),
        "harms": (
            "More bed days, deconditioning and infection risk from staying longer, and distress for patients and "
            "families. The model says who is *likely* to return, not that staying longer would stop it."
        ),
        "support": "A use like this would need strong evidence that it prevents harm before it could be justified.",
        "timing": (
            "To change *when* someone goes home, the prediction has to exist before the discharge decision. "
            "The model as built is run as the patient leaves, which is too late. We could rebuild it to predict "
            "the day before discharge. It could then only use what is known by then (just as Stage 2 showed that "
            "the moment the model is run decides what counts), so it would need to be re-tested, and "
            "performance is likely to be lower."
        ),
    },
    {
        "key": "deprioritise",
        "title": "Deprioritise 'frequent readmitters' for planned operations",
        "compulsory": False,
        "what": "Move patients with a high predicted readmission risk down waiting lists for planned (elective) care.",
        "device_lean": "Likely a medical device, and a serious fairness concern",
        "device": (
            "Prioritising individual patients' access to care on the basis of a predicted clinical outcome is guiding "
            "clinical care, so device regulation is likely to apply."
        ),
        "harms": (
            "This penalises the people with the greatest need, who are also more likely to be from deprived "
            "groups. A high readmission risk does not mean a patient would benefit less from the operation. "
            "Fairness and non-discrimination are legal obligations, not just good practice."
        ),
        "support": "This use is very hard to justify: weigh the fairness points above against any benefit you can name.",
    },
]

BY_KEY = {i["key"]: i for i in INTERVENTIONS}
