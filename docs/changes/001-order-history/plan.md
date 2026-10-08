# Plan: Order status history for customers

References: intent.md, spec.md, ux-brief.md

Scope follows the decisions at the end of spec.md: one write path `set_status`, in-memory history for the process
lifetime, the function-level API `status_history(customer_id, order_id)` as the deliverable, a fixed +07:00 offset,
`status_for_customer` unchanged, and R9–R13 proven by demo (no web layer in this repo).

## Data shape
1. **One update is an immutable record**, in `app/orders.py`:
   ```python
   class StatusUpdate(NamedTuple):   # typing.NamedTuple, standard library
       order_id: str
       status: str
       at: datetime                  # always aware, normalized to UTC when stored
   ```
   Exactly three fields (R1: "and nothing else"; no customer id, no personal fields, spec concern 12). Being a tuple,
   a stored update cannot be edited in place.
2. **History store is an append-only table keyed by order id**: `_HISTORY: dict[str, list[StatusUpdate]] = {}`.
   - Starts empty for every order (R2, no backfill). An order with no key has no history.
   - List order is record order. "Newest first" is `reversed(list)`, never a sort by time, so two updates with the
     same timestamp keep the later-recorded one first (E10) without any tie-break logic.
3. **The only writer is `set_status(order_id, status, at=None)`**. It updates `_ORDERS` and `_HISTORY` together, so the
   rule "the newest update's status is the current status" holds by construction. It replaces the order dict
   (`_ORDERS[order_id] = {**order, "status": status}`) rather than mutating it, so `get_order` copies stay valid and tests
   can restore state with `unittest.mock.patch.dict`.
   Validation happens before any write, so a rejected call stores nothing (E9):
   | Input | Result |
   |---|---|
   | order id not in `_ORDERS` | raise `OrderNotFound`, nothing stored |
   | `at` naive (`at.tzinfo is None` or `utcoffset() is None`) | raise `ValueError`, nothing stored |
   | `at` is None | server clock, `datetime.now(timezone.utc)` (spec concern 7) |
   | `status` equal to the current code | return `False`, nothing stored (E7) |
   | any other code, including one with no label | store, return `True` (E8) |
4. **Bangkok time is a value, not logic spread around**, in a new pure module `app/timefmt.py`:
   ```python
   BANGKOK = timezone(timedelta(hours=7), "Asia/Bangkok")    # no DST, no zoneinfo data needed (decision 7)
   _MONTHS = ("Jan", "Feb", ..., "Dec")                       # fixed English names, not locale-dependent %b
   def time_view(at) -> {"text": "10 Oct 2026, 01:30", "iso": "2026-10-10T01:30:00+07:00"}
   ```
   `text` is `f"{t.day} {_MONTHS[t.month - 1]} {t.year}, {t:%H:%M}"` (no leading zero on the day, 24-hour clock);
   `iso` is `t.isoformat(timespec="seconds")` on the Bangkok-converted time (R6, E11).
5. **Read model returned by `status_history(customer_id, order_id)`** is built fresh on every call from plain dicts,
   lists and strings, so callers can never reach stored records (R8):
   ```python
   {
     "order_id": "A1001",
     "status": "delivered", "label": "Delivered",
     "updated": {"text": ..., "iso": ...} | None,   # time of the current status if recorded, else None (R4, E3, E4)
     "history": [ {"status": ..., "label": ..., "time": {"text": ..., "iso": ...}}, ... ]   # newest first
   }
   ```
   `updated` is the newest update's time when that update's status equals the current status, otherwise `None`.
   Labels always come from `status_label` (R5).
6. **Access check is reused, not copied**: `status_history` calls `status_for_customer(customer_id, order_id)` first,
   so missing, other-customer, empty/None customer id and malformed order ids all raise the same
   `OrderNotFound("Order not found")` (R3, E1, E2, E5, E6). One guard is added in front: a non-string order id or
   customer id raises the same error, so an unhashable id (e.g. a list) can never surface as a `TypeError` (E5).
   `get_order` stays internal and is not called by the customer path directly.

## Throughput checkpoint
- Blocking first steps: the failing tests in `tests/test_order_history.py` (from E1–E12 and R1–R8), committed and locked
  with `.pod/lock-tests`; they fix the data shape above (field names, return shape, error types) before any code exists.
- Independent workstreams: `app/timefmt.py` (pure formatting, depends on nothing) can be built separately from the
  `set_status` / `status_history` work in `app/orders.py`; the page demo for R9–R13 is outside this repo.
- Shared mutable state: `_ORDERS` and the new `_HISTORY` in `app/orders.py`, written only by `set_status`; tests must
  isolate them with `patch.dict` / cleanup so `tests/test_orders.py` still sees the original sample data (R7).
- Smallest safe decomposition: (1) `timefmt.time_view` → its tests pass; (2) `StatusUpdate`, `_HISTORY`, `set_status`
  → write-path tests pass; (3) `status_history` → read-path tests pass; each unit ends with `make test` green.

## Parallel parts
none: the whole change is about 80 lines in two small modules, and `status_history` imports `time_view`, so running
two agents would cost more coordination than it saves. Units are built one at a time in the order below.

## Files to change
| File | What changes | Requirement |
|---|---|---|
| `tests/test_order_history.py` (new) | Failing tests for set_status, status_history and Bangkok formatting, one per R/E listed in Proof; state isolated per test | R1–R8, E1–E12 |
| `app/timefmt.py` (new) | `BANGKOK` offset, `_MONTHS`, `time_view(at)` returning `text` and `iso` | R6, E11 |
| `app/orders.py` | Add `StatusUpdate`, `_HISTORY`, `set_status`, `status_history`; existing functions and `STATUS_LABELS` untouched | R1, R2, R3, R4, R5, R8, E5–E10, E12 |
| `tests/test_orders.py` | No change (must pass as is) | R7 |
| `docs/changes/001-order-history/acceptance.md` (later, gate 4) | Demo record for R9–R13 against ux-brief.md | R9–R13 |

No file in `docs/risk-paths` is touched (no `app/auth*`, no migrations). Risk stays high by decision 6.

## Order of work
1. `/superdev:test-first`: write `tests/test_order_history.py` from the edge cases in spec.md; confirm every new test
   fails for the right reason (missing function or wrong value, not an import typo in the test); run
   `make strength`; commit `test(001): ...`.
2. Lock the tests (`touch .pod/lock-tests`).
3. Unit 1: `app/timefmt.py` with `time_view`. `make test` passes for the formatting tests; other new tests still fail.
   Commit `feat(001): Bangkok time format`.
4. Unit 2: in `app/orders.py`, add `StatusUpdate`, `_HISTORY` and `set_status` with the validation table above.
   `make test` passes for R1, R2, E7, E8, E9; commit `feat(001): record status updates`.
5. Unit 3: add `status_history` (guard, reuse of `status_for_customer`, read model). All tests pass, including
   `tests/test_orders.py` unchanged. Commit `feat(001): status history for customers`.
6. `make check` (tests, strength, CODEOWNERS, `gate-check.sh --all`), then `/superdev:review`.
7. Demo R9–R13 with the page owner against ux-brief.md and record results in acceptance.md (gate 4).

## Risks
- **History missed by writers outside this repo.** Anything that sets `_ORDERS[...]["status"]` directly skips history.
  Reduce: `set_status` is the only writer here (decision 1); review checks with a search that no other code assigns
  `status`; the real product must route payment, warehouse and admin changes through the same function.
- **History lost on restart** (in-memory, decision 2). Accepted for this repo; durable storage is a separate change.
  The customer sees "No status updates are listed" and the earlier-updates note, never a wrong time.
- **Test state leaking between tests.** `set_status` changes module-level data that `tests/test_orders.py` reads
  (e.g. A1001 must stay `shipped`). Reduce: replace order dicts instead of mutating them, and isolate every new test
  with `patch.dict(orders._ORDERS)` and `patch.dict(orders._HISTORY, clear=True)`.
- **Existence leak through errors.** A different message or exception type for "other customer" vs "missing" vs
  "malformed id" would reveal that an order exists. Reduce: one code path (`status_for_customer`) plus the type guard,
  and tests compare type and message across all cases.
- **Wrong date at midnight or locale-dependent month names.** Reduce: convert to the fixed +07:00 offset before
  formatting, use a fixed month tuple instead of `%b`, and test 18:30 UTC → `10 Oct 2026, 01:30` (E11).
- **Naive timestamps silently treated as local time.** Reduce: reject them with `ValueError` before any write (E9).
- **Caller edits leaking into storage.** Reduce: immutable `StatusUpdate` records and a freshly built read model (R8).
- **Page-level requirements (R9–R13) cannot be tested here.** Reduce: prove by demo against ux-brief.md, recorded in
  acceptance.md; the page must pass the customer id from the verified session, never from the URL (decision 4).

## Proof
- `make test` and `make strength` pass; `make check` passes.
- R1: change A1001 `shipped` → `delivered` with an aware time; exactly one update with fields `order_id`, `status`, `at`
  (aware), and `get_order("A1001")["status"] == "delivered"`.
- R2: every sample order (A1001–A1004) starts with `history == []` and `updated is None`.
- R3, E1, E2, E5, E6: own order returns data; A1003 as C001, `NOPE`, `""`, `None`, a 1000-char id, `"A1001 "`, `"A1;001"`
  and a list all raise `OrderNotFound` with the same message; empty and None customer ids also raise it.
- R4, E4, E10: two changes → current status, `updated` equal to the newest row's time, rows newest first; two changes
  with the same timestamp list the later-recorded one first.
- R5, E8: `set_status(..., "on_hold", ...)` → label `on_hold` in both current status and history.
- R6, E11: a UTC time formats as `9 Oct 2026, 14:05` with `iso` ending `+07:00`; 2026-10-09 18:30 UTC →
  `10 Oct 2026, 01:30`.
- R7: `tests/test_orders.py` passes without edits (checked by `git diff main -- tests/test_orders.py` being empty).
- R8: editing the returned `history` list and its dicts, then calling `status_history` again, returns the original data.
- E7: setting the current code again returns `False` and adds no update.
- E9: a naive time or a missing order id raises and leaves `_HISTORY` and `_ORDERS` unchanged.
- E12: A1004 (cancelled) is returned like any other order for C003.
- R9–R13, E13–E18: demo of the page (owned outside this repo) against ux-brief.md States, Copy and Accessibility
  notes, recorded in acceptance.md: success, empty, loading, not found (missing and other customer), could-not-load,
  signed out, 10-second timeout, 3 failed retries showing `error.load.support`, keyboard, screen reader, contrast,
  200% zoom and 320 px width.

## Rollback
- Revert the squash-merge commit on main: `git revert <merge-commit>`, open a PR, run `make check`, merge.
- What is lost: the in-memory history recorded since release (accepted in intent.md; it is also lost on any restart).
  No stored data or schema needs to be undone, because there is no migration.
- The page must stop calling `status_history` first (or at the same time), otherwise it gets an `AttributeError`;
  coordinate with the page owner, or have the page show the could-not-load state on failure.
- Check afterwards: `make test` passes, `status_for_customer("C001", "A1001")` returns the same dict as before, and the
  revert is recorded by a human with `scripts/mark-revert.sh` (agents do not run it).

## Open questions
- Who owns the order status page outside this repo, and when can they run the R9–R13 demo before gate 4?
- `{support_contact}` for `error.load.support` is still unknown; the PO supplies it before release (ux-brief.md).
- Whether a status history linked to a customer id is personal data (`intent.md:45-46`) is still open; the data shape
  stores no customer id or personal fields, which SuperDev confirms here.

## Summary for SuperBiz
1. We will keep a record every time an order's status changes and give customers a way to see that list for their own orders, newest first, in Bangkok time.
2. Customers will see when their order was last updated and each earlier change since release; orders not changed since release show the status only, plus the note that earlier updates are not listed.
3. In this sample app the record is lost whenever the system restarts or the change is undone, and the customer page itself lives elsewhere, so it is checked by a live demo rather than automated tests.
