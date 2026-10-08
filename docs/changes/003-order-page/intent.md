# Intent: Order status page for customers

Status: draft

## Problem
Change 001 delivered the order status history as a function (`app/orders.py`), but customers still cannot see it:
there is no order page. Customers who want to know where their order is still have to contact support.

Evidence:
- Change 001's `ux-brief.md` (`docs/changes/001-order-history/ux-brief.md`) already defines the page: its screen,
  states, copy and accessibility notes.
- Change 001's `review.md` left one Major open: the page states (E13–E18, and with them R9–R13) have no proof because
  the page was not built. Its `acceptance.md` accepted the function only on the condition that a page demo of
  R9–R13 and E13–E18 is run and recorded before customers see the page.
- The Success measure of change 001 (28 chats per week, demo data) cannot move while customers have no page.

## Users
- Customers viewing one of their own orders, arriving from the order link in their order confirmation email.
- Out of scope: support staff.

## Success measure
1. "Where is my order" plus "order status not showing" chats per week, from the support tool weekly report (the same
   measure as change 001).
   - Current: 28 per week (demo data, as in change 001).
   - Target: 14 per week within 30 days after this page is released.
2. For this change: every state in the 001 ux-brief is shown on the page.
   - Current: 0 (there is no page).
   - Target: all of them, shown in a recorded demo before release: empty, loading, success, not found, could not load
     (including the 10-second timeout and the support line after 3 failed retries), and not signed in / session
     expired. This also closes the open Major from change 001.

## Risk
Risk: high

1. Law or regulation: no. The PO confirmed no regulation is involved.
2. Customers see the result directly: yes. The page is customer-facing.
3. Rollback within minutes without data loss: yes. The PO says the page can be reverted within minutes, and the page
   stores and changes no data.
4. Personal or sensitive data: no by the PO's answer. The page shows the customer's own order and its status history,
   with no payment or personal fields.

By these 4 answers alone the tier would be medium. This draft sets high because the page is the first place in this
repo that turns a signed-in customer id into access to order data, and it adds a demo stand-in for the signed-in
identity. `docs/pod-charter.md` lists "Change access permissions or authentication" as work the pod may not do alone
(always high). Following `docs/risk-tiers.md` ("if unsure, choose the higher tier"), this draft takes high; see
Open questions.

## Constraints
- Python standard library only. `http.server` is fine for this sample.
- Follow the copy, states and accessibility notes in `docs/changes/001-order-history/ux-brief.md`.
- A customer must never see another customer's order.
- Sign-in is outside this repo. The page receives the signed-in customer id from a trusted layer. The sample uses a
  clearly marked demo stand-in for that layer.
- The page only reads. It stores and changes no data.

## Open questions
- Risk tier: the 4 questions give medium, the pod charter's "access permissions or authentication" item gives high.
  Do SuperBiz and SuperDev agree with high? If the pod decides the ownership check reuses the existing rule in
  `app/orders.py` and does not change access permissions, the tier could be medium. If the tier changes after gate 1,
  gate 1 must be signed again. Note that if the demo stand-in lives under a path matched by `app/auth*` in
  `docs/risk-paths`, the change is high at merge time whatever this file says.
- If high: the escalation signer at gates 2 and 4 is the person named in `pod.yml`. Are they available for this change?
- How is the demo stand-in for the signed-in customer id kept out of production, and how will the real trusted layer
  pass the customer id? (SuperDev, in plan.md.)
- Change 001's spec decision 3 put the page outside this repo. This change builds it here as a sample. Who owns the
  production page, and does a demo of this sample count as the page demo that change 001's acceptance requires?
- The 001 history is kept in memory only and is lost on restart (001 acceptance). Until that changes, most orders may
  show the empty state after a restart. Does this limit how far the page can move the Success measure?
- The 28 per week figure is demo data. What is the real baseline from the support tool, who pulls the weekly report
  30 days after release, and what is the release date?
- The `delivery_date is None` bug (001 intent) may also move the measure. How will its effect be separated from this
  page's effect?
- `{support_contact}` for `error.load.support` is still unknown. The PO supplies it before release.

## PO answers (before gate 1)
- Risk: keep high. The page is the first place that turns a signed-in customer id into order access, and the demo stand-in for sign-in must be reviewed by escalation.
- Support contact after 3 failed retries: "Still not working? Contact support at support@shop.example." (demo address).
