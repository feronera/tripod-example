"""Order status lookup for customers (sample domain, in-memory data)."""

from datetime import datetime, timezone
from typing import NamedTuple

from app.timefmt import time_view

STATUS_LABELS = {
    "pending": "Awaiting payment",
    "paid": "Paid",
    "packing": "Preparing order",
    "shipped": "Shipped",
    "delivered": "Delivered",
    "cancelled": "Cancelled",
}

_ORDERS = {
    "A1001": {"customer_id": "C001", "status": "shipped", "items": ["T-shirt", "Cap"]},
    "A1002": {"customer_id": "C001", "status": "delivered", "items": ["Shoes"]},
    "A1003": {"customer_id": "C002", "status": "pending", "items": ["Bag"]},
    "A1004": {"customer_id": "C003", "status": "cancelled", "items": ["Watch"]},
}


class StatusUpdate(NamedTuple):
    """One recorded status change; immutable once stored."""

    order_id: str
    status: str
    at: datetime  # aware, normalized to UTC


# Append-only, in record order, keyed by order id; lives for the process lifetime.
_HISTORY = {}


class OrderNotFound(LookupError):
    """Raised when an order does not exist or does not belong to the customer."""


def set_status(order_id, status, at=None):
    """Change an order's status and record the update; the only writer of status.

    Returns False when the status is already current (nothing recorded).
    Validation happens before any write, so a rejected call stores nothing.
    """
    order = _ORDERS.get(order_id)
    if order is None:
        raise OrderNotFound("Order not found")
    if at is None:
        at = datetime.now(timezone.utc)
    elif at.tzinfo is None or at.utcoffset() is None:
        raise ValueError("at must be timezone-aware")
    if status == order["status"]:
        return False
    _ORDERS[order_id] = {**order, "status": status}
    _HISTORY.setdefault(order_id, []).append(
        StatusUpdate(order_id, status, at.astimezone(timezone.utc))
    )
    return True


def get_order(order_id):
    """Return a copy of the order, or None when it does not exist (internal use)."""
    order = _ORDERS.get(order_id)
    if order is None:
        return None
    return {"order_id": order_id, **order, "items": list(order["items"])}


def status_label(status):
    """Customer-facing label for a status code; unknown codes are shown as-is."""
    return STATUS_LABELS.get(status, status)


def status_for_customer(customer_id, order_id):
    """Status of one order for the customer who owns it.

    Another customer's order raises the same error as a missing order,
    so the response never reveals that the order exists.
    """
    order = get_order(order_id)
    if order is None or order["customer_id"] != customer_id:
        raise OrderNotFound("Order not found")
    return {
        "order_id": order_id,
        "status": order["status"],
        "label": status_label(order["status"]),
    }


def status_history(customer_id, order_id):
    """Current status and recorded updates (newest first) of one order for its owner.

    Uses the same access check as status_for_customer, so missing, other-customer
    and malformed ids all raise the same OrderNotFound. The result is built fresh
    from plain values, so editing it never changes stored history.
    """
    if not isinstance(customer_id, str) or not isinstance(order_id, str):
        raise OrderNotFound("Order not found")
    current = status_for_customer(customer_id, order_id)
    updates = _HISTORY.get(order_id, [])
    updated = None
    if updates and updates[-1].status == current["status"]:
        updated = time_view(updates[-1].at)
    return {
        **current,
        "updated": updated,
        "history": [
            {"status": u.status, "label": status_label(u.status), "time": time_view(u.at)}
            for u in reversed(updates)
        ],
    }


def orders_for_customer(customer_id):
    """All orders of one customer, sorted by order id."""
    return [
        status_for_customer(customer_id, order_id)
        for order_id in sorted(_ORDERS)
        if _ORDERS[order_id]["customer_id"] == customer_id
    ]
