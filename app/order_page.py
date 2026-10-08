"""Customer order status page (change 003): view records, copy and pure rendering.

Everything a customer can see is produced here from plain values. The server only
matches the path, calls one function and writes the returned Page.
"""

import html
from string import Formatter
from typing import NamedTuple
from urllib.parse import quote

# R8, R9: defined once here; they reach the script through data- attributes.
LOAD_TIMEOUT_SECONDS = 10
SUPPORT_AFTER_FAILED_RETRIES = 3

# Copy from ux-brief.md "Copy", exactly (R14).
COPY = {
    "demo.banner": "Demo sign-in: Customer {customer_id}",
    "page.title": "Order {order_id}",
    "page.loading_title": "Loading order",
    "page.loading": "Loading your order…",
    "status.heading": "Current status",
    "status.updated": "Updated {datetime}",
    "history.heading": "Status history",
    "history.order": "Newest first",
    "history.row": "{status_label} – {datetime}",
    "history.empty": "No status updates are listed for this order.",
    "history.earlier_note": "Earlier updates are not listed.",
    "history.timezone": "Times are shown in Bangkok time (GMT+7).",
    "error.not_found.title": "Order not found",
    "error.not_found.body": (
        "We couldn't find this order. Open the order link in your order confirmation email, "
        "and check that you are signed in with the account you used to place the order."
    ),
    "error.load.title": "We couldn't load your order",
    "error.load.body": "Something went wrong. Check your connection and try again in a moment.",
    "error.load.retry": "Try again",
    "error.load.support": "Still not working? Contact support at support@shop.example.",
}

SUPPORT_ADDRESS = "support@shop.example"


class Loading(NamedTuple):
    order_id: str | None  # None → title "Loading order" (E4)


class Success(NamedTuple):
    order_id: str
    label: str
    updated: dict | None  # {"text", "iso"}; None when the latest update is not the current status (E2)
    history: tuple  # ((label, {"text", "iso"}), ...), newest first, non-empty


class Empty(NamedTuple):
    order_id: str
    label: str


class NotFound(NamedTuple):
    """No fields: nothing order-specific can be shown (R7)."""


class LoadError(NamedTuple):
    show_support: bool  # True only after SUPPORT_AFTER_FAILED_RETRIES failed retries (R9)


class SignedOut(NamedTuple):
    return_path: str  # built by the server from the matched route, never from the query


class Page(NamedTuple):
    status: int
    headers: tuple
    body: bytes


HEADERS = (
    ("Content-Type", "text/html; charset=utf-8"),
    ("Cache-Control", "no-store"),
    ("X-Content-Type-Options", "nosniff"),
    ("Referrer-Policy", "no-referrer"),
    ("Content-Security-Policy",
     "default-src 'none'; script-src 'self'; style-src 'self'; connect-src 'self'; frame-ancestors 'none'"),
)


def _esc(value):
    """The one way a value enters HTML (R17)."""
    return html.escape(str(value), quote=True)


def _fill(key, **markup):
    """COPY[key] as HTML: its own text escaped, each {field} replaced by ready markup."""
    out = []
    for literal, field, _, _ in Formatter().parse(COPY[key]):
        out.append(_esc(literal))
        if field is not None:
            out.append(markup[field])
    return "".join(out)


def _h1(text):
    return f'<h1 tabindex="-1">{_esc(text)}</h1>'


def _document(title, main, banner, shell=""):
    aside = "" if banner is None else f'<aside aria-label="Demo notice"><p>{_esc(banner)}</p></aside>\n'
    return (
        "<!doctype html>\n"
        '<html lang="en">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f"<title>{_esc(title)}</title>\n"
        '<link rel="stylesheet" href="/static/order_page.css">\n'
        "</head>\n<body>\n"
        f"{aside}"
        f"<main{shell and ' ' + shell}>\n{main}\n</main>\n"
        "</body>\n</html>\n"
    )


def _not_found_main(view):
    return "\n".join([
        _h1(COPY["error.not_found.title"]),
        f'<div role="status"><p>{_esc(COPY["error.not_found.body"])}</p></div>',
    ])


def _load_error_main(view):
    lines = [f'<p>{_esc(COPY["error.load.body"])}</p>']
    if view.show_support:
        before, _, after = COPY["error.load.support"].partition(SUPPORT_ADDRESS)
        lines.append(f"<p>{_esc(before)}<span>{_esc(SUPPORT_ADDRESS)}</span>{_esc(after)}</p>")
    return "\n".join([
        _h1(COPY["error.load.title"]),
        f'<div role="status">{"".join(lines)}</div>',
        f'<button type="button" data-action="retry">{_esc(COPY["error.load.retry"])}</button>',
    ])


def _page(status, title, main, banner):
    return Page(status, HEADERS, _document(title, main, banner).encode("utf-8"))


def _render_not_found(view, banner):
    return _page(404, COPY["error.not_found.title"], _not_found_main(view), banner)


def _render_load_error(view, banner):
    return _page(503, COPY["error.load.title"], _load_error_main(view), banner)


def _render_signed_out(view, banner):
    # R11, R12: a redirect with no body, so no banner and no order data
    location = "/sign-in?return=" + quote(view.return_path, safe="/")
    return Page(303, HEADERS + (("Location", location),), b"")


_RENDER = {
    NotFound: _render_not_found,
    LoadError: _render_load_error,
    SignedOut: _render_signed_out,
}


def render(view, banner):
    """The Page for one view; `banner` is the demo banner text, or None without the stand-in."""
    return _RENDER[type(view)](view, banner)
