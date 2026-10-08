I've written the UX brief at `docs/changes/001-order-history/ux-brief.md`. Gate 1 had passed (Risk: high), so I went ahead. I haven't committed the file.

**What's in it**
- **One screen, the order page:** the current status (with "Updated 9 Oct 2026, 14:05" only when that time was actually recorded), then the status history below it.
- **Your five decisions are all applied:** newest first, 24-hour clock, the undated "Earlier updates are not listed." on every order, unknown codes shown as the raw code, and no link in the not-found message.
- **All four states are covered.** The empty state is an order with no updates recorded since release, and its text doesn't say "yet", so it doesn't clash with a status like Delivered. Loading, success and three error cases (not found, could not load, not signed in) are each defined.
- **The not-found message is the same** whether the order doesn't exist or belongs to another customer. The brief also sets the order of checks: sign-in first, then ownership, then the history. That way no error can reveal that someone else's order exists.
- **Accessibility notes:** headings in every state, the history as a numbered list, where keyboard focus goes after loading and after "Try again", no meaning carried by color alone, AA contrast, and a layout that works at 200% zoom and on narrow screens.

**ux-critic review:** it found no Blockers and five Major items. I fixed all five:
- where the ownership check happens, so a "could not load" error can't leak another customer's order;
- the not-found text now gives a next step the customer can take;
- the empty-state wording;
- keyboard focus being lost after "Try again";
- a missing state for customers who aren't signed in.

I also fixed the Minor items: a page title in every state, connection-aware error text, a visible "Newest first" line, consistent punctuation and wording, and screen readers announcing the error again after a failed retry.

**Questions left for the PO and SuperDev, listed at the end of the brief:**
1. Should the page show the proposed "Times are shown in Bangkok time (GMT+7)." note?
2. Should the current status also appear as the newest history row? The brief currently shows it in both places on purpose.
3. How do customers reach the page? The not-found wording depends on it.
4. How does the existing sign-in flow work, and does it bring the customer back to this page afterwards?
5. How many seconds before a slow load shows the error?
6. What should the page offer after several failed retries?

Next step: `/superbiz:spec`, which combines intent.md and this brief into spec.md for gate 2. Because the risk is high, gate 2 also needs the extra escalation signature.
