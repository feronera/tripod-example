# Intent: Order status history for customers

Status: draft

## Problem
Customers checking their orders see only the current status, not when it changed. They contact support to ask
what happened to their order.

Evidence: `logs/sample-app.log` records one day (2026-03-02) with 4 support chats on the topic "Order status not showing"
(`support.ticket ... count_today=4`). The support tool weekly report shows 28 "where is my order" plus
"order status not showing" chats per week (last 4 weeks average; demo data).

## Users
- Customers checking their own orders.
- Out of scope: support staff.

## Success measure
"Where is my order" plus "order status not showing" chats per week, from the support tool weekly report.
- Current: 28 per week (last 4 weeks average; demo data).
- Target: 14 per week within 30 days after release.

## Risk
Risk: high

1. Law or regulation: no. The PO confirmed no regulation is involved.
2. Customers see the result directly: yes. The history is shown to customers.
3. Rollback within minutes without data loss: no. Reverting removes the feature and the status history recorded
   since release. The PO accepts this loss because nothing else uses the history, but the data is still lost,
   so the criteria in `docs/risk-tiers.md` put this change at high.
4. Personal or sensitive data: no by the PO's answer. The data is the customer's own order status history,
   with no payment or personal fields.

## Constraints
- Python standard library only.
- A customer must never see another customer's order.
- Reuse the existing data in `app/orders.py`.
- History starts at release. No backfill of past status changes.
- Show the status label and the date/time of each change in Asia/Bangkok time.
- Out of scope: the `delivery_date is None` error in `logs/sample-app.log`. It is a separate bug.

## Open questions
- Risk tier: question 3 is "no" because history is lost on revert, so this draft says high. Do SuperBiz and SuperDev
  agree, or can the rollback keep the recorded history (e.g. hide the feature and keep the data) so the change
  qualifies as medium? If the tier changes after gate 1, gate 1 must be signed again.
- Question 4: is a status history linked to a customer ID treated as personal data under the team's data policy?
  The PO says no personal fields are involved; SuperDev should confirm when checking the data shape.
- Evidence overlap: in `logs/sample-app.log`, the 4 "Order status not showing" chats come on the same morning as
  5 `orders.status` errors (`TypeError: delivery_date is None`) for 3 customers. Some of these chats may be caused by
  that bug, not by the missing history. How much of the 28 per week does this change address, and is the target of 14
  still realistic if the bug is fixed separately?
- The current value of 28 per week is demo data. What is the real value from the support tool, and who pulls the
  weekly report 30 days after release?
- How will the support tool tell "where is my order" chats apart from other order chats, so the measure is counted
  the same way before and after release?
- If the tier stays high, the escalation signer at gates 2 and 4 is Lee (`pod.yml`). Is Lee available for this change?
  Note that `pod.yml` gives the escalation and SuperBiz the same GitHub login, so a PR approval may not show two
  different people.
