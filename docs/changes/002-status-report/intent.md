# Intent: Order count per status for the support lead

Status: draft

## Problem
The support lead plans staffing each morning, but there is no quick way to see how many orders are in each status.
Today they count by hand from the order list, every working morning.
Evidence: the support lead's report that the manual count takes about 15 minutes a day (demo data, see Open questions).

## Users
- The support lead (internal) is the only user.
- Customers never see this report.

## Success measure
Time the support lead spends on the morning count per status:
from about 15 minutes a day (current, demo data) to under 1 minute a day, within 2 weeks of release.

## Risk
Risk: low

1. Law or regulation: no. No regulation applies.
2. Seen directly by customers or external users: no. It is an internal report for the support lead.
3. Rolled back within minutes without data loss: yes. It is a read-only function and stores nothing.
4. Personal or sensitive data: no. The output is counts per status only, with no customer ids or names.

Questions 1, 2 and 4 are "no" and question 3 is "yes", so the tier is low.

## Constraints
- Python standard library only; no new dependencies.
- Read-only over the existing order data in `app/orders.py`; no writes and nothing stored.
- Return a count for each status label, including statuses that have zero orders.
- No customer identifiers (ids, names) in the output.

## Open questions
- The current value (about 15 minutes a day) comes from demo data. Is that figure acceptable as the baseline for gate 1, or should it be confirmed with the support lead?
- How will the "under 1 minute" target be measured after release (self-report by the support lead, or a timed check)?
- The order data may contain a status code that has no label in `STATUS_LABELS`. Should it be counted under its raw code, grouped as "other", or left out?

## PO answers (before gate 1)
1. Use 15 minutes as the starting value; it is demo data, and the support lead will confirm it in the first week.
2. The support lead reports the time for 5 working days after release.
3. Count unlabelled codes under the raw code, the same way the order page shows them.
