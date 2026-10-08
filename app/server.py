"""Sample HTTP server for the customer order page (thin adapter around app.order_page).

Run: python3 -m app.server [--demo-customer C001]
Without --demo-customer nobody is signed in, so every order page redirects to sign-in.
"""

import argparse
import pathlib
import re
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit

from app.auth_demo import NO_SIGN_IN, DemoSignIn
from app.order_page import LoadError, Loading, NotFound, Page, SignedOut, render, resolve
from app.orders import status_history

STATIC_DIR = pathlib.Path(__file__).resolve().parent / "static"
# Fixed allowlist: no filesystem path is ever built from the URL.
STATIC_FILES = {
    "/static/order_page.js": ("order_page.js", "text/javascript; charset=utf-8"),
    "/static/order_page.css": ("order_page.css", "text/css; charset=utf-8"),
}
# Order id is the raw path segment: not URL-decoded, trimmed or case-folded.
ROUTES = (
    ("shell", re.compile(r"^/orders/([^/]*)$")),
    ("content", re.compile(r"^/content/orders/([^/]*)$")),
)
SIGN_IN_RETURN_FALLBACK = "/"


def route(path):
    """(kind, order_id) for a raw request path; the query string is dropped."""
    path = urlsplit(path).path
    if path in STATIC_FILES:
        return "static", None
    for kind, pattern in ROUTES:
        match = pattern.match(path)
        if match:
            return kind, match.group(1)
    return "other", None


def handle(method, path, identify, load, banner):
    """The Page for one request. Takes no headers or cookies: the customer comes only from identify."""
    if method != "GET":
        # never calls identify or load
        page = render(NotFound(), None)
        return Page(405, (*page.headers, ("Allow", "GET")), b"")
    kind, order_id = route(path)
    if kind == "static":
        return _static(urlsplit(path).path)
    if kind == "content":
        view = resolve(identify, order_id, load)
    else:
        view = _signed_in_view(identify, Loading(order_id or None) if kind == "shell" else NotFound())
    if isinstance(view, SignedOut):
        # rebuilt from the matched route, never from the query
        view = SignedOut(f"/orders/{order_id}" if kind in ("shell", "content") else SIGN_IN_RETURN_FALLBACK)
        return render(view, None)
    return render(view, banner)


def _signed_in_view(identify, view):
    """`view` when someone is signed in; the sign-in check runs first, as in resolve."""
    try:
        customer_id = identify()
    except Exception:
        return LoadError(False)
    if customer_id is None:
        return SignedOut(SIGN_IN_RETURN_FALLBACK)
    return view


def _static(path):
    name, content_type = STATIC_FILES[path]
    headers = tuple((k, content_type if k == "Content-Type" else v) for k, v in render(NotFound(), None).headers)
    return Page(200, headers, (STATIC_DIR / name).read_bytes())


def parse_args(argv=None):
    """Command-line flags; the demo fault switches are accepted only with --demo-customer."""
    parser = argparse.ArgumentParser(prog="python3 -m app.server", description=__doc__.splitlines()[0])
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--demo-customer", metavar="ID",
                        help="DEMO ONLY: treat every request as signed in as this customer")
    parser.add_argument("--demo-fail-loads", type=int, metavar="N",
                        help="DEMO ONLY: the next N order loads fail")
    parser.add_argument("--demo-delay-seconds", type=float, metavar="S",
                        help="DEMO ONLY: wait S seconds before each order load")
    args = parser.parse_args(argv)
    if args.demo_customer is None:
        for flag, value in [("--demo-fail-loads", args.demo_fail_loads),
                            ("--demo-delay-seconds", args.demo_delay_seconds)]:
            if value is not None:
                parser.error(f"{flag} needs --demo-customer")
    return args


def wire(args):
    """(identify, load, banner) for these flags; identify and banner come from one source."""
    if args.demo_customer is None:
        identify, banner = NO_SIGN_IN
    else:
        stand_in = DemoSignIn(args.demo_customer)
        identify, banner = stand_in.identify, stand_in.banner
    return identify, _demo_faults(status_history, args.demo_fail_loads, args.demo_delay_seconds), banner


def _demo_faults(load, fail_loads, delay_seconds):
    """Wrap load with the demo-only fault switches; unchanged when neither is set."""
    if not fail_loads and not delay_seconds:
        return load
    lock = threading.Lock()
    remaining = [fail_loads or 0]

    def faulty_load(customer_id, order_id):
        if delay_seconds:
            time.sleep(delay_seconds)
        with lock:
            fail = remaining[0] > 0
            if fail:
                remaining[0] -= 1
        if fail:
            raise RuntimeError("demo load failure")
        return load(customer_id, order_id)

    return faulty_load


def make_server(args):
    """A ThreadingHTTPServer for these flags (not started)."""
    identify, load, banner = wire(args)

    class OrderPageHandler(BaseHTTPRequestHandler):
        """Pass-through: all logic is in handle(). Logs never contain the path or ids (AGENTS.md rule 6)."""

        def _respond(self):
            page = handle(self.command, self.path, identify, load, banner)
            self.send_response(page.status)
            for name, value in page.headers:
                self.send_header(name, value)
            self.send_header("Content-Length", str(len(page.body)))
            self.end_headers()
            if self.command != "HEAD":
                self.wfile.write(page.body)
            self.log_message("%s %s %d", self.command, route(self.path)[0], page.status)

        do_GET = do_HEAD = do_POST = do_PUT = do_DELETE = do_PATCH = do_OPTIONS = _respond

        def log_request(self, code="-", size="-"):
            pass  # the default request log line contains the path

        def log_error(self, format, *args):
            sys.stderr.write("request error\n")

        def log_message(self, format, *args):
            sys.stderr.write(f"{self.log_date_time_string()} {format % args}\n")

    return ThreadingHTTPServer((args.host, args.port), OrderPageHandler)


def main(argv=None):
    args = parse_args(argv)
    httpd = make_server(args)
    host, port = httpd.server_address[:2]
    print(f"Serving on http://{host}:{port}/orders/<order id>", file=sys.stderr)
    if args.demo_customer is not None:
        print("DEMO ONLY: demo sign-in stand-in is on", file=sys.stderr)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()


if __name__ == "__main__":
    main()
