"""DEMO ONLY sign-in stand-in for the sample order page. Never wire into production.

The sample has no real sign-in layer. When the server starts with `--demo-customer <id>`,
every request is treated as signed in as that customer and every page shows the demo banner.
`identify` and `banner` come from the same object, so one is never on without the other.
Only app/server.py may import this module.
"""

from typing import NamedTuple

from app.order_page import COPY


class DemoSignIn(NamedTuple):  # DEMO ONLY – never wire into production
    customer_id: str

    def identify(self):
        return self.customer_id

    @property
    def banner(self):
        return COPY["demo.banner"].format(customer_id=self.customer_id)


# (identify, banner) when the flag is absent: everyone is signed out and there is no banner.
NO_SIGN_IN = (lambda: None, None)
