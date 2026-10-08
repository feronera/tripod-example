"""Failing tests for change 002 (order count per status), from spec.md R1-R8 and E1-E8."""

import copy
import unittest
from datetime import datetime, timezone

from app import orders

UTC = timezone.utc
T1 = datetime(2026, 10, 8, 2, 15, tzinfo=UTC)
T2 = datetime(2026, 10, 9, 7, 5, tzinfo=UTC)

LABELS = [
    "Awaiting payment",
    "Paid",
    "Preparing order",
    "Shipped",
    "Delivered",
    "Cancelled",
]
DEMO_COUNTS = {
    "Awaiting payment": 1,
    "Paid": 0,
    "Preparing order": 0,
    "Shipped": 1,
    "Delivered": 1,
    "Cancelled": 1,
}


class StatusReportTestCase(unittest.TestCase):
    def setUp(self):
        saved_orders = copy.deepcopy(orders._ORDERS)

        def restore_orders():
            orders._ORDERS.clear()
            orders._ORDERS.update(saved_orders)

        self.addCleanup(restore_orders)
        saved_history = copy.deepcopy(orders._HISTORY)
        orders._HISTORY.clear()

        def restore_history():
            orders._HISTORY.clear()
            orders._HISTORY.update(saved_history)

        self.addCleanup(restore_history)


class CountsTest(StatusReportTestCase):
    def test_r1_demo_data_counts_current_status(self):
        result = orders.status_counts()
        self.assertEqual(result, DEMO_COUNTS)
        self.assertEqual(list(result), LABELS)

    def test_r1_e8_only_current_status_is_counted_not_history(self):
        orders.set_status("A1003", "paid", T1)
        orders.set_status("A1003", "packing", T2)
        self.assertEqual(len(orders._HISTORY["A1003"]), 2)
        self.assertEqual(
            orders.status_counts(),
            {
                "Awaiting payment": 0,
                "Paid": 0,
                "Preparing order": 1,
                "Shipped": 1,
                "Delivered": 1,
                "Cancelled": 1,
            },
        )

    def test_e8_second_call_reflects_status_change(self):
        self.assertEqual(orders.status_counts()["Shipped"], 1)
        orders.set_status("A1001", "delivered", T2)
        result = orders.status_counts()
        self.assertEqual(result["Shipped"], 0)
        self.assertEqual(result["Delivered"], 2)

    def test_r2_known_code_is_keyed_by_label(self):
        result = orders.status_counts()
        self.assertEqual(result["Awaiting payment"], 1)
        for code in ("pending", "paid", "packing", "shipped", "delivered", "cancelled"):
            self.assertNotIn(code, result)

    def test_r3_e2_labels_without_orders_are_zero(self):
        result = orders.status_counts()
        self.assertEqual(result["Paid"], 0)
        self.assertEqual(result["Preparing order"], 0)
        self.assertEqual(result["Shipped"], 1)
        self.assertEqual(sorted(result), sorted(LABELS))

    def test_e1_no_orders_gives_every_label_zero(self):
        orders._ORDERS.clear()
        result = orders.status_counts()
        self.assertEqual(result, {label: 0 for label in LABELS})
        self.assertEqual(list(result), LABELS)
        self.assertEqual(sum(result.values()), 0)

    def test_r4_e3_unlabelled_code_counted_under_raw_code(self):
        orders.set_status("A1001", "on_hold", T2)
        result = orders.status_counts()
        self.assertEqual(result["on_hold"], 1)
        self.assertEqual(result["Shipped"], 0)
        self.assertEqual(list(result), LABELS + ["on_hold"])

    def test_r5_labels_first_then_raw_codes_sorted(self):
        orders.set_status("A1001", "zz_lost", T2)
        orders.set_status("A1002", "on_hold", T2)
        result = orders.status_counts()
        self.assertEqual(list(result), LABELS + ["on_hold", "zz_lost"])
        self.assertEqual(result["on_hold"], 1)
        self.assertEqual(result["zz_lost"], 1)
        self.assertEqual(result["Shipped"], 0)
        self.assertEqual(result["Delivered"], 0)

    def test_e4_empty_status_counted_under_empty_key(self):
        orders.set_status("A1001", "", T2)
        result = orders.status_counts()
        self.assertEqual(result[""], 1)
        self.assertEqual(result["Shipped"], 0)
        self.assertEqual(list(result), LABELS + [""])

    def test_e5_none_and_int_status_do_not_raise_and_keep_raw_value(self):
        orders.set_status("A1001", None, T2)
        orders.set_status("A1002", 3, T2)
        orders.set_status("A1003", "on_hold", T2)
        result = orders.status_counts()
        self.assertEqual(result[None], 1)
        self.assertEqual(result[3], 1)
        self.assertEqual(result["on_hold"], 1)
        self.assertEqual(result["Shipped"], 0)
        self.assertEqual(result["Delivered"], 0)
        self.assertEqual(result["Awaiting payment"], 0)
        # string raw codes first, then non-strings ordered by their text ("3" < "None")
        self.assertEqual(list(result), LABELS + ["on_hold", 3, None])

    def test_e6_raw_code_equal_to_label_text_merges_with_label(self):
        orders.set_status("A1001", "Paid", T2)
        orders.set_status("A1002", "paid", T2)
        result = orders.status_counts()
        self.assertEqual(result["Paid"], 2)
        self.assertEqual(list(result), LABELS)
        self.assertEqual(sum(result.values()), 4)


class PrivacyTest(StatusReportTestCase):
    def test_r6_e7_only_status_keys_and_int_counts(self):
        orders.set_status("A1001", "on_hold", T2)
        result = orders.status_counts()
        self.assertEqual(set(result), set(LABELS) | {"on_hold"})
        self.assertEqual(result["on_hold"], 1)
        for key, value in result.items():
            self.assertIs(type(value), int, key)
        text = repr(result)
        for secret in ("C001", "C002", "C003", "A1001", "A1002", "A1003", "A1004",
                       "T-shirt", "Cap", "Shoes", "Bag", "Watch", "customer_id", "items"):
            self.assertNotIn(secret, text)


class ReadOnlyTest(StatusReportTestCase):
    def test_r7_call_and_editing_result_do_not_change_stores(self):
        orders.set_status("A1001", "on_hold", T2)
        orders_before = copy.deepcopy(orders._ORDERS)
        history_before = copy.deepcopy(orders._HISTORY)

        result = orders.status_counts()
        self.assertEqual(result["on_hold"], 1)
        self.assertEqual(orders._ORDERS, orders_before)
        self.assertEqual(orders._HISTORY, history_before)

        result["on_hold"] = 99
        result["Delivered"] = 42
        result["extra"] = 1
        del result["Cancelled"]
        self.assertEqual(orders._ORDERS, orders_before)
        self.assertEqual(orders._HISTORY, history_before)

        again = orders.status_counts()
        self.assertEqual(again["on_hold"], 1)
        self.assertEqual(again["Delivered"], 1)
        self.assertEqual(again["Cancelled"], 1)
        self.assertNotIn("extra", again)


class SumTest(StatusReportTestCase):
    def test_r8_sum_equals_number_of_orders(self):
        self.assertEqual(sum(orders.status_counts().values()), 4)
        orders.set_status("A1001", "on_hold", T2)
        orders.set_status("A1002", None, T2)
        self.assertEqual(sum(orders.status_counts().values()), 4)
        orders._ORDERS["A1005"] = {"customer_id": "C004", "status": "paid", "items": ["Hat"]}
        result = orders.status_counts()
        self.assertEqual(sum(result.values()), 5)
        self.assertEqual(result["Paid"], 1)


if __name__ == "__main__":
    unittest.main()
