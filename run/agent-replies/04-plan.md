I've written `docs/changes/001-order-history/plan.md`. The gate 3 format check passes: it reports no missing sections, only the two signatures that haven't been given yet, which is expected. The plan is not committed.

**What the plan says, following the decisions at the end of spec.md:**
- **Data shape:**
  - Each status change is stored as a fixed record holding only the order id, the new status code and a UTC time. There is no customer id and no personal data.
  - These records go into an in-memory table per order, kept in the order they were recorded. "Newest first" is just that order reversed, so two changes with the same timestamp show the later one first without extra code.
  - `set_status(order_id, status, at=None)` is the only function that changes a status. It updates the status and the history together, and it checks everything before writing. A missing order or a timestamp without a time zone is rejected and nothing is stored. Setting the same code again records nothing.
  - A new small module, `app/timefmt.py`, turns a time into Bangkok time (fixed +07:00) in the format `9 Oct 2026, 14:05`, plus the ISO value. It uses a fixed list of English month names so the output doesn't depend on the computer's language settings.
  - `status_history(customer_id, order_id)` first runs the existing `status_for_customer` ownership check, so a missing order, someone else's order and a malformed id all give the same "Order not found" error. It also rejects ids that aren't text the same way. It returns fresh copies, so a caller can't change the stored history.
- **Parallel parts:** none. The change is about 80 lines across two small modules, and one depends on the other.
- **Order of work:** failing tests in `tests/test_order_history.py`, then lock the tests, then three small steps (time format, `set_status`, `status_history`), each ending with `make test` passing.
- **Tests and existing data:** `tests/test_orders.py` stays untouched. To protect it, `set_status` replaces an order's entry instead of editing it in place, and each new test restores the sample data when it finishes.
- **Rollback:** revert the merge commit. The only thing lost is the in-memory history, which is accepted. There's no migration. The customer page must stop calling `status_history` before or with the revert.
- **Open questions in the plan:** who owns the customer page and will run the demo of R9–R13 before gate 4, the real support contact, and whether a history linked to a customer id counts as personal data.

**Next steps:**
1. SuperDev runs `scripts/gate.sh docs/changes/001-order-history 3`.
2. SuperBiz reads "Summary for SuperBiz", checks it still matches the intent, then runs the same command.
3. Then `/superdev:test-first`, then `/superdev:build`.
