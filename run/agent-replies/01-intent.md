I've written `docs/changes/001-order-history/intent.md`. It is still `Status: draft`, and I edited nothing else.

**I set the risk to high, not medium.** By `docs/risk-tiers.md`, rolling back means losing the order history recorded since release, so the "roll back without data loss" question is a "no". That alone makes it high, even though the PO accepts the loss. The other three answers: no regulation, customers see it, and no personal data (per the PO). Open questions asks whether a rollback could hide the feature but keep the data, which would make it medium. If the tier changes after gate 1, gate 1 has to be signed again.

**Gate 1 check (`docs/gates.md`):**
- **Problem and users:** pass. The evidence from the log is real and the users are defined.
- **Risk section:** pass. It answers all 4 questions.
- **Success measure:** only partly passes. It is a number with a current value and a target (28 → 14 per week within 30 days), but the 28 is demo data. The real figure is listed under Open questions.
- **SuperDev's "can it be measured?" check:** at risk. The 4 "Order status not showing" chats in the log fall on the same morning as 5 `delivery_date is None` errors for 3 customers. Some of the chats may be caused by that bug, which is out of scope, not by the missing history. If so, fixing the bug separately would also move the measure, so the target of 14 may not be credible. This is listed under Open questions.

Two more items under Open questions:
- Whether an order history tied to a customer ID counts as personal data under the team's data policy.
- `pod.yml` gives SuperBiz and the escalation signer (Lee) the same GitHub login (`hx-natthawat`). A PR approval may therefore not show two different people.

**Next steps:**
1. SuperBiz reviews intent.md, then runs `scripts/gate.sh docs/changes/001-order-history 1`.
2. Ask SuperDev to cross-check that it can be built and measured (especially the overlap with the bug), then run the same command.
3. Check the result with `scripts/gate-check.sh docs/changes/001-order-history`.
