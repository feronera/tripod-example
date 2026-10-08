I've written and committed the failing tests in `tests/test_order_history.py` (commit `f5a54ca`). Two of the required checks didn't run: this session couldn't get approval for `scripts/gate-check.sh` or `scripts/test-strength.sh`.

**Gate 3:** `gate-check.sh` didn't run. As a substitute I read `gates.log`: gate 3 has the owner signature (dan) and the cross signature (bee), and no commit has touched plan.md since. The script itself still needs to confirm it.

**The 26 new tests**, named after spec R/E items:

| Area | Tests |
|---|---|
| `set_status` (saving a change) | R1 ×3 (exactly three fields, server clock by default, saved record can't be edited), E7, E8, E9 ×2 (time without a time zone, missing order: nothing saved) |
| `status_history` (reading) | R2, R3, R3/E1/E2, R4, R5, R6 (input in another time zone), R7, R8, E3, E4, E5 (`""`, `None`, 1000 characters, `"A1001 "`, `"A1;001"`, a list, an int), E6, E10, E11, E12 |
| `timefmt.time_view` (Bangkok time format) | R6 ×3 (no leading zero on the day, 24-hour clock, other offsets), E11 ×2 (crossing midnight, crossing the year end) |

R9–R13 and E13–E18 have no tests, because plan.md says they are proven by demo. R7 is also checked by `tests/test_orders.py` staying unchanged.

**Red run:** `python3 -m unittest discover -s tests -t .` ran 136 tests, with 40 errors (counting subtests). The tests fail for the right reason, because the code doesn't exist yet:
- 19 × `AttributeError: module 'app.orders' has no attribute 'status_history'`
- 16 × `AttributeError: module 'app.orders' has no attribute 'set_status'`
- 5 × `ImportError: cannot import name 'timefmt' from 'app'`

The test file itself loads without errors, and the other 96 tests pass, including `tests/test_orders.py`.

**Strength:** `test-strength.sh` didn't run. Every new test is still red, so the script would only report each one as `FAIL (normal run)`. The skill says to check those by hand, and I did: each test checks results against explicit values from the spec. Tests that check an empty result also check a case with data. Error messages are compared on every not-found path. `make check` will measure strength properly once the code is built.

**What you need to do:**
1. Run `scripts/gate-check.sh docs/changes/001-order-history 3` and `make strength` yourself to confirm.
2. Lock the tests: `touch .pod/lock-tests`. I haven't done this.
3. Next step is `/superdev:build`. When the change is finished, unlock with `rm .pod/lock-tests`.
