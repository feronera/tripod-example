"""Failing tests for change 001 (order status history), from spec.md R1-R8 and E1-E12."""

import copy
import unittest
from datetime import datetime, timedelta, timezone

from app import orders

UTC = timezone.utc
T1 = datetime(2026, 10, 8, 2, 15, tzinfo=UTC)   # Bangkok 8 Oct 2026, 09:15
T2 = datetime(2026, 10, 9, 7, 5, tzinfo=UTC)    # Bangkok 9 Oct 2026, 14:05
T1_VIEW = {"text": "8 Oct 2026, 09:15", "iso": "2026-10-08T09:15:00+07:00"}
T2_VIEW = {"text": "9 Oct 2026, 14:05", "iso": "2026-10-09T14:05:00+07:00"}


def time_view(at):
    # imported here so a missing module fails only the formatting tests
    from app import timefmt
    return timefmt.time_view(at)


class OrderHistoryTestCase(unittest.TestCase):
    def setUp(self):
        saved_orders = copy.deepcopy(orders._ORDERS)

        def restore_orders():
            orders._ORDERS.clear()
            orders._ORDERS.update(saved_orders)

        self.addCleanup(restore_orders)
        history = getattr(orders, "_HISTORY", None)
        if history is not None:
            saved_history = copy.deepcopy(history)
            history.clear()

            def restore_history():
                history.clear()
                history.update(saved_history)

            self.addCleanup(restore_history)


class SetStatusTest(OrderHistoryTestCase):
    def test_r1_records_one_update_with_exactly_three_fields(self):
        changed = orders.set_status("A1001", "delivered", T2)
        self.assertIs(changed, True)
        self.assertEqual(orders.get_order("A1001")["status"], "delivered")
        updates = orders._HISTORY["A1001"]
        self.assertEqual(len(updates), 1)
        update = updates[0]
        self.assertEqual(update._fields, ("order_id", "status", "at"))
        self.assertEqual(update.order_id, "A1001")
        self.assertEqual(update.status, "delivered")
        self.assertEqual(update.at, T2)
        self.assertEqual(update.at.utcoffset(), timedelta(0))

    def test_r1_default_time_is_aware_server_clock(self):
        before = datetime.now(UTC)
        self.assertIs(orders.set_status("A1001", "delivered"), True)
        after = datetime.now(UTC)
        update = orders._HISTORY["A1001"][0]
        self.assertEqual(update.status, "delivered")
        self.assertIsNotNone(update.at.tzinfo)
        self.assertTrue(before <= update.at <= after)

    def test_r1_stored_update_cannot_be_edited_in_place(self):
        orders.set_status("A1001", "delivered", T2)
        update = orders._HISTORY["A1001"][0]
        with self.assertRaises(AttributeError):
            update.status = "cancelled"
        self.assertEqual(orders.status_history("C001", "A1001")["history"][0]["status"], "delivered")

    def test_e7_same_status_records_nothing(self):
        self.assertIs(orders.set_status("A1001", "shipped", T1), False)
        self.assertEqual(orders.status_history("C001", "A1001")["history"], [])
        self.assertIs(orders.set_status("A1001", "delivered", T2), True)
        self.assertEqual(len(orders.status_history("C001", "A1001")["history"]), 1)

    def test_e8_code_without_label_is_recorded_as_raw_code(self):
        self.assertIs(orders.set_status("A1001", "on_hold", T2), True)
        self.assertEqual(orders.get_order("A1001")["status"], "on_hold")
        self.assertEqual(
            orders.status_history("C001", "A1001")["history"],
            [{"status": "on_hold", "label": "on_hold", "time": T2_VIEW}],
        )

    def test_e9_naive_time_is_rejected_and_nothing_stored(self):
        with self.assertRaises(ValueError):
            orders.set_status("A1001", "delivered", datetime(2026, 10, 9, 7, 5))
        self.assertEqual(orders.get_order("A1001")["status"], "shipped")
        self.assertEqual(orders.status_history("C001", "A1001")["history"], [])
        # a valid change afterwards is the only update stored
        orders.set_status("A1001", "delivered", T2)
        self.assertEqual(
            orders.status_history("C001", "A1001")["history"],
            [{"status": "delivered", "label": "Delivered", "time": T2_VIEW}],
        )

    def test_e9_missing_order_is_rejected_and_nothing_stored(self):
        with self.assertRaises(orders.OrderNotFound):
            orders.set_status("NOPE", "delivered", T2)
        self.assertIsNone(orders.get_order("NOPE"))
        self.assertNotIn("NOPE", orders._HISTORY)
        self.assertEqual(sorted(orders._ORDERS), ["A1001", "A1002", "A1003", "A1004"])
        self.assertEqual(orders.get_order("A1001")["status"], "shipped")


class StatusHistoryTest(OrderHistoryTestCase):
    def test_r2_sample_orders_start_with_empty_history(self):
        owners = {
            "A1001": ("C001", "shipped", "Shipped"),
            "A1002": ("C001", "delivered", "Delivered"),
            "A1003": ("C002", "pending", "Awaiting payment"),
            "A1004": ("C003", "cancelled", "Cancelled"),
        }
        for order_id, (customer_id, status, label) in owners.items():
            with self.subTest(order_id=order_id):
                self.assertEqual(
                    orders.status_history(customer_id, order_id),
                    {"order_id": order_id, "status": status, "label": label,
                     "updated": None, "history": []},
                )

    def test_r3_own_order_returns_history(self):
        orders.set_status("A1001", "delivered", T2)
        result = orders.status_history("C001", "A1001")
        self.assertEqual(result["order_id"], "A1001")
        self.assertEqual(result["status"], "delivered")

    def test_r3_e1_e2_other_customer_and_missing_order_look_the_same(self):
        with self.assertRaises(orders.OrderNotFound) as other:
            orders.status_history("C001", "A1003")
        with self.assertRaises(orders.OrderNotFound) as missing:
            orders.status_history("C001", "NOPE")
        self.assertIs(type(other.exception), type(missing.exception))
        self.assertEqual(str(other.exception), "Order not found")
        self.assertEqual(str(missing.exception), "Order not found")

    def test_e5_malformed_order_id_is_not_found(self):
        malformed = ["", None, "A" * 1000, "A1001 ", "A1;001", ["A1001"], 1001]
        for order_id in malformed:
            with self.subTest(order_id=repr(order_id)[:20]):
                with self.assertRaises(orders.OrderNotFound) as caught:
                    orders.status_history("C001", order_id)
                self.assertIs(type(caught.exception), orders.OrderNotFound)
                self.assertEqual(str(caught.exception), "Order not found")
        self.assertEqual(orders.status_history("C001", "A1001")["status"], "shipped")

    def test_e6_missing_or_empty_customer_id_is_not_found(self):
        for customer_id in ["", None, ["C001"]]:
            with self.subTest(customer_id=customer_id):
                with self.assertRaises(orders.OrderNotFound) as caught:
                    orders.status_history(customer_id, "A1001")
                self.assertIs(type(caught.exception), orders.OrderNotFound)
                self.assertEqual(str(caught.exception), "Order not found")
        self.assertEqual(orders.status_history("C001", "A1001")["label"], "Shipped")

    def test_r4_two_changes_newest_first(self):
        orders.set_status("A1003", "paid", T1)
        orders.set_status("A1003", "packing", T2)
        self.assertEqual(
            orders.status_history("C002", "A1003"),
            {
                "order_id": "A1003",
                "status": "packing",
                "label": "Preparing order",
                "updated": T2_VIEW,
                "history": [
                    {"status": "packing", "label": "Preparing order", "time": T2_VIEW},
                    {"status": "paid", "label": "Paid", "time": T1_VIEW},
                ],
            },
        )

    def test_e3_owned_order_without_updates_has_no_updated_time(self):
        self.assertEqual(
            orders.status_history("C001", "A1002"),
            {"order_id": "A1002", "status": "delivered", "label": "Delivered",
             "updated": None, "history": []},
        )

    def test_e4_recorded_current_status_is_also_newest_row(self):
        orders.set_status("A1001", "delivered", T2)
        result = orders.status_history("C001", "A1001")
        self.assertEqual(result["status"], "delivered")
        self.assertEqual(result["updated"], T2_VIEW)
        self.assertEqual(result["history"][0], {"status": "delivered", "label": "Delivered", "time": T2_VIEW})
        self.assertEqual(result["updated"], result["history"][0]["time"])

    def test_r5_unknown_code_label_falls_back_to_code(self):
        orders.set_status("A1001", "on_hold", T2)
        self.assertEqual(
            orders.status_history("C001", "A1001"),
            {
                "order_id": "A1001",
                "status": "on_hold",
                "label": "on_hold",
                "updated": T2_VIEW,
                "history": [{"status": "on_hold", "label": "on_hold", "time": T2_VIEW}],
            },
        )

    def test_r6_non_utc_input_is_shown_in_bangkok_time(self):
        tokyo = timezone(timedelta(hours=9))
        orders.set_status("A1001", "delivered", datetime(2026, 10, 9, 16, 5, tzinfo=tokyo))
        self.assertEqual(orders.status_history("C001", "A1001")["updated"], T2_VIEW)

    def test_r7_status_for_customer_shape_is_unchanged_after_a_change(self):
        orders.set_status("A1001", "delivered", T2)
        self.assertEqual(
            orders.status_for_customer("C001", "A1001"),
            {"order_id": "A1001", "status": "delivered", "label": "Delivered"},
        )
        self.assertEqual(
            [o["status"] for o in orders.orders_for_customer("C001")],
            ["delivered", "delivered"],
        )

    def test_r8_editing_the_result_does_not_change_stored_history(self):
        orders.set_status("A1003", "paid", T1)
        orders.set_status("A1003", "packing", T2)
        first = orders.status_history("C002", "A1003")
        first["history"][0]["status"] = "cancelled"
        first["history"][0]["time"]["text"] = "edited"
        first["history"].append({"status": "x", "label": "x", "time": None})
        first["updated"]["iso"] = "edited"
        first["status"] = "cancelled"
        self.assertEqual(
            orders.status_history("C002", "A1003"),
            {
                "order_id": "A1003",
                "status": "packing",
                "label": "Preparing order",
                "updated": T2_VIEW,
                "history": [
                    {"status": "packing", "label": "Preparing order", "time": T2_VIEW},
                    {"status": "paid", "label": "Paid", "time": T1_VIEW},
                ],
            },
        )

    def test_e10_same_timestamp_later_recorded_first(self):
        orders.set_status("A1001", "delivered", T2)
        orders.set_status("A1001", "cancelled", T2)
        self.assertEqual(
            orders.status_history("C001", "A1001")["history"],
            [
                {"status": "cancelled", "label": "Cancelled", "time": T2_VIEW},
                {"status": "delivered", "label": "Delivered", "time": T2_VIEW},
            ],
        )

    def test_e11_history_uses_bangkok_date_across_midnight(self):
        orders.set_status("A1001", "delivered", datetime(2026, 10, 9, 18, 30, tzinfo=UTC))
        self.assertEqual(
            orders.status_history("C001", "A1001")["history"][0]["time"],
            {"text": "10 Oct 2026, 01:30", "iso": "2026-10-10T01:30:00+07:00"},
        )

    def test_e12_cancelled_order_is_shown_like_any_other(self):
        self.assertEqual(
            orders.status_history("C003", "A1004"),
            {"order_id": "A1004", "status": "cancelled", "label": "Cancelled",
             "updated": None, "history": []},
        )
        orders.set_status("A1001", "cancelled", T2)
        self.assertEqual(
            orders.status_history("C001", "A1001"),
            {
                "order_id": "A1001",
                "status": "cancelled",
                "label": "Cancelled",
                "updated": T2_VIEW,
                "history": [{"status": "cancelled", "label": "Cancelled", "time": T2_VIEW}],
            },
        )


class TimeViewTest(unittest.TestCase):
    def test_r6_formats_utc_time_in_bangkok(self):
        self.assertEqual(time_view(T2), T2_VIEW)

    def test_r6_day_has_no_leading_zero_and_clock_is_24_hour(self):
        self.assertEqual(
            time_view(datetime(2026, 10, 1, 15, 0, tzinfo=UTC)),
            {"text": "1 Oct 2026, 22:00", "iso": "2026-10-01T22:00:00+07:00"},
        )

    def test_r6_converts_other_offsets_to_bangkok(self):
        tokyo = timezone(timedelta(hours=9))
        self.assertEqual(time_view(datetime(2026, 1, 5, 9, 0, tzinfo=tokyo)),
                         {"text": "5 Jan 2026, 07:00", "iso": "2026-01-05T07:00:00+07:00"})

    def test_e11_crosses_midnight_into_bangkok_date(self):
        self.assertEqual(
            time_view(datetime(2026, 10, 9, 18, 30, tzinfo=UTC)),
            {"text": "10 Oct 2026, 01:30", "iso": "2026-10-10T01:30:00+07:00"},
        )

    def test_e11_crosses_year_end(self):
        self.assertEqual(
            time_view(datetime(2026, 12, 31, 17, 0, tzinfo=UTC)),
            {"text": "1 Jan 2027, 00:00", "iso": "2027-01-01T00:00:00+07:00"},
        )


if __name__ == "__main__":
    unittest.main()
