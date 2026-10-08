"""Failing tests for change 003, part A (page rendering), from spec.md and plan.md (Data shape).

Covers app/order_page.py (COPY, the view records, resolve, render, Page) and the static files the shell links.
Part B (server and demo sign-in) is tested in tests/test_order_server.py.
"""

import ast
import copy
import inspect
import pathlib
import re
import unittest
from datetime import datetime, timezone
from unittest import mock

from app import orders
from tests._html import by_text, parse

APP_DIR = pathlib.Path(__file__).resolve().parent.parent / "app"
UTC = timezone.utc
T1 = datetime(2026, 10, 8, 2, 15, tzinfo=UTC)   # Bangkok 8 Oct 2026, 09:15
T2 = datetime(2026, 10, 9, 7, 5, tzinfo=UTC)    # Bangkok 9 Oct 2026, 14:05
T1_VIEW = {"text": "8 Oct 2026, 09:15", "iso": "2026-10-08T09:15:00+07:00"}
T2_VIEW = {"text": "9 Oct 2026, 14:05", "iso": "2026-10-09T14:05:00+07:00"}

# Copy from ux-brief.md "Copy", exactly
BANNER = "Demo sign-in: Customer C001"
TIMEZONE_NOTE = "Times are shown in Bangkok time (GMT+7)."
EARLIER_NOTE = "Earlier updates are not listed."
EMPTY_NOTE = "No status updates are listed for this order."
NOT_FOUND_TITLE = "Order not found"
NOT_FOUND_BODY = (
    "We couldn't find this order. Open the order link in your order confirmation email, "
    "and check that you are signed in with the account you used to place the order."
)
LOAD_TITLE = "We couldn't load your order"
LOAD_BODY = "Something went wrong. Check your connection and try again in a moment."
SUPPORT = "Still not working? Contact support at support@shop.example."
LOADING = "Loading your order…"
UX_COPY = {
    "demo.banner": "Demo sign-in: Customer {customer_id}",
    "page.title": "Order {order_id}",
    "page.loading_title": "Loading order",
    "page.loading": LOADING,
    "status.heading": "Current status",
    "status.updated": "Updated {datetime}",
    "history.heading": "Status history",
    "history.order": "Newest first",
    "history.row": "{status_label} – {datetime}",
    "history.empty": EMPTY_NOTE,
    "history.earlier_note": EARLIER_NOTE,
    "history.timezone": TIMEZONE_NOTE,
    "error.not_found.title": NOT_FOUND_TITLE,
    "error.not_found.body": NOT_FOUND_BODY,
    "error.load.title": LOAD_TITLE,
    "error.load.body": LOAD_BODY,
    "error.load.retry": "Try again",
    "error.load.support": SUPPORT,
}
SECURITY_HEADERS = (
    ("Content-Type", "text/html; charset=utf-8"),
    ("Cache-Control", "no-store"),
    ("X-Content-Type-Options", "nosniff"),
    ("Referrer-Policy", "no-referrer"),
    ("Content-Security-Policy",
     "default-src 'none'; script-src 'self'; style-src 'self'; connect-src 'self'; frame-ancestors 'none'"),
)


def op():
    # imported here so a missing module fails each test on its own
    from app import order_page
    return order_page


def signed_in_as(customer_id):
    return lambda: customer_id


class Calls:
    """A load that records each call, then raises `error` or delegates to status_history."""

    def __init__(self, error=None):
        self.calls = []
        self.error = error

    def __call__(self, customer_id, order_id):
        self.calls.append((customer_id, order_id))
        if self.error is not None:
            raise self.error
        return orders.status_history(customer_id, order_id)


class PageTestCase(unittest.TestCase):
    def setUp(self):
        # seeded orders and history are undone after each test, so 001/002 tests see the sample data
        for patcher in (mock.patch.dict(orders._ORDERS), mock.patch.dict(orders._HISTORY, clear=True)):
            patcher.start()
            self.addCleanup(patcher.stop)

    def view(self, order_id, customer_id="C001", load=None):
        if load is None:
            return op().resolve(signed_in_as(customer_id), order_id)
        return op().resolve(signed_in_as(customer_id), order_id, load)

    def doc(self, view, banner=BANNER):
        page = op().render(view, banner)
        return page, parse(page.body)

    def one(self, root, tag, attrs=None):
        found = root.find_all(tag, attrs)
        self.assertEqual(len(found), 1, f"expected one <{tag}> {attrs or ''}, found {len(found)}")
        return found[0]

    def title(self, root):
        return self.one(root, "title").text()

    def texts(self, root, tag):
        return [el.text() for el in root.find_all(tag)]

    def times(self, root):
        return [(t.attrs.get("datetime"), t.text()) for t in root.find_all("time")]

    def in_live_region(self, el):
        return any(a.attrs.get("role") == "status" for a in [el, *el.ancestors()])

    def assertInOrder(self, text, parts):
        pos = 0
        for part in parts:
            found = text.find(part, pos)
            self.assertNotEqual(found, -1, f"{part!r} missing or out of order in {text!r}")
            pos = found + len(part)

    def body_views(self):
        """Every state that has a page body (all but signed out)."""
        m = op()
        return {
            "loading": m.Loading("A1001"),
            "loading_no_id": m.Loading(None),
            "success": m.Success("A1001", "Delivered", T2_VIEW, (("Delivered", T2_VIEW), ("Paid", T1_VIEW))),
            "empty": m.Empty("A1002", "Delivered"),
            "not_found": m.NotFound(),
            "load_error": m.LoadError(False),
            "load_error_support": m.LoadError(True),
        }


class ResolveTest(PageTestCase):
    def test_r1_r5_owned_order_with_updates_resolves_to_success(self):
        orders.set_status("A1001", "paid", T1)
        orders.set_status("A1001", "delivered", T2)
        view = self.view("A1001")
        self.assertIs(type(view), op().Success)
        self.assertEqual(
            view,
            op().Success("A1001", "Delivered", T2_VIEW, (("Delivered", T2_VIEW), ("Paid", T1_VIEW))),
        )

    def test_r6_e1_owned_order_without_updates_resolves_to_empty(self):
        view = self.view("A1002")
        self.assertIs(type(view), op().Empty)
        self.assertEqual(view, op().Empty("A1002", "Delivered"))
        self.assertEqual(self.view("A1001"), op().Empty("A1001", "Shipped"))

    def test_e2_latest_update_not_current_has_no_updated_time(self):
        orders.set_status("A1001", "paid", T1)
        orders._ORDERS["A1001"] = {**orders._ORDERS["A1001"], "status": "shipped"}
        self.assertEqual(
            self.view("A1001"),
            op().Success("A1001", "Shipped", None, (("Paid", T1_VIEW),)),
        )

    def test_r7_e3_e11_missing_and_other_customers_orders_are_not_found(self):
        for order_id in ["A9999", "A1003", "A1004"]:
            with self.subTest(order_id=order_id):
                view = self.view(order_id)
                self.assertIs(type(view), op().NotFound)
                self.assertEqual(view, op().NotFound())
        # the owner still sees it
        self.assertEqual(self.view("A1003", customer_id="C002"), op().Empty("A1003", "Awaiting payment"))

    def test_r2_customer_id_comes_only_from_identify(self):
        # resolve takes no request data, so a query, header or cookie cannot supply a customer id
        self.assertEqual(list(inspect.signature(op().resolve).parameters), ["identify", "order_id", "load"])
        load = Calls()
        self.assertEqual(op().resolve(signed_in_as("C001"), "A1001", load), op().Empty("A1001", "Shipped"))
        self.assertEqual(op().resolve(signed_in_as("C002"), "A1003", load), op().Empty("A1003", "Awaiting payment"))
        self.assertEqual(load.calls, [("C001", "A1001"), ("C002", "A1003")])

    def test_r3_e13_no_signed_in_customer_never_loads(self):
        load = Calls()
        for order_id in ["A1001", "A1003", "A9999"]:
            with self.subTest(order_id=order_id):
                view = op().resolve(lambda: None, order_id, load)
                self.assertIs(type(view), op().SignedOut)
                self.assertEqual(op().render(view, BANNER).status, 303)
        self.assertEqual(load.calls, [])
        op().resolve(signed_in_as("C001"), "A1001", load)
        self.assertEqual(load.calls, [("C001", "A1001")])

    def test_r3_sign_in_is_checked_before_loading(self):
        events = []

        def identify():
            events.append("identify")
            return "C001"

        def load(customer_id, order_id):
            events.append(("load", customer_id, order_id))
            return orders.status_history(customer_id, order_id)

        self.assertEqual(op().resolve(identify, "A1002", load), op().Empty("A1002", "Delivered"))
        self.assertEqual(events, ["identify", ("load", "C001", "A1002")])

    def test_e14_stand_in_failure_is_could_not_load_for_every_order(self):
        def identify():
            raise RuntimeError("stand-in down")

        load = Calls()
        pages = []
        for order_id in ["A1001", "A1003", "A9999"]:
            with self.subTest(order_id=order_id):
                view = op().resolve(identify, order_id, load)
                self.assertIs(type(view), op().LoadError)
                self.assertEqual(view, op().LoadError(False))
                pages.append(op().render(view, BANNER))
        self.assertEqual(load.calls, [])
        self.assertEqual(pages[0].status, 503)
        self.assertEqual(pages[1], pages[0])
        self.assertEqual(pages[2], pages[0])

    def test_r8_load_failure_is_could_not_load(self):
        for error in [RuntimeError("down"), TimeoutError(), OSError("disk"), KeyError("x")]:
            with self.subTest(error=type(error).__name__):
                view = self.view("A1001", load=Calls(error))
                self.assertIs(type(view), op().LoadError)
                self.assertEqual(view, op().LoadError(False))
        self.assertEqual(self.view("A1001", load=Calls()), op().Empty("A1001", "Shipped"))

    def test_r4_resolving_and_rendering_change_no_data(self):
        orders.set_status("A1001", "paid", T1)
        orders.set_status("A1001", "delivered", T2)
        before = (copy.deepcopy(orders._ORDERS), copy.deepcopy(orders._HISTORY))
        statuses = [
            op().render(self.view("A1001"), BANNER).status,
            op().render(self.view("A1002"), BANNER).status,
            op().render(self.view("A9999"), BANNER).status,
            op().render(op().resolve(lambda: None, "A1001"), None).status,
            op().render(self.view("A1001", load=Calls(RuntimeError("down"))), BANNER).status,
            op().render(op().Loading("A1001"), BANNER).status,
        ]
        self.assertEqual(statuses, [200, 200, 404, 303, 503, 200])
        self.assertEqual((orders._ORDERS, orders._HISTORY), before)

    def test_r1_page_reads_orders_only_through_status_history(self):
        orders.set_status("A1001", "delivered", T2)
        writes = mock.patch.object(orders, "set_status", side_effect=AssertionError("page wrote data"))
        lists = mock.patch.object(orders, "orders_for_customer", side_effect=AssertionError("not allowed"))
        counts = mock.patch.object(orders, "status_counts", side_effect=AssertionError("not allowed"))
        with writes, lists, counts:
            page, root = self.doc(self.view("A1001"))
        self.assertEqual(page.status, 200)
        self.assertEqual(self.texts(root, "h1"), ["Order A1001"])

        tree = ast.parse((APP_DIR / "order_page.py").read_text(encoding="utf-8"))
        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module == "app.orders":
                imported |= {alias.name for alias in node.names}
            if isinstance(node, ast.ImportFrom) and node.module == "app":
                self.assertNotIn("orders", {alias.name for alias in node.names})
                self.assertNotIn("auth_demo", {alias.name for alias in node.names})
            if isinstance(node, ast.Import):
                self.assertFalse({a.name for a in node.names} & {"app.orders", "app.auth_demo"})
        self.assertIn("status_history", imported)
        self.assertLessEqual(imported, {"status_history", "OrderNotFound"})
        used = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)}
        used |= {n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)}
        forbidden = {"get_order", "set_status", "orders_for_customer", "status_counts", "status_for_customer"}
        self.assertEqual(used & forbidden, set())


class RenderStatesTest(PageTestCase):
    def test_r5_success_page_shows_status_then_history_newest_first(self):
        orders.set_status("A1001", "paid", T1)
        orders.set_status("A1001", "delivered", T2)
        page, root = self.doc(self.view("A1001"))
        self.assertEqual(page.status, 200)
        self.assertEqual(self.title(root), "Order A1001")
        self.assertEqual(self.texts(root, "h1"), ["Order A1001"])
        self.assertEqual(self.texts(root, "h2"), ["Current status", "Status history"])
        main = self.one(root, "main").text()
        self.assertInOrder(main, [
            "Order A1001", "Current status", "Delivered", "Updated 9 Oct 2026, 14:05", TIMEZONE_NOTE,
            "Status history", "Newest first",
            "Delivered – 9 Oct 2026, 14:05", "Paid – 8 Oct 2026, 09:15", EARLIER_NOTE,
        ])
        # the time zone note sits directly under the "Updated" line
        self.assertRegex(main, r"Updated 9 Oct 2026, 14:05\s*" + re.escape(TIMEZONE_NOTE))
        self.assertEqual(len(by_text(root, "Updated 9 Oct 2026, 14:05")), 1)
        ol = self.one(root, "ol")
        self.assertEqual(ol.attrs.get("aria-label"), "Status history, newest first")
        self.assertEqual(self.texts(ol, "li"), ["Delivered – 9 Oct 2026, 14:05", "Paid – 8 Oct 2026, 09:15"])
        self.assertEqual(self.times(root), [
            ("2026-10-09T14:05:00+07:00", "9 Oct 2026, 14:05"),
            ("2026-10-09T14:05:00+07:00", "9 Oct 2026, 14:05"),
            ("2026-10-08T09:15:00+07:00", "8 Oct 2026, 09:15"),
        ])

    def test_e2_success_without_updated_line_still_lists_history(self):
        page, root = self.doc(op().Success("A1001", "Shipped", None, (("Paid", T1_VIEW),)))
        self.assertEqual(page.status, 200)
        main = self.one(root, "main").text()
        self.assertNotIn("Updated", main)
        self.assertInOrder(main, ["Order A1001", "Shipped", TIMEZONE_NOTE, "Paid – 8 Oct 2026, 09:15", EARLIER_NOTE])
        self.assertEqual(self.texts(root, "li"), ["Paid – 8 Oct 2026, 09:15"])
        self.assertEqual(self.times(root), [("2026-10-08T09:15:00+07:00", "8 Oct 2026, 09:15")])

    def test_r6_e1_empty_page_has_no_updated_line_and_says_none_listed(self):
        page, root = self.doc(self.view("A1002"))
        self.assertEqual(page.status, 200)
        self.assertEqual(self.title(root), "Order A1002")
        self.assertEqual(self.texts(root, "h1"), ["Order A1002"])
        self.assertEqual(self.texts(root, "h2"), ["Current status", "Status history"])
        main = self.one(root, "main").text()
        self.assertNotIn("Updated", main)
        self.assertInOrder(main, ["Order A1002", "Current status", "Delivered", TIMEZONE_NOTE, EMPTY_NOTE, EARLIER_NOTE])
        self.assertEqual(self.times(root), [])
        self.assertEqual(self.texts(root, "li"), [])

    def test_r7_not_found_page_has_no_link_and_no_retry(self):
        page, root = self.doc(op().NotFound())
        self.assertEqual(page.status, 404)
        self.assertEqual(self.title(root), NOT_FOUND_TITLE)
        self.assertEqual(self.texts(root, "h1"), [NOT_FOUND_TITLE])
        self.assertIn(NOT_FOUND_BODY, self.one(root, "main").text())
        self.assertTrue(any(NOT_FOUND_BODY in el.text() and self.in_live_region(el) for el in by_text(root, NOT_FOUND_BODY)))
        self.assertEqual(root.find_all("button", templates=True), [])
        self.assertEqual(root.find_all("a", templates=True), [])

    def test_r7_e3_e5_e6_e11_not_found_is_identical_for_every_order_number(self):
        expected = op().render(self.view("A9999"), BANNER)
        self.assertEqual(expected.status, 404)
        self.assertEqual(self.title(parse(expected.body)), NOT_FOUND_TITLE)
        ids = ["A1003", "A1004", "", " A1001", "A1001 ", "a1001", "A" * 1000, "A;1", "%00", "A%31001",
               "A1001/x", "<script>", 'A<script>"']
        for order_id in ids:
            with self.subTest(order_id=order_id[:20]):
                self.assertEqual(op().render(self.view(order_id), BANNER), expected)
        body = expected.body.decode("utf-8")
        for leak in ["A1003", "A1004", "A9999", "a1001", "&lt;script", "C002", "C003"]:
            self.assertNotIn(leak, body)

    def test_r8_could_not_load_page_offers_try_again(self):
        page, root = self.doc(op().LoadError(False))
        self.assertEqual(page.status, 503)
        self.assertEqual(self.title(root), LOAD_TITLE)
        self.assertEqual(self.texts(root, "h1"), [LOAD_TITLE])
        self.assertInOrder(self.one(root, "main").text(), [LOAD_TITLE, LOAD_BODY, "Try again"])
        self.assertTrue(any(self.in_live_region(el) for el in by_text(root, LOAD_BODY)))
        self.assertEqual(self.texts(root, "button"), ["Try again"])
        self.assertNotIn("support@shop.example", page.body.decode("utf-8"))
        self.assertEqual(root.find_all("a"), [])

    def test_r9_e17_support_line_after_three_failed_retries(self):
        page, root = self.doc(op().LoadError(True))
        self.assertEqual(page.status, 503)
        self.assertEqual(self.title(root), LOAD_TITLE)
        self.assertEqual(self.texts(root, "h1"), [LOAD_TITLE])
        self.assertEqual(self.texts(root, "button"), ["Try again"])
        self.assertInOrder(self.one(root, "main").text(), [LOAD_TITLE, LOAD_BODY, SUPPORT])
        lines = by_text(root, SUPPORT)
        self.assertEqual(len(lines), 1)
        self.assertTrue(self.in_live_region(lines[0]))
        # the address is its own element and the final full stop is outside it
        address = [el for el in lines[0].elements() if el.text() == "support@shop.example"]
        self.assertEqual([el.tag for el in address], ["span"])
        # plain text, not a link (PO answer 7)
        self.assertEqual(root.find_all("a"), [])
        self.assertNotIn("mailto:", page.body.decode("utf-8"))

    def test_r10_loading_shows_only_the_loading_message(self):
        page, root = self.doc(op().Loading("A1001"))
        self.assertEqual(page.status, 200)
        self.assertEqual(self.title(root), "Order A1001")
        self.assertEqual(self.texts(root, "h1"), ["Order A1001"])
        loading = by_text(root, LOADING)
        self.assertEqual(len(loading), 1)
        self.assertEqual(loading[0].attrs.get("tabindex"), "-1")
        self.assertTrue(self.in_live_region(loading[0]))
        main = self.one(root, "main").text()
        for data in ["Current status", "Status history", "Shipped", "Updated", TIMEZONE_NOTE, LOAD_BODY, NOT_FOUND_BODY]:
            self.assertNotIn(data, main)

    def test_r10_e4_loading_without_order_number_has_generic_title(self):
        page, root = self.doc(op().Loading(None))
        self.assertEqual(page.status, 200)
        self.assertEqual(self.title(root), "Loading order")
        self.assertEqual(len(root.find_all("h1")), 1)
        self.assertEqual(len(by_text(root, LOADING)), 1)
        self.assertNotIn("Order ", self.title(root))

    def test_r8_r9_loading_shell_embeds_both_error_variants_and_limits(self):
        page, root = self.doc(op().Loading("A1001"))
        templates = {t.attrs.get("id"): t for t in root.find_all("template")}
        self.assertEqual(set(templates), {"tpl-load-error", "tpl-load-error-support"})
        plain = parse(op().render(op().LoadError(False), BANNER).body)
        support = parse(op().render(op().LoadError(True), BANNER).body)
        # the templates are render's own could-not-load markup, not copy written again in JS
        self.assertEqual(templates["tpl-load-error"].text(), self.one(plain, "main").text())
        self.assertEqual(templates["tpl-load-error-support"].text(), self.one(support, "main").text())
        self.assertNotIn(SUPPORT, templates["tpl-load-error"].text())
        self.assertIn(SUPPORT, templates["tpl-load-error-support"].text())
        # 10-second timeout (R8) and 3 failed retries (R9) reach the script from one place
        self.assertEqual(
            [el.attrs["data-load-timeout-seconds"] for el in root.find_all(attrs={"data-load-timeout-seconds": None})],
            ["10"],
        )
        self.assertEqual(
            [el.attrs["data-support-after"] for el in root.find_all(attrs={"data-support-after": None})],
            ["3"],
        )

    def test_r11_signed_out_is_a_redirect_with_no_body_and_no_banner(self):
        page = op().render(op().SignedOut("/orders/A1001"), BANNER)
        self.assertEqual(page.status, 303)
        headers = dict(page.headers)
        self.assertEqual(headers["Location"], "/sign-in?return=/orders/A1001")
        self.assertEqual(page.body, b"")
        self.assertFalse(any("Demo" in value for _, value in page.headers))
        quoted = op().render(op().SignedOut('/orders/A<script>"'), None)
        self.assertEqual(dict(quoted.headers)["Location"], "/sign-in?return=/orders/A%3Cscript%3E%22")
        self.assertEqual(quoted.body, b"")

    def test_r17_every_response_has_the_fixed_security_headers(self):
        views = {**self.body_views(), "signed_out": op().SignedOut("/orders/A1001")}
        for name, view in views.items():
            with self.subTest(state=name):
                page = op().render(view, BANNER)
                for header in SECURITY_HEADERS:
                    self.assertIn(header, page.headers)


class BannerTest(PageTestCase):
    def test_r12_demo_banner_comes_first_in_every_state(self):
        for name, view in self.body_views().items():
            with self.subTest(state=name):
                page, root = self.doc(view)
                aside = self.one(root, "aside", {"aria-label": "Demo notice"})
                self.assertEqual(aside.text(), BANNER)
                main = self.one(root, "main")
                h1 = self.one(root, "h1")
                order = list(root.elements(templates=True))
                self.assertLess(order.index(aside), order.index(main))
                self.assertLess(order.index(aside), order.index(h1))
                self.assertNotIn(main, list(aside.ancestors()))
                self.assertFalse(self.in_live_region(aside))
                # exactly once, also not inside the error templates
                self.assertEqual(page.body.decode("utf-8").count("Demo sign-in"), 1)

    def test_r12_no_banner_without_the_demo_stand_in(self):
        for name, view in self.body_views().items():
            with self.subTest(state=name):
                page, root = self.doc(view, banner=None)
                self.assertEqual(len(root.find_all("h1")), 1)
                self.assertEqual(root.find_all("aside", templates=True), [])
                self.assertNotIn("Demo sign-in", page.body.decode("utf-8"))


class CopyAndContentTest(PageTestCase):
    def test_r14_copy_matches_the_ux_brief_exactly(self):
        self.assertEqual(op().COPY, UX_COPY)
        self.assertEqual(op().COPY["demo.banner"].format(customer_id="C001"), BANNER)
        _, root = self.doc(op().NotFound())
        self.assertIn(NOT_FOUND_BODY, root.text())

    def test_r14_e7_unknown_status_is_shown_as_raw_code_like_a_label(self):
        orders.set_status("A1001", "on_hold", T2)
        orders.set_status("A1002", "shipped", T1)
        _, raw = self.doc(self.view("A1001"))
        _, known = self.doc(self.view("A1002"))
        self.assertEqual(self.texts(raw, "li"), ["on_hold – 9 Oct 2026, 14:05"])
        self.assertInOrder(self.one(raw, "main").text(), ["Current status", "on_hold", "Updated 9 Oct 2026, 14:05"])
        raw_label = by_text(raw, "on_hold")[0]
        known_label = by_text(known, "Shipped")[0]
        self.assertEqual((raw_label.tag, raw_label.attrs), (known_label.tag, known_label.attrs))

    def test_r15_e10_times_are_bangkok_time_inside_time_elements(self):
        orders.set_status("A1001", "delivered", datetime(2026, 10, 9, 18, 30, tzinfo=UTC))
        orders.set_status("A1001", "cancelled", datetime(2026, 12, 31, 17, 0, tzinfo=UTC))
        _, root = self.doc(self.view("A1001"))
        self.assertEqual(self.times(root), [
            ("2027-01-01T00:00:00+07:00", "1 Jan 2027, 00:00"),
            ("2027-01-01T00:00:00+07:00", "1 Jan 2027, 00:00"),
            ("2026-10-10T01:30:00+07:00", "10 Oct 2026, 01:30"),
        ])
        self.assertEqual(self.texts(root, "li"), ["Cancelled – 1 Jan 2027, 00:00", "Delivered – 10 Oct 2026, 01:30"])

    def test_e9_same_time_later_recorded_is_listed_first(self):
        orders.set_status("A1001", "delivered", T2)
        orders.set_status("A1001", "cancelled", T2)
        _, root = self.doc(self.view("A1001"))
        self.assertEqual(self.texts(root, "li"), ["Cancelled – 9 Oct 2026, 14:05", "Delivered – 9 Oct 2026, 14:05"])

    def test_r17_e5_e8_order_number_and_status_code_are_escaped(self):
        evil_id, evil_code = 'A<script>"', '<b>x</b>"'
        orders._ORDERS[evil_id] = {"customer_id": "C001", "status": "pending", "items": []}
        orders.set_status(evil_id, evil_code, T2)
        for name, view in [("loading", op().Loading(evil_id)), ("success", self.view(evil_id))]:
            with self.subTest(state=name):
                page, root = self.doc(view)
                raw = page.body.decode("utf-8")
                self.assertNotIn("A<script>", raw)
                self.assertNotIn("<b>", raw)
                self.assertIn("A&lt;script&gt;&quot;", raw)
                self.assertEqual(self.title(root), 'Order A<script>"')
                self.assertEqual(self.texts(root, "h1"), ['Order A<script>"'])
                self.assertEqual(root.find_all("b", templates=True), [])
        page, root = self.doc(self.view(evil_id))
        self.assertIn("&lt;b&gt;x&lt;/b&gt;&quot;", page.body.decode("utf-8"))
        self.assertEqual(self.texts(root, "li"), ['<b>x</b>" – 9 Oct 2026, 14:05'])


class AccessibilityTest(PageTestCase):
    def test_r16_one_h1_per_state_that_can_take_focus(self):
        for name, view in self.body_views().items():
            with self.subTest(state=name):
                _, root = self.doc(view)
                h1 = self.one(root, "h1")
                self.assertEqual(h1.attrs.get("tabindex"), "-1")

    def test_r16_try_again_is_the_only_focusable_element(self):
        for name, view in self.body_views().items():
            with self.subTest(state=name):
                _, root = self.doc(view)
                expected = ["Try again"] if name.startswith("load_error") else []
                self.assertEqual(self.texts(root, "button"), expected)
                for el in root.elements(templates=True):
                    self.assertNotIn(el.tag, {"a", "input", "select", "textarea"})
                    if "tabindex" in el.attrs:
                        self.assertEqual(el.attrs["tabindex"], "-1")

    def test_r16_markup_has_no_inline_script_or_style(self):
        # the strict CSP allows no inline script or style, so none may be written
        for name, view in self.body_views().items():
            with self.subTest(state=name):
                _, root = self.doc(view)
                self.assertEqual(len(root.find_all("main")), 1)
                self.assertEqual(root.find_all("style", templates=True), [])
                for el in root.elements(templates=True):
                    self.assertNotIn("style", el.attrs)
                    self.assertEqual([a for a in el.attrs if a.startswith("on")], [])
                    if el.tag == "script":
                        self.assertIn("src", el.attrs)
                        self.assertEqual("".join(c for c in el.children if isinstance(c, str)).strip(), "")


class StaticFilesTest(PageTestCase):
    def test_r16_e20_shell_links_a_stylesheet_with_focus_outline_and_wrapping(self):
        _, root = self.doc(op().Loading("A1001"))
        self.assertEqual(
            [el.attrs.get("href") for el in root.find_all("link", {"rel": "stylesheet"})],
            ["/static/order_page.css"],
        )
        css = (APP_DIR / "static" / "order_page.css").read_text(encoding="utf-8")
        self.assertIn("overflow-wrap: anywhere", css)
        self.assertRegex(css, r":focus(-visible)?[^{]*\{[^}]*outline\s*:")

    def test_r8_r9_r10_shell_script_fetches_content_with_timeout_and_counts_retries(self):
        _, root = self.doc(op().Loading("A1001"))
        self.assertEqual([el.attrs.get("src") for el in root.find_all("script")], ["/static/order_page.js"])
        js = (APP_DIR / "static" / "order_page.js").read_text(encoding="utf-8")
        for needed in ["AbortController", "/content/orders/", "tpl-load-error-support", "failedRetries"]:
            self.assertIn(needed, js)
        for banned in ["eval(", "new Function"]:
            self.assertNotIn(banned, js)


if __name__ == "__main__":
    unittest.main()
