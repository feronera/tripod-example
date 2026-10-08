I wrote 14 failing tests for change 002 in `tests/test_status_report.py` and committed them as `ef55042` (`test(002): failing tests from spec`). They aren't locked yet; that's for you to do.

**Why they fail:** in `make test`, all 14 new tests fail with `AttributeError: module 'app.orders' has no attribute 'status_counts'`, because the function doesn't exist yet. The other 136 tests still pass.

**Commands I couldn't run:** this run had no way to approve them, so these weren't run:
- **`scripts/gate-check.sh … 3`:** instead I checked that both gate 3 sign-offs in `gates.log` match the current plan.md (blob `dfa621f…`). Please run the script yourself to confirm.
- **`make strength`:** it can't measure tests that are still red anyway, so I checked them by hand against the 5 weak-test kinds. Each test calls `orders.status_counts()` the way the support lead would and compares the result to fixed values written in the test. A function that returns `None` fails all of them. `make check` measures them properly once the code exists.
- **A trial run against a throwaway version of the plan's design:** instead I worked out the key orders by hand from the plan's sort rule. For example, with `on_hold`, `3` and `None` as statuses, the order after the six labels is `on_hold`, `3`, `None`.

**Tests by requirement:**
| Requirement | Test |
|---|---|
| R1 | `test_r1_demo_data_counts_current_status` (exact counts and key order) |
| R1/E8 | `test_r1_e8_only_current_status_is_counted_not_history` |
| E8 | `test_e8_second_call_reflects_status_change` |
| R2 | `test_r2_known_code_is_keyed_by_label` |
| R3/E2 | `test_r3_e2_labels_without_orders_are_zero` |
| E1 | `test_e1_no_orders_gives_every_label_zero` |
| R4/E3 | `test_r4_e3_unlabelled_code_counted_under_raw_code` (`on_hold: 1`, `Shipped: 0`) |
| R5 | `test_r5_labels_first_then_raw_codes_sorted` |
| E4 | `test_e4_empty_status_counted_under_empty_key` |
| E5 | `test_e5_none_and_int_status_do_not_raise_and_keep_raw_value` (also checks mixed-type order) |
| E6 | `test_e6_raw_code_equal_to_label_text_merges_with_label` (`Paid: 2`) |
| R6/E7 | `test_r6_e7_only_status_keys_and_int_counts` (no customer ids, order ids or items) |
| R7 | `test_r7_call_and_editing_result_do_not_change_stores` |
| R8 | `test_r8_sum_equals_number_of_orders` |

R9 is checked by the demo at gate 4, as the spec says, so it has no unit test. Each test saves and restores `_ORDERS` and `_HISTORY` the same way the order history tests do.

One mismatch with plan.md: it says `.pod/lock-tests` is left over from change 001, but the file doesn't exist, so nothing needed removing.

**Next steps:**
1. Lock the tests: `touch .pod/lock-tests`
2. Run `/superdev:build`
3. When the change is finished, unlock with `rm .pod/lock-tests`
