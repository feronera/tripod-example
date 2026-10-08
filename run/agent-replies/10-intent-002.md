I've written `docs/changes/002-status-report/intent.md` from your answers. It is still `Status: draft`, and I didn't sign anything.

**Risk: low.** There's no regulation, customers never see the report, it can be rolled back in minutes because it only reads data and stores nothing, and it shows counts only, with no personal data. The work stays in `app/orders.py`, which isn't on the sensitive-paths list in `docs/risk-paths`.

**Gate 1 questions:**
- **Problem and users:** passes, with one caveat. The users are clear, but the only evidence is "about 15 minutes a day" from demo data.
- **Success measure:** passes. It has a current value (~15 min/day), a target (under 1 min) and a deadline (2 weeks after release). How it will be measured after release isn't decided yet.
- **Risk:** passes. All 4 questions are answered.
- **SuperDev (one change, measurable?):** likely yes, since it's one read-only function. SuperDev still needs to confirm how the time will be measured.

**Open questions in the file:**
1. Can the demo-data figure of 15 minutes be the starting value, or should the support lead confirm it?
2. How will "under 1 minute" be measured: the support lead reports it, or someone times it?
3. Some orders may have a status code that has no label in `STATUS_LABELS`. Should they be counted under the raw code, grouped as "other", or left out?

**Next steps:**
1. SuperBiz reviews intent.md, then runs `scripts/gate.sh docs/changes/002-status-report 1`.
2. SuperDev cross-checks it (can it be built and measured?), then runs the same command.
3. Check the result with `scripts/gate-check.sh docs/changes/002-status-report`.
