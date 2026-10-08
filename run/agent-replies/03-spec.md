I've recorded the PO's six answers in `ux-brief.md` and written `docs/changes/001-order-history/spec.md`. Gate 1 had passed (Risk: high). I didn't sign any gate or touch `gates.log`.

**Changes to ux-brief.md** (it hasn't passed a gate yet, so no approval goes stale)
- The open questions are replaced by a "PO answers" section, and the States, Layout and Copy sections now match it.
- **Copy I drafted that the PO should check:**
  - I reworded `error.not_found.body` to point customers to their confirmation email.
  - I added a new `error.load.support` message for after 3 failed retries.
- One open question remains: the real support contact text. I didn't make one up.

**spec.md**
- **Requirements:** 13 (R1–R13), each with how it is checked. R1–R8 can be unit tested. R9–R13 cover the page and can only be shown by demo.
- **Edge cases:** 18 (E1–E18). They cover missing orders, another customer's order looking the same as a missing one, malformed IDs, empty history, unknown status codes, the Bangkok date crossing midnight, the 10-second timeout and the retry count.
- **Out of scope:** 9 items.

**Flagged concerns:** there are 12; the main ones from the ba-researcher's code search:
1. **Nothing in the repo changes an order's status.** `app/orders.py:24-59` only reads orders, so nothing can record history yet. Whatever changes status in production is outside this repo.
2. **Orders are stored only in memory** (`app/orders.py:12-17`), so history would be lost on every restart. If a real database needs a migration, that touches a sensitive path (`**/migrations/**`).
3. **There is no page, request handler or sign-in code in this repo.** R9–R13 can't be built or tested here; SuperDev needs to say in plan.md where the page lives.
4. **The customer ID is trusted as passed in** (`app/orders.py:44`). `get_order` has no ownership check, so the customer-facing path must not use it directly.
5. **An existing test compares the whole result of `status_for_customer`** (`tests/test_orders.py:18-20`). History therefore has to come from a new function.
6. **The code search supports keeping Risk: high**, so gate 2 needs Lee's escalation signature. The open questions in the intent are still unanswered.
7. **PO to confirm "3 failed retries".** I read it as the first failed load plus 3 failed "Try again" presses.

**Next steps (gate 2)**
1. SuperBiz runs `scripts/gate.sh docs/changes/001-order-history 2`.
2. SuperDev cross-checks the spec, then runs the same command.
3. Because Risk is high, Lee (the escalation signer in `pod.yml`) must also run the same command.

Before signing, answer each flagged concern or accept it as a risk; the gate 2 checklist requires it.
