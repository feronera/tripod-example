"""Sample HTTP server for the customer order page (thin adapter around app.order_page).

Run: python3 -m app.server [--demo-customer C001]
Without --demo-customer nobody is signed in, so every order page redirects to sign-in.
"""

import argparse
import threading
import time

from app.auth_demo import NO_SIGN_IN, DemoSignIn
from app.orders import status_history


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
