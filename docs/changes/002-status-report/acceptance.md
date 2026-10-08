# Acceptance: Order count per status for the support lead

References: intent.md (Success measure), PR: #5 (auto-merged to main as 398334b, low risk; `role=auto` line in gates.log)

This is acceptance after merge. The change is already on main.

## What changed (for non-developers)
- The support lead can now get the number of orders in each status with one command, instead of counting by hand.
- Every status appears, even ones with 0 orders. An order with an unknown status shows up under its own name, so nothing is hidden.
- The report shows only status names and numbers: no customer names, customer ids or order ids.
- It only reads data. It stores nothing and changes nothing, and customers see no change.
- Files in the merge (398334b): `app/orders.py` (+19 lines, a new `status_counts()` function), a new test file
  `tests/test_status_report.py`, and this change's documents. No other code or config file is in the merge.

## Success measure check
| Success measure | How measured | Result | Pass? |
|---|---|---|---|
| Morning count per status: from about 15 min/day (demo baseline) to under 1 min/day, within 2 weeks of release | Now: the count is available from one call (spec R9, demo step 1). After release: the support lead self-reports the time for 5 working days (intent.md PO answer 2) | One call returns the full count per status (step 1). The time in real use is not measured yet | Pending: can only be measured after release |
| Baseline of about 15 min/day is real | The support lead confirms it in the first week after release (intent.md PO answer 1) | Not confirmed yet; demo data | Pending |

The time target can be measured only after release. Measurement: the support lead reports minutes spent on the
morning count for 5 working days after release. Release date and report dates are not recorded in the change
documents; see Open questions.

## Demo steps
Run on branch `accept/002` (same content as main at 398334b), on 2026-10-09, with the demo order data.

1. Get the morning count with one call (the R9 demo from plan.md step 6 and review.md):
   `python3 -c "from app.orders import status_counts; print(status_counts())"`
   - Expected result: `Awaiting payment: 1, Paid: 0, Preparing order: 0, Shipped: 1, Delivered: 1, Cancelled: 1`, in that order (spec R1, R3, R5).
   - Actual result:
     ```
     {'Awaiting payment': 1, 'Paid': 0, 'Preparing order': 0, 'Shipped': 1, 'Delivered': 1, 'Cancelled': 1}
     ```
     Matches. Only status names and numbers appear (R6).
Steps 2 and 3 were run as one command:
`python3 -c "from app import orders; r = orders.status_counts(); print(sum(r.values()), len(orders._ORDERS), all(type(v) is int for v in r.values())); orders.set_status('A1001', 'on_hold'); print(orders.status_counts())"`

2. Check that the counts add up to the number of orders and that every value is a whole number (spec R8, R6).
   - Expected result: sum equals the number of orders; all values are whole numbers.
   - Actual result: `4 4 True`. Matches.
3. In the same run (in memory only, nothing saved), give order A1001 a status with no label and count again (spec R4, PO answer 3).
   - Expected result: `on_hold: 1` added after the labels, and `Shipped: 0`.
   - Actual result:
     ```
     {'Awaiting payment': 1, 'Paid': 0, 'Preparing order': 0, 'Shipped': 0, 'Delivered': 1, 'Cancelled': 1, 'on_hold': 1}
     ```
     Matches.

## Checks
- Gate 3: gates.log has `gate=3 role=owner` (dan) and `gate=3 role=cross` (bee). `scripts/gate-check.sh docs/changes/002-status-report 3`
  could not be run in this session (the command needed approval in a non-interactive run), so this is read from gates.log, not from the script.
- review.md Major 1 (pod.yml and README in the diff): the merge commit 398334b contains no `pod.yml` or `README.md`, which supports SuperDev's decision that it was a false positive.
- review.md Major 2 (a list or other unhashable status makes the call fail): accepted as out of scope by SuperDev, under spec Decision 1. No such data exists today. Not demonstrated here.

## Open questions
- Release date, and so the dates of the 5-day self-report and the 2-week deadline for the time target, are not recorded. SuperBiz to set them.
- Who records the support lead's 5-day report, and where (for example, a note added to this file).

## Decision
Decision (proposed, for SuperBiz to confirm): accept

Reason: all three demo steps gave exactly the expected output. One call returns a count for every status, in a fixed
order, including zero counts (step 1); the counts add up to the 4 demo orders and contain only numbers and status
names, with no customer data (step 2); an unknown status is shown under its own name, as PO answer 3 asked (step 3).
This proves the part of the Success measure that can be shown now (spec R9: the count takes one call). The time
target (under 1 minute a day) can be measured only after release, through the support lead's 5-day self-report.
If that report does not show under 1 minute a day within 2 weeks of release, SuperBiz should reopen this decision.
