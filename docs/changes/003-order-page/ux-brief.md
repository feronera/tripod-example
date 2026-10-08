# UX brief: Order status page for customers

References: intent.md, `docs/changes/001-order-history/ux-brief.md`

## Source of this brief
This brief is a copy of the change 001 ux-brief, which the PO approved for this page. Its decisions, PO answers,
screen, states, copy and accessibility notes are kept as they were. Only two things differ, both required by this
change's intent.md:
1. **Demo sign-in banner** (new). The sample has no real sign-in; it uses a demo stand-in for the trusted layer that
   supplies the signed-in customer id. The page shows a clearly labelled banner so nobody mistakes it for real sign-in.
   See `demo.banner` and the rules below.
2. **Support contact** (filled in). `error.load.support` now uses the text the PO supplied in intent.md
   ("PO answers (before gate 1)"). The 001 open question about `{support_contact}` is closed for this sample.

Nothing else changed, apart from notes that follow from these two items: Accessibility (banner landmark, plain-text
support address, wrapping), the full-stop note for `demo.banner`, PO answer 4, PO answer 7 (support address stays
plain text), and the open questions.

## PO decisions applied
These were decided by the PO (SuperBiz) before the 001 brief was drafted, and still apply:
- History is listed newest first.
- Times use the 24-hour clock.
- The note "Earlier updates are not listed" is shown on every order, with no date.
- A status code with no label is shown as the raw code.
- There is no "Your orders" page, so the not-found message has no link.

Decisions from this change's intent.md (PO answers before gate 1):
- The page shows a clearly labelled demo banner: "Demo sign-in: Customer C001".
- Support contact after 3 failed retries: "Still not working? Contact support at support@shop.example." (demo address).

Decision from the PO for this brief (PO answer 7):
- The support address is plain text, not a `mailto:` link.

Wording: this brief uses "update" for a recorded status change, the same word as the customer copy.

## Screens
One screen meets the intent.

| Screen | Purpose | Data shown | Main action |
|---|---|---|---|
| Order status | Let a customer see what their order's status is now and when it was updated, so they do not need to contact support | Demo sign-in banner (sample only), order number, current status label, time of the latest recorded update (if any), list of updates (label + date/time, Asia/Bangkok, newest first), the fixed note about earlier updates | Read only. The only action is "Try again" in the could-not-load state |

Layout, top to bottom:
0. **Demo sign-in banner** (`demo.banner`), full width, above everything else on the page, including the `h1`. It is
   outside the page's main content (see Accessibility notes). It is not a link and has no action.
1. Page heading (`h1`) with the order number.
2. **Current status** section: the status label, and below it "Updated <date/time>" when the latest update is recorded.
   The time zone note (`history.timezone`, PO answer 1) sits directly under this line, before any other time. With no
   "Updated" line, it sits at the top of the history section instead.
3. **Status history** section: a visible "Newest first" line under the heading, then the list of updates. Each row
   shows the status label and the date/time.
4. The note "Earlier updates are not listed", always shown under the list.

Date/time format: `9 Oct 2026, 14:05` (day, short English month name, year, 24-hour time). The month name avoids
confusion between day/month and month/day order. All times are in Asia/Bangkok time.

## States
| Screen | empty | loading | error | success |
|---|---|---|---|---|
| Order status | Demo banner. The order exists but no update has been recorded since release. Show the current status label without an "Updated" line. In the history section show `history.empty`, then `history.earlier_note` | Demo banner. Show `page.loading` in place of the content. No partial data. Browser title is `page.title` (or `page.loading_title` when the order number is not known) | Demo banner in every error case. Three cases, see the rules below. **Not found**: `error.not_found.title` + `error.not_found.body`, no link, no retry. **Could not load**: `error.load.title` + `error.load.body` + `error.load.retry` button. **Not signed in / session expired**: the existing sign-in flow, then back to this page | Demo banner. Current status label with `status.updated` line (when the latest update is recorded), history list newest first, then `history.earlier_note` |

Rules for every state:
- **Demo sign-in banner.** Shown in every state in which the demo stand-in supplies the signed-in customer (loading,
  empty, success, not found, could not load). The text is fixed and identical in every state and for every order
  number; it is also shown on could-not-load when the failure is in the demo stand-in itself, so could-not-load looks
  the same in every case. It names only the demo customer the stand-in signs in as, never the customer who owns the order being
  looked up, so it never tells the user whether an order exists or whose it is. It is never shown in the not signed
  in / session expired case, because no customer is signed in then. It is never shown outside the demo (how it is kept
  out of production is an open question for SuperDev, from intent.md).
- **Order of checks.** Sign-in is checked first, then ownership, then the history is loaded. A customer can reach the
  could-not-load state only for an order they own. Any failure before the ownership check shows the could-not-load
  state for every order number, owned or not, so the state never tells the customer whether an order exists.
- **Not found** covers both a missing order and another customer's order. Same text, same layout, same page title,
  same response time as far as the customer can see. It never says or hints that the order exists.
- **Not signed in / session expired** looks the same for every order number: the customer is sent to sign in, and
  after signing in returns to this page, where the normal checks run. No order data or order-specific message is
  shown before sign-in.
- **Loading timeout.** If no response arrives within 10 seconds, show the could-not-load state (PO answer 5).
- **Repeated failures.** "Try again" stays available after each failure; the copy stays the same. After 3 failed
  retries, `error.load.support` is also shown under `error.load.body` and stays until the order loads (PO answer 6).
- An unknown status code is shown as the raw code (for example `on_hold`) in both the current status and the history,
  in the same style as a normal label.
- The "Updated" line is shown only when the time of the current status is recorded. Orders whose status was last
  updated before release show the label only; the line is never shown with an empty or guessed time.
- When the current status's update is recorded, it appears both in "Current status" (with the "Updated" line) and as
  the newest history row. This repetition is deliberate: the top section answers "where is my order now", the list
  answers "what happened when". The PO confirmed this (PO answer 2).

## Copy
| key | Text | Notes |
|---|---|---|
| demo.banner | Demo sign-in: Customer C001 | New in this change (PO, intent.md). Fixed text, no link, no action. Shown in every state except not signed in / session expired. Sample only, never in production |
| page.title | Order {order_id} | `h1` and browser title in loading, empty and success states |
| page.loading_title | Loading order | Browser title while loading when the order number is not known |
| page.loading | Loading your order… | Shown while waiting |
| status.heading | Current status | Section heading (`h2`) |
| status.updated | Updated {datetime} | Under the current status label. Only when the latest update is recorded |
| history.heading | Status history | Section heading (`h2`) |
| history.order | Newest first | Visible line under the history heading |
| history.row | {status_label} – {datetime} | One per update. Visually the date/time may sit on its own line |
| history.empty | No status updates are listed for this order. | Empty state for the history list. Does not say "yet", so it does not conflict with a status such as Delivered |
| history.earlier_note | Earlier updates are not listed. | Shown on every order, under the history list. No date (PO decision) |
| history.timezone | Times are shown in Bangkok time (GMT+7). | Kept (PO answer 1). Right after the "Updated" line, or at the top of the history section when there is no "Updated" line |
| error.not_found.title | Order not found | `h1` and browser title |
| error.not_found.body | We couldn't find this order. Open the order link in your order confirmation email, and check that you are signed in with the account you used to place the order. | Same text whether the order is missing or belongs to someone else. No link (there is no "Your orders" page). Points to the confirmation email because customers arrive from its order link (PO answer 3) |
| error.load.title | We couldn't load your order | `h1` and browser title |
| error.load.body | Something went wrong. Check your connection and try again in a moment. | Server, network or timeout failure |
| error.load.retry | Try again | Button. Reloads the order. "Try again" is used only for this button |
| error.load.support | Still not working? Contact support at support@shop.example. | Changed in this change: PO-supplied text (intent.md), replaces the 001 placeholder. Shown under `error.load.body` after 3 failed retries (PO answer 6). `support@shop.example` is a demo address. Wrap the address in its own element (for example `<span>`) so the final full stop is outside it when selected or copied |

All sentence-style notes end with a full stop; headings, labels and buttons do not. `demo.banner` is a label and has
no full stop.

Status labels come from `STATUS_LABELS` in `app/orders.py` (Awaiting payment, Paid, Preparing order, Shipped,
Delivered, Cancelled). No new labels are added by this brief.

## Accessibility notes
- All text is readable by a screen reader, and no meaning is conveyed by color alone. Statuses are text labels; any
  color or icon is decoration only and has a text equivalent.
- Demo banner: a labelled landmark before the `main` element (for example `<aside aria-label="Demo notice">`), not
  inside the live region, so it is not re-announced on every state
  change. It is plain text, read in normal reading order before the `h1`. Its "demo" meaning is carried by the words
  "Demo sign-in", never by color or an icon alone. It is not focusable and does not take focus.
- Headings: one `h1` in every state (see Copy), `h2` for "Current status" and "Status history", so screen reader
  users can jump between sections. The banner is not a heading.
- The history is an ordered list (`ol`) so a screen reader announces the number of items. Its accessible name is
  "Status history, newest first", matching the visible "Newest first" line.
- Each date/time uses a `<time datetime="…">` element with the full ISO value including the +07:00 offset.
- The loading message and the error messages are in a polite live region (`role="status"`). After a failed retry the
  region is cleared and refilled, so the same error is announced again.
- Focus management:
  - First load: when content or an error appears, focus moves to the `h1` (with `tabindex="-1"`), so screen reader
    users know loading has finished.
  - Retry: when "Try again" is pressed, focus moves to the `page.loading` text (`tabindex="-1"`). On success it then
    moves to the `h1`; on failure it moves to the error `h1`, with "Try again" next in the tab order.
- Full keyboard use: the only interactive element is the "Try again" button; it is reachable with Tab, works with
  Enter and Space, and has a visible focus outline. The support address in `error.load.support` is plain text, not a
  link (PO answer 7).
- Text contrast is at least 4.5:1 (WCAG AA) for all text, including the demo banner, the date/time, "Newest first" and
  the earlier-updates note, which must not be styled as faint grey text below this ratio.
- The layout works at 200% zoom and on a 320 px wide screen without horizontal scrolling; long raw status codes and
  the banner text wrap.

## PO answers to the open questions (from change 001)
Answered by the PO (SuperBiz) for the 001 brief. They still apply.
1. Time zone note: **yes**, show `history.timezone` ("Times are shown in Bangkok time (GMT+7).") directly under the
   "Updated" line. When there is no "Updated" line (empty state), it sits at the top of the history section, before any
   time is shown.
2. Current status repeated as the newest history row: **yes**, keep it in both places.
3. How customers reach the page: from the order link in their order confirmation email. The not-found copy now points
   to that email instead of asking the customer to check a number they cannot edit.
4. Sign-in: it exists outside this repo and returns the customer to this page after sign-in. SuperDev still confirms
   how the page gets the verified customer in plan.md. In this sample a demo stand-in supplies the customer
   (this change).
5. Loading timeout: show the could-not-load state after **10 seconds** without a response.
6. Repeated failures: after **3 failed retries** (3 presses of "Try again" that each fail), also show
   `error.load.support` under the error. "Try again" stays available.

## PO answers (this change)
7. Support address as a link: **no**. Keep `support@shop.example` as plain text, with no `mailto:` link. "Try again"
   stays the only focusable element on the page.

## Open questions
- The 001 open question on `{support_contact}` is closed for this sample by the PO's text in intent.md. The address is
  a demo address; the real support contact for production is still to be supplied by the PO before a production
  release.
- How the demo stand-in and its banner are kept out of production (SuperDev, plan.md; from intent.md).
- With the demo stand-in always signing in as C001, how is the not signed in / session expired state shown in the
  recorded demo that intent.md Success measure 2 requires? (SuperDev, plan.md.) This brief does not choose a mechanism.
- intent.md still lists `{support_contact}` as unknown under Open questions, while its "PO answers" section supplies
  the text. intent.md has passed gate 1, so it is not edited here; SuperBiz decides whether to update it and re-sign.
