"""Preview harness (not part of the repo): seed realistic status changes, then start the sample server."""
import sys
from datetime import datetime, timedelta, timezone
from app import orders, server

BKK = timezone(timedelta(hours=7))
if "--seed" in sys.argv:
    sys.argv.remove("--seed")
    orders.set_status("A1001", "paid", datetime(2026, 10, 6, 9, 12, tzinfo=BKK))
    orders.set_status("A1001", "packing", datetime(2026, 10, 7, 14, 5, tzinfo=BKK))
    orders.set_status("A1001", "shipped", datetime(2026, 10, 8, 8, 40, tzinfo=BKK))
server.main(sys.argv[1:])
