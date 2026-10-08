blockers: 0
majors_open: 1
second_opinion: agree
reviewed_head: 4f72765a87d0b7229584a5369e6852c577014bc7

# Review: 001 order status history

The first 4 lines are a header read by `scripts/auto-merge-check.sh`. Do not rename the keys.
`second_opinion: agree` means reviewer-second found no Blocker that the main reviewer missed and does not dispute the "no Blocker" result.

Reviewed: `git diff main...HEAD` (app/orders.py, app/timefmt.py, tests/test_order_history.py) with three lenses
(security, correctness, tests and edge cases), then reviewer-second.

## Blocker
- none. R1–R8 each map to code and tests (R1 orders.py:25-60, R2/R3 orders.py:92-101, R4 orders.py:103-113,
  R5 orders.py:73, R6 timefmt.py, R7 unchanged functions + tests/test_orders.py, R8 fresh dicts + immutable `StatusUpdate`).
  Missing, other-customer and malformed ids all raise the same `OrderNotFound("Order not found")`. No personal data,
  standard library only. Locked tests unchanged since f5a54ca (`git diff f5a54ca HEAD -- tests/` is empty).

## Major
- docs/changes/001-order-history/ E13–E18 (and R9–R13) have no automated test (checklist: edge case without a test).
  Not fixed: this repo has no web layer, and spec.md decision 3 / plan.md "Proof" assign them to a page demo.
  `acceptance.md` does not exist yet, so nothing proves them today. Human decision needed: accept demo-only proof
  and record the E13–E18 demo in acceptance.md before gate 4.

## Minor
- app/orders.py:54-56 `set_status` accepts any `status` (None, "", list). An unhashable status makes
  `status_label` (orders.py:73) raise `TypeError` for the owner's reads; a mutable one is returned by reference in
  `history[*].status`. Only internal callers today. Question: reject non-`str`/empty status before any write?
- app/orders.py:47 `set_status` with an unhashable `order_id` raises `TypeError`, not `OrderNotFound` as plan.md's
  validation table says. Nothing is stored, so E9 still holds.
- app/orders.py:52 `at` that is not a datetime raises `AttributeError`, not `ValueError`. Nothing is stored.
- app/orders.py:49, 84, 100 `"Order not found"` is written three times; a module constant would keep the
  not-found message identical (protects E2 against future rewording).
- app/orders.py:52 the `at.utcoffset() is None` branch (tzinfo set, offset None) has no test; tests are locked.
- tests/test_order_history.py:124-128 `test_r3_own_order_returns_history` checks only `order_id`/`status`;
  `history`/`updated` are covered by R4/E4 tests. Locked, noted only.
- tests/test_order_history.py:24-40 state isolation uses deepcopy + cleanup rather than `patch.dict` named in
  plan.md Risks; same effect. The `getattr(..., "_HISTORY", None)` fallback is now dead code. Locked, noted only.
- orders.py:92-101 / R10: ownership is only as strong as the caller's `customer_id`, and `set_status` has no caller
  check. The R10 demo should show the id comes from the verified session and no route calls `set_status`.

## Second opinion (reviewer-second)
- verdict: no-blocker, agrees with the "no Blocker" result. It raised the same Minors (status/order_id/at type
  guards, test isolation style) and treats E13–E18 as demo-scoped by spec decision 3, pending acceptance.md.

## Checks
- `make check`: not run as one command (the non-interactive session was refused permission for `make check`).
  Parts run separately: unit tests `python3 -m unittest discover -s tests -t .` → 136 tests OK;
  `scripts/gate-check.sh --all` → OK (passed up to gate 3, Risk: high).
  `scripts/sync-codeowners.sh --check` was not run (permission refused). SuperDev must run `make check` before gate 4.
- `scripts/test-strength.sh`: not run (permission refused). All three lenses and reviewer-second read the tests and
  found that each asserts concrete values and would fail if every function returned None. This is not verified by running it.
