# Plan: Order count per status for the support lead

References: intent.md (gate 1 passed, Risk: low), spec.md (gate 2 passed). No ux-brief.md (no screen).

## Data shape
One fresh, insertion-ordered `dict[label_or_raw_code, int]`, built in two steps from data that already exists:

1. **Seed** from `STATUS_LABELS` (`app/orders.py:8-15`): `{label: 0 for label in STATUS_LABELS.values()}`.
   Every label is present with 0 before any order is read, so R3, E1 and E2 cannot be missed, and the
   labels come out in `STATUS_LABELS` order (R5, first half) for free.
2. **Tally** with `collections.Counter(status_label(o["status"]) for o in _ORDERS.values())`.
   Keying through the existing `status_label` (`app/orders.py:71-73`) is the single rule for every key:
   known code → label (R2), unlabelled code → raw code (R4, E3, E4, E5), raw code equal to a label's text →
   merged under that label (E6, spec Decision 2). There is no separate branch per case.

The result is `seed` updated with the tally, then the leftover keys (those not in the seed, i.e. raw codes)
appended in a fixed sort order. Values are only `int`; keys are only what `status_label` returns, so no
customer id, order id or item can reach the result (R6). The dict is built new on each call from plain
values, so editing it never touches `_ORDERS` or `_HISTORY` (R7). Every order adds exactly 1 to exactly one
key, so the sum equals `len(_ORDERS)` (R8).

Sort key for leftover raw codes (spec Flagged concern 2: mixed key types must not fail):
`key=lambda k: (not isinstance(k, str), str(k))` — string codes first in normal string order, then any
non-string values (e.g. `None`, `3`) ordered by their text. This never compares a `str` with `None`.

Public shape: `status_counts() -> dict` in `app/orders.py`, no arguments (R9: one call).

## Throughput checkpoint
- Blocking first steps: failing tests in `tests/test_status_report.py` for R1-R8 and E1-E8, checked with `make strength`, committed, then tests locked.
- Independent workstreams: n/a: the whole change is one function of about 10 lines in one file.
- Shared mutable state: `_ORDERS` and `_HISTORY` in `app/orders.py` are module globals; the new tests change them through `set_status` and must save and restore them in `setUp`, as `tests/test_order_history.py:22-40` does (spec Flagged concern 4).
- Smallest safe decomposition: unit 1 seed plus tally (R1-R3, R6-R8, E1, E2, E7, E8) ending in `make test`; unit 2 raw-code ordering and mixed types (R4, R5, E3-E6) ending in `make test`, then `make check`.

## Parallel parts
none: one new function in one code file and one new test file; splitting would add coordination with no time saved.

## Files to change
| File | What changes | Requirement |
|---|---|---|
| tests/test_status_report.py (new) | Failing tests for R1-R8 and E1-E8, with save/restore of `_ORDERS` and `_HISTORY` in `setUp` | R1-R8 |
| app/orders.py | Add `status_counts()` after `status_label`; add `from collections import Counter`. No existing function changes. | R1-R9 |

## Order of work
1. Write failing tests from spec.md R1-R8 and E1-E8 in `tests/test_status_report.py` (`/superdev:test-first`).
   Note: `.pod/lock-tests` exists now (left from change 001); the test-first skill handles removing and re-creating it, not the build.
   Tests to include: demo data exact result and key order; zero labels present; `set_status("A1001", "on_hold")` gives `on_hold: 1`, `Shipped: 0`;
   key order with two raw codes; `""`, `None` and an int status do not raise and appear under their raw value; status `"Paid"` merges with `paid`;
   empty `_ORDERS` gives all labels at 0; every value is `int` and no `customer_id`/order id/item appears; stores unchanged after call and after editing the result; sum equals `len(_ORDERS)`; second call after a status change reflects only the current status.
   Run `make strength`, then commit.
2. Lock the tests (`touch .pod/lock-tests`).
3. Unit 1: add `status_counts()` with seed and tally, leftover keys appended unsorted. `make test` — the R1-R3, R6-R8 tests pass; commit `feat(002)`.
4. Unit 2: sort leftover raw codes with the mixed-type key. `make test` passes in full; commit `feat(002)`.
5. `make check` (tests, strength, CODEOWNERS, gate-check) passes.
6. Prepare the R9 demo for gate 4: `python3 -c "from app.orders import status_counts; print(status_counts())"` and its output in acceptance.md.

## Risks
- Tests leaking state into other tests through `_ORDERS`/`_HISTORY`. Reduce: `setUp` deep-copies and `addCleanup` restores both, copying the pattern in `tests/test_order_history.py:22-40`; run the full suite, not just the new file.
- Sorting mixed key types (`str`, `None`, `int`) raising `TypeError`. Reduce: the sort key above never compares unlike types; tests cover `None` and an int status together with a string raw code.
- Unhashable status values (e.g. a list) make `status_label` itself raise `TypeError`, because it does a dict lookup. The spec (E5) covers `None` and non-string values but did not name unhashable ones. This plan does not handle them: no such data exists, the existing customer-facing functions fail the same way, and validating `set_status` is a separate change (spec Decision 1). See Open questions.
- Accidental change to customer-facing behavior. Reduce: no existing function is edited; existing tests `tests/test_orders.py` and `tests/test_order_history.py` must keep passing unchanged.
- Risk tier: `app/orders.py` and `tests/` do not match `docs/risk-paths`; the change stays Risk: low.

## Proof
- `make test` and `make strength` pass; `make check` passes.
- R1: test on demo data expects exactly `Awaiting payment: 1, Paid: 0, Preparing order: 0, Shipped: 1, Delivered: 1, Cancelled: 1`, and a test that adds history via `set_status` and changes back shows only current status is counted (E8).
- R2: test that `pending` is reported as "Awaiting payment" and no key `pending` exists.
- R3 / E1 / E2: test that all six labels are present with 0 when `_ORDERS` is empty and that `Paid` and `Preparing order` are 0 on demo data.
- R4 / E3: test with `set_status("A1001", "on_hold")` expects `on_hold: 1` and `Shipped: 0`.
- R5: test on `list(result)` equals the six labels in `STATUS_LABELS` order followed by raw codes in sorted order.
- E4 / E5: tests that `""`, `None` and an int status do not raise and are counted under that raw value.
- E6: test that status `"Paid"` and `paid` give `Paid: 2` and no extra key.
- R6 / E7: test that every value is an `int`, every key is a label or a current raw status, and no customer id, order id or item text appears.
- R7: test comparing deep copies of `_ORDERS` and `_HISTORY` before and after the call and after mutating the result.
- R8: test that `sum(result.values()) == len(_ORDERS)` on demo data and after status changes.
- R9: gate 4 demo of one call and its output in acceptance.md; the time is self-reported by the support lead for 5 working days after release (intent.md PO answer 2).

## Rollback
- `git revert <merge commit of 002>` removes `status_counts()` and its tests. Nothing is stored and nothing else calls the function, so there is no data to restore.
- Check afterwards: `make check` passes and `tests/test_orders.py` / `tests/test_order_history.py` are unchanged and green.

## Open questions
- Unhashable status values (list, dict) would raise from `status_label` before counting. Accept as out of scope (with the `set_status` validation change), or should `status_counts()` guard against them in this change?

## Summary for SuperBiz
1. We will add one way for the support lead to get, in a single step, how many orders are in each status, including statuses with none.
2. Customers see no change; the support lead gets the morning count without counting by hand, and odd status values show up under their own name instead of being hidden.
3. Low risk: it only reads order data and stores nothing; it can be removed in minutes, and one rare kind of broken status value is not handled yet (listed under Open questions).
