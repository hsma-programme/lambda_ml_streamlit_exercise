# Ongoing questions

Open design questions that haven't been settled. Add new items at the top, and move an item to "Resolved" with the decision when it is settled.

## Open

### Does the Stage 4 closing discussion prompt work as written?

**Where:** this was the closing "Discuss" prompt on [app/app_pages/bringing_people.py](app/app_pages/bringing_people.py). On 2026-10-14 all the stage-page discussion prompts were moved to an "Extension" expander at the end of the sign-off page (`DISCUSSION` in `app/ui.py`), so this is now an optional extension rather than part of the main route. The prompt:

> What is the most useful question a sceptical consultant could ask about this model, and what evidence would you want before answering it?

**The uncertainty:** it is not yet clear that this works for the audience (senior NHS leaders with no ML background, at the end of a long session). It asks learners to generate a question from scratch *and* say what evidence would answer it, which is probably the hardest kind of task in the exercise. Some groups may produce one generic question and stall. It hasn't been tried with anyone yet; a pilot with someone unfamiliar with ML would settle most of this.

**What we might expect groups to come up with** (not yet written into the facilitator page):

| Likely answer | What it is really asking | Evidence they might name |
|---|---|---|
| "Is it accurate?" or "How often is it wrong?" | Performance and uncertainty | Held-out results, how many calls would be wasted or missed |
| "Does it work for *our* patients?" | Local validation and calibration | Testing on our own recent discharges, checking that a "46%" really is about 46% |
| "Does phoning people actually reduce readmissions?" | Effect of the action, not just the prediction | A trial against usual care, or random allocation of limited calls |
| "Is it fair? Who does it miss?" | Fairness across groups | Performance by age, deprivation and ethnicity, who is on and off the list |
| "Why is this patient flagged, and can I overrule it?" | Explanation and human judgement | The waterfall, a clear route for staff to disagree |
| "What happens when it's wrong, and who's accountable?" | Safety and governance | A named owner, a hazard log, monitoring, criteria for pausing |
| "Has anything leaked, and when does it run?" | Data and timing | A check of every input against the moment of prediction |

The first six threads come from the exercise itself; "has anything leaked" is Stage 2, and "does it actually help" is the effect-of-the-action thread from Stages 1 and 3.

**What groups will probably actually say:**
- The most common first answer is likely to be "Is it accurate?". That is a reasonable instinct but vague. A facilitator can push with "accurate for whom, measured how, compared with what?", which leads towards calibration, subgroups and a random-calling comparison.
- The most valuable answer, "how do we know the calls help?", is probably the least likely to appear unprompted: people tend to treat a good prediction as proof of a good service.
- Governance and accountability questions will probably come from the more senior people in the room.

**Options for changing it:**

1. **Keep the open prompt.** Best if the debrief is time-rich and the groups are confident. Rely on the facilitator page's table above to prompt and probe.
2. **Offer a shortlist** (suggested). Give six or seven candidate questions (the table above) and ask the group to pick the one a sceptical consultant would find most persuasive, and to say what evidence would settle it. Then ask "what would you add?". This keeps the conversation and makes the evidence step concrete.
3. **Split it in two.** First "what would you want to ask?", then, as a separate step with the shortlist revealed, "what evidence would answer it?".

**Related follow-ups:**
- Add the "what groups tend to say" table to the facilitator page when it is built (chunk 6).
- If the shortlist version is chosen, the candidate questions can be reused in the Stage 5 sign-off conditions (local validation, calibration, equity checks, intervention evaluation, accountable owner, monitoring).

## Resolved

_Nothing yet._
