"""Failing tests for change 003, part B (server and demo sign-in), from spec.md and plan.md (Data shape).

Covers app/server.py (route table, handle, parse_args, wire, make_server) and app/auth_demo.py.
Pages are built by part A's render, so the page-content checks here pass once part A is in place.
Part A (page rendering) is tested in tests/test_order_page.py.
"""

import ast
import contextlib
import copy
import http.client
import inspect
import io
import pathlib
import threading
import time
import unittest
from datetime import datetime, timezone
from unittest import mock

from app import orders
from tests._html import parse

APP_DIR = pathlib.Path(__file__).resolve().parent.parent / "app"
UTC = timezone.utc
T1 = datetime(2026, 10, 8, 2, 15, tzinfo=UTC)   # Bangkok 8 Oct 2026, 09:15
T2 = datetime(2026, 10, 9, 7, 5, tzinfo=UTC)    # Bangkok 9 Oct 2026, 14:05
BANNER = "Demo sign-in: Customer C001"
LOAD_TITLE = "We couldn't load your order"


def srv():
    # imported here so a missing module fails each test on its own
    from app import server
    return server


def demo():
    from app import auth_demo
    return auth_demo


def signed_in_as(customer_id):
    return lambda: customer_id


class Calls:
    """Records calls; as a load it delegates to status_history unless `error` is set."""

    def __init__(self, result=None, error=None):
        self.calls = []
        self.result = result
        self.error = error

    def identify(self):
        self.calls.append("identify")
        if self.error is not None:
            raise self.error
        return self.result

    def load(self, customer_id, order_id):
        self.calls.append((customer_id, order_id))
        if self.error is not None:
            raise self.error
        return orders.status_history(customer_id, order_id)


class ServerTestCase(unittest.TestCase):
    def setUp(self):
        # seeded orders and history are undone after each test, so 001/002 tests see the sample data
        for patcher in (mock.patch.dict(orders._ORDERS), mock.patch.dict(orders._HISTORY, clear=True)):
            patcher.start()
            self.addCleanup(patcher.stop)

    def get(self, path, identify=None, load=None, banner=BANNER, method="GET"):
        return srv().handle(
            method,
            path,
            signed_in_as("C001") if identify is None else identify,
            orders.status_history if load is None else load,
            banner,
        )

    def signed_out(self, path, load=None, method="GET"):
        return self.get(path, identify=lambda: None, load=load, banner=None, method=method)

    def title(self, page):
        found = parse(page.body).find_all("title")
        self.assertEqual(len(found), 1)
        return found[0].text()

    def h1(self, page):
        return [el.text() for el in parse(page.body).find_all("h1")]

    def banners(self, page):
        return [el.text() for el in parse(page.body).find_all("aside", {"aria-label": "Demo notice"})]

    def assertRedirectsToSignIn(self, page):
        self.assertEqual(page.status, 303)
        self.assertTrue(dict(page.headers)["Location"].startswith("/sign-in?return="))
        self.assertEqual(page.body, b"")
        self.assertFalse(any("Demo" in value for _, value in page.headers))


class RouteTest(ServerTestCase):
    def test_r1_shell_route_serves_the_loading_page(self):
        page = self.get("/orders/A1001")
        self.assertEqual(page.status, 200)
        self.assertEqual(self.title(page), "Order A1001")
        self.assertEqual(self.h1(page), ["Order A1001"])
        root = parse(page.body)
        self.assertIn("Loading your order…", root.text())
        self.assertNotIn("Shipped", root.text())

    def test_r1_content_route_serves_the_order_page(self):
        orders.set_status("A1001", "paid", T1)
        orders.set_status("A1001", "delivered", T2)
        page = self.get("/content/orders/A1001")
        self.assertEqual(page.status, 200)
        self.assertEqual(self.h1(page), ["Order A1001"])
        self.assertEqual(
            [el.text() for el in parse(page.body).find_all("li")],
            ["Delivered – 9 Oct 2026, 14:05", "Paid – 8 Oct 2026, 09:15"],
        )

    def test_r1_routes_never_write_or_use_other_domain_functions(self):
        orders.set_status("A1001", "delivered", T2)
        writes = mock.patch.object(orders, "set_status", side_effect=AssertionError("route wrote data"))
        lists = mock.patch.object(orders, "orders_for_customer", side_effect=AssertionError("not allowed"))
        counts = mock.patch.object(orders, "status_counts", side_effect=AssertionError("not allowed"))
        with writes, lists, counts:
            statuses = [
                self.get("/orders/A1001").status,
                self.get("/content/orders/A1001").status,
                self.get("/content/orders/A1002").status,
                self.get("/content/orders/A9999").status,
                self.get("/nope").status,
                self.signed_out("/orders/A1001").status,
                self.get("/content/orders/A1001", method="POST").status,
            ]
        self.assertEqual(statuses, [200, 200, 200, 404, 404, 303, 405])

        tree = ast.parse((APP_DIR / "server.py").read_text(encoding="utf-8"))
        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module == "app.orders":
                imported |= {alias.name for alias in node.names}
            if isinstance(node, ast.ImportFrom) and node.module == "app":
                self.assertNotIn("orders", {alias.name for alias in node.names})
            if isinstance(node, ast.Import):
                self.assertNotIn("app.orders", {alias.name for alias in node.names})
        self.assertLessEqual(imported, {"status_history", "OrderNotFound"})
        used = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)}
        used |= {n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)}
        forbidden = {"get_order", "set_status", "orders_for_customer", "status_counts", "status_for_customer"}
        self.assertEqual(used & forbidden, set())

    def test_r2_e12_query_string_cannot_choose_the_customer(self):
        # handle takes no headers or cookies at all; the customer id comes only from identify
        self.assertEqual(
            list(inspect.signature(srv().handle).parameters),
            ["method", "path", "identify", "load", "banner"],
        )
        calls = Calls()
        own = self.get("/content/orders/A1001?customer_id=C002", load=calls.load)
        self.assertEqual(own.status, 200)
        self.assertEqual(self.h1(own), ["Order A1001"])
        self.assertIn("Shipped", parse(own.body).text())
        other = self.get("/content/orders/A1003?customer_id=C002", load=calls.load)
        self.assertEqual(other, self.get("/content/orders/A9999"))
        self.assertEqual(other.status, 404)
        self.assertEqual(calls.calls, [("C001", "A1001"), ("C001", "A1003")])

    def test_r3_e13_signed_out_redirects_for_every_order_without_loading(self):
        calls = Calls()
        pages = {}
        for order_id in ["A1001", "A1003", "A9999"]:
            with self.subTest(order_id=order_id):
                shell = self.signed_out(f"/orders/{order_id}", load=calls.load)
                self.assertRedirectsToSignIn(shell)
                self.assertEqual(dict(shell.headers)["Location"], f"/sign-in?return=/orders/{order_id}")
                self.assertRedirectsToSignIn(self.signed_out(f"/content/orders/{order_id}", load=calls.load))
                pages[order_id] = shell
        self.assertEqual(calls.calls, [])
        # the responses differ only in the quoted path
        without_location = {
            order_id: (page.status, tuple(h for h in page.headers if h[0] != "Location"), page.body)
            for order_id, page in pages.items()
        }
        self.assertEqual(without_location["A1003"], without_location["A1001"])
        self.assertEqual(without_location["A9999"], without_location["A1001"])
        self.assertEqual(self.get("/content/orders/A1001", load=calls.load).status, 200)
        self.assertEqual(calls.calls, [("C001", "A1001")])

    def test_r11_return_path_is_rebuilt_from_the_route_and_quoted(self):
        self.assertEqual(
            dict(self.signed_out("/orders/A1001?next=//evil.example").headers)["Location"],
            "/sign-in?return=/orders/A1001",
        )
        self.assertEqual(
            dict(self.signed_out('/orders/A<script>"').headers)["Location"],
            "/sign-in?return=/orders/A%3Cscript%3E%22",
        )

    def test_e5_unparseable_request_target_gets_the_not_found_page(self):
        # urlsplit raises ValueError on this target; review 003 Major 1
        page = self.get("http://[/orders/A1001")
        self.assertEqual(page.status, 404)
        self.assertEqual(self.title(page), "Order not found")
        self.assertEqual(self.h1(page), ["Order not found"])
        self.assertEqual(self.banners(page), [BANNER])
        self.assertNotIn("Location", dict(page.headers))
        self.assertEqual(page, self.get("/content/orders/A9999"))

    def test_r11_e19_signed_out_sign_in_path_is_not_found_not_a_redirect(self):
        # /sign-in used to redirect to /sign-in?return=/, which redirected to itself; review 003 Major 1
        calls = Calls()
        page = self.signed_out("/sign-in?return=/orders/A1001", load=calls.load)
        self.assertEqual(page.status, 404)
        self.assertEqual(self.title(page), "Order not found")
        self.assertEqual(self.h1(page), ["Order not found"])
        self.assertEqual(self.banners(page), [])
        self.assertNotIn("Location", dict(page.headers))
        self.assertEqual(calls.calls, [])

    def test_e19_session_expired_before_try_again(self):
        session = {"customer": "C001"}
        identify = lambda: session["customer"]  # noqa: E731
        first = self.get("/content/orders/A1001", identify=identify)
        self.assertEqual(first.status, 200)
        self.assertIn("Shipped", parse(first.body).text())
        session["customer"] = None
        retry = self.get("/content/orders/A1001", identify=identify)
        self.assertRedirectsToSignIn(retry)
        self.assertNotIn(b"Shipped", retry.body)

    def test_e14_stand_in_failure_is_the_same_for_every_order(self):
        calls = Calls(error=RuntimeError("stand-in down"))
        pages = [self.get(f"/content/orders/{order_id}", identify=calls.identify, load=calls.load)
                 for order_id in ["A1001", "A1003", "A9999"]]
        self.assertEqual(pages[0].status, 503)
        self.assertEqual(self.h1(pages[0]), [LOAD_TITLE])
        self.assertEqual(self.banners(pages[0]), [BANNER])
        self.assertEqual(pages[1], pages[0])
        self.assertEqual(pages[2], pages[0])
        self.assertEqual(calls.calls, ["identify", "identify", "identify"])

    def test_r7_e3_e5_e6_e11_not_found_is_identical_for_every_raw_order_number(self):
        expected = self.get("/content/orders/A9999")
        self.assertEqual(expected.status, 404)
        self.assertEqual(self.title(expected), "Order not found")
        # raw path segments: not URL-decoded, not trimmed, not case-folded
        segments = ["A1003", "A1004", "a1001", "%20A1001", "A1001%20", " A1001", "A%31001", "A;1", "%00",
                    "%3Cscript%3E", "<script>", 'A"1', "A" * 1000]
        for segment in segments:
            with self.subTest(segment=segment[:20]):
                self.assertEqual(self.get(f"/content/orders/{segment}"), expected)
        for path in ["/content/orders/A1001/x", "/nope", "/", "/orders", "/content/orders"]:
            with self.subTest(path=path):
                self.assertEqual(self.get(path), expected)
        # the same order number, written plainly, is found
        self.assertEqual(self.get("/content/orders/A1001").status, 200)

    def test_e4_no_order_number_in_the_path(self):
        self.assertEqual(self.get("/content/orders/"), self.get("/content/orders/A9999"))
        shell = self.get("/orders/")
        self.assertEqual(shell.status, 200)
        self.assertEqual(self.title(shell), "Loading order")

    def test_e15_non_get_methods_are_rejected_without_touching_data(self):
        orders.set_status("A1001", "delivered", T2)
        before = (copy.deepcopy(orders._ORDERS), copy.deepcopy(orders._HISTORY))
        calls = Calls(result="C001")
        for method in ["POST", "PUT", "DELETE", "PATCH"]:
            for path in ["/orders/A1001", "/content/orders/A1001"]:
                with self.subTest(method=method, path=path):
                    page = self.get(path, identify=calls.identify, load=calls.load, method=method)
                    self.assertEqual(page.status, 405)
                    self.assertIn(("Allow", "GET"), page.headers)
        self.assertEqual(calls.calls, [])
        self.assertEqual((orders._ORDERS, orders._HISTORY), before)
        self.assertEqual(self.get("/content/orders/A1001", identify=calls.identify, load=calls.load).status, 200)
        self.assertEqual(calls.calls, ["identify", ("C001", "A1001")])

    def test_r4_no_request_changes_orders_or_history(self):
        orders.set_status("A1001", "paid", T1)
        orders.set_status("A1001", "delivered", T2)
        before = (copy.deepcopy(orders._ORDERS), copy.deepcopy(orders._HISTORY))
        failing = Calls(error=RuntimeError("down"))
        statuses = [
            self.get("/orders/A1001").status,
            self.get("/content/orders/A1001").status,
            self.get("/content/orders/A1002").status,
            self.get("/content/orders/A1003").status,
            self.get("/content/orders/A1001", load=failing.load).status,
            self.signed_out("/content/orders/A1001").status,
            self.get("/content/orders/A1001", method="DELETE").status,
        ]
        self.assertEqual(statuses, [200, 200, 200, 404, 503, 303, 405])
        self.assertEqual((orders._ORDERS, orders._HISTORY), before)

    def test_r16_static_files_come_from_a_fixed_allowlist(self):
        for name, kind in [("order_page.js", "text/javascript"), ("order_page.css", "text/css")]:
            with self.subTest(file=name):
                # no data in static files, so no sign-in is needed
                page = self.signed_out(f"/static/{name}")
                self.assertEqual(page.status, 200)
                self.assertTrue(dict(page.headers)["Content-Type"].startswith(kind))
                self.assertEqual(page.body, (APP_DIR / "static" / name).read_bytes())
        expected = self.get("/content/orders/A9999")
        for path in ["/static/../server.py", "/static/%2e%2e/server.py", "/static/server.py",
                     "/static/order_page.js/x", "/static/", "/app/static/order_page.js"]:
            with self.subTest(path=path):
                self.assertEqual(self.get(path), expected)


class DemoSignInTest(ServerTestCase):
    def test_r13_no_flag_means_nobody_is_signed_in_and_no_banner(self):
        identify, load, banner = srv().wire(srv().parse_args([]))
        self.assertIsNone(identify())
        self.assertIsNone(banner)
        self.assertEqual(load("C001", "A1002")["label"], "Delivered")
        page = srv().handle("GET", "/orders/A1001", identify, load, banner)
        self.assertRedirectsToSignIn(page)

    def test_r12_r13_demo_flag_signs_in_and_always_shows_the_banner(self):
        identify, load, banner = srv().wire(srv().parse_args(["--demo-customer", "C001"]))
        self.assertEqual(identify(), "C001")
        self.assertEqual(banner, BANNER)
        orders.set_status("A1001", "delivered", T2)
        for path in ["/orders/A1001", "/content/orders/A1001", "/content/orders/A1002", "/content/orders/A9999"]:
            with self.subTest(path=path):
                self.assertEqual(self.banners(srv().handle("GET", path, identify, load, banner)), [BANNER])

    def test_r12_r13_stand_in_and_banner_come_from_one_object(self):
        stand_in = demo().DemoSignIn("C002")
        self.assertEqual(stand_in.identify(), "C002")
        self.assertEqual(stand_in.banner, "Demo sign-in: Customer C002")
        no_identify, no_banner = demo().NO_SIGN_IN
        self.assertIsNone(no_identify())
        self.assertIsNone(no_banner)
        identify, _, banner = srv().wire(srv().parse_args(["--demo-customer", "C002"]))
        self.assertEqual((identify(), banner), ("C002", "Demo sign-in: Customer C002"))

    def test_r13_fault_flags_need_the_demo_customer_flag(self):
        for argv in [["--demo-fail-loads", "1"], ["--demo-delay-seconds", "1"]]:
            with self.subTest(argv=argv):
                with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as caught:
                    srv().parse_args(argv)
                self.assertEqual(caught.exception.code, 2)
        args = srv().parse_args(["--demo-customer", "C001", "--demo-fail-loads", "1", "--demo-delay-seconds", "0"])
        self.assertEqual(srv().wire(args)[2], BANNER)

    def test_r8_r9_demo_fail_loads_fails_the_next_n_loads(self):
        identify, load, banner = srv().wire(srv().parse_args(["--demo-customer", "C001", "--demo-fail-loads", "2"]))
        pages = [srv().handle("GET", "/content/orders/A1001", identify, load, banner) for _ in range(3)]
        self.assertEqual([p.status for p in pages], [503, 503, 200])
        self.assertEqual(self.h1(pages[0]), [LOAD_TITLE])
        self.assertEqual(self.h1(pages[2]), ["Order A1001"])

    def test_r8_demo_delay_seconds_waits_before_loading(self):
        identify, load, banner = srv().wire(srv().parse_args(["--demo-customer", "C001", "--demo-delay-seconds", "0.2"]))
        start = time.monotonic()
        page = srv().handle("GET", "/content/orders/A1001", identify, load, banner)
        self.assertGreaterEqual(time.monotonic() - start, 0.2)
        self.assertEqual(page.status, 200)

    def test_r13_only_the_server_imports_the_demo_stand_in(self):
        importers = set()
        for path in APP_DIR.rglob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                names = set()
                if isinstance(node, ast.ImportFrom):
                    names = {node.module} | {f"{node.module}.{a.name}" for a in node.names}
                elif isinstance(node, ast.Import):
                    names = {a.name for a in node.names}
                if "app.auth_demo" in names:
                    importers.add(path.relative_to(APP_DIR).as_posix())
        self.assertEqual(importers, {"server.py"})
        self.assertEqual(srv().wire(srv().parse_args(["--demo-customer", "C001"]))[2], BANNER)

    def test_r13_stand_in_is_labelled_demo_only(self):
        source = (APP_DIR / "auth_demo.py").read_text(encoding="utf-8")
        self.assertRegex(source, r"(?i)demo[ -]only")
        self.assertRegex(ast.get_docstring(ast.parse(source)) or "", r"(?i)demo[ -]only")
        self.assertEqual(demo().DemoSignIn("C001").banner, BANNER)
        self.assertEqual(srv().wire(srv().parse_args(["--demo-customer", "C001"]))[0](), "C001")

    def test_r13_server_binds_localhost_by_default(self):
        args = srv().parse_args([])
        self.assertEqual(args.host, "127.0.0.1")
        self.assertIsNone(args.demo_customer)
        self.assertEqual(srv().parse_args(["--demo-customer", "C001"]).demo_customer, "C001")


class SmokeTest(ServerTestCase):
    """One real ThreadingHTTPServer on port 0, so headers and cookies reach the handler."""

    def start(self, argv):
        httpd = srv().make_server(srv().parse_args([*argv, "--port", "0"]))
        thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        thread.start()

        def stop():
            httpd.shutdown()
            httpd.server_close()
            thread.join(5)

        self.addCleanup(stop)
        return httpd.server_address[:2]

    def request(self, address, method, path, headers=None):
        conn = http.client.HTTPConnection(*address, timeout=5)
        try:
            conn.request(method, path, headers=headers or {})
            response = conn.getresponse()
            return response.status, dict(response.getheaders()), response.read()
        finally:
            conn.close()

    def test_r2_e12_headers_and_cookies_cannot_choose_the_customer(self):
        address = self.start(["--demo-customer", "C001"])
        self.assertEqual(address[0], "127.0.0.1")
        forged = {"X-Customer-Id": "C002", "Cookie": "customer_id=C002"}
        with contextlib.redirect_stderr(io.StringIO()) as log:
            own = self.request(address, "GET", "/content/orders/A1001?customer_id=C002", forged)
            other = self.request(address, "GET", "/content/orders/A1003", forged)
            missing = self.request(address, "GET", "/content/orders/A9999")
            posted = self.request(address, "POST", "/content/orders/A1001")
        self.assertEqual(own[0], 200)
        self.assertEqual(own[1]["Content-Type"], "text/html; charset=utf-8")
        self.assertEqual([el.text() for el in parse(own[2]).find_all("h1")], ["Order A1001"])
        self.assertIn("Shipped", parse(own[2]).text())
        self.assertEqual(other[0], 404)
        self.assertEqual(other[2], missing[2])
        self.assertEqual(posted[0], 405)
        self.assertEqual(posted[1]["Allow"], "GET")
        # the log has the method but never the path, order id or customer id (AGENTS.md rule 6)
        logged = log.getvalue()
        self.assertIn("GET", logged)
        for secret in ["A1001", "A1003", "A9999", "C002", "/content/orders"]:
            self.assertNotIn(secret, logged)

    def test_r11_without_the_flag_every_order_redirects_to_sign_in(self):
        address = self.start([])
        with contextlib.redirect_stderr(io.StringIO()):
            responses = [self.request(address, "GET", f"/orders/{order_id}") for order_id in ["A1001", "A1003", "A9999"]]
        self.assertEqual([r[0] for r in responses], [303, 303, 303])
        self.assertEqual(
            [r[1]["Location"] for r in responses],
            ["/sign-in?return=/orders/A1001", "/sign-in?return=/orders/A1003", "/sign-in?return=/orders/A9999"],
        )
        self.assertEqual([r[2] for r in responses], [b"", b"", b""])


if __name__ == "__main__":
    unittest.main()
