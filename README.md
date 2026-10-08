# Tripod example

A real run of [Tripod](https://github.com/feronera/tripod) 0.5.1 on GitHub. One change, **order status history**, goes from the first intent to a merged pull request through all four gates. The run uses the real Claude Code plugins, real CI, branch protection and pull request approvals.

- The pull request with the full history: [PR #1](https://github.com/feronera/tripod-example/pull/1)
- The change folder: [docs/changes/001-order-history/](docs/changes/001-order-history/), with intent, UX brief, spec, plan, review, acceptance and `gates.log`
- The code the agents wrote: [app/orders.py](app/orders.py), [app/timefmt.py](app/timefmt.py) and [tests/test_order_history.py](tests/test_order_history.py)
- Each agent step's final reply: [run/agent-replies/](run/agent-replies/)

The repository started from the Tripod template, so everything else here is the standard kit. The people and the support numbers are fictional demo data.

## The team

| Role | Person | Signs gates as (git email) | GitHub account |
|---|---|---|---|
| SuperBiz | Bee | `bee@pod.example` | `hx-natthawat` |
| SuperDev | Dan | `dan@pod.example` | `feronera` |
| Escalation | Lee | `lee@pod.example` | `hx-natthawat` |

Demo limitation: only two GitHub accounts were available, so SuperBiz and escalation share one GitHub login. Gate signatures in `gates.log` still come from three different identities. In a real team, escalation is a third person.

## How the run worked

- Each person worked in their own clone with their own git identity.
- Each agent step ran `claude -p` with only that person's plugin (`superbiz` or `superdev`) and a narrow list of allowed tools. See [run/ask.sh](run/ask.sh).
- Every gate was signed by a person with `scripts/gate.sh`. Agents never signed.
- Models:
  - `claude-opus-5-5` for the main sessions.
  - `claude-sonnet-5-5` for the `reviewer-second` agent, as the plugin specifies.
- Non-interactive runs cannot ask follow-up questions, so the PO's answers were given in the prompts. In a normal session the skills ask them one at a time.

## Timeline

| Step | Who | What happened | Agent time | Cost (USD) |
|---|---|---|---|---|
| 1 | Bee + agent | `/superbiz:intent`: set Risk: high, because rolling back deletes recorded history. It also noticed that SuperBiz and escalation share a GitHub login | 38 s | 0.39 |
| Gate 1 | Bee, Dan | Signed. Dan opened PR #1 as a draft, CI ran, and `pr-check` failed as expected because there was no approval yet | | |
| 2 | Bee + agent | `/superbiz:ux-brief`: `ux-critic` found 5 Major issues, all fixed | 148 s | 0.72 |
| 3 | Bee + agent | `/superbiz:spec`: `ba-researcher` cited exact code lines and raised 12 flagged concerns | 152 s | 0.83 |
| Gate 2 | Bee, Dan, Lee | Bee and Dan recorded a decision on each concern in spec.md, then three signatures (Risk: high) | | |
| 4 | Dan + agent | `/superdev:plan`: data shape, throughput checkpoint, rollback, and a plain summary for SuperBiz | 92 s | 0.63 |
| Gate 3 | Dan, Bee | Bee cross-checked the summary against the intent | | |
| 5 | Dan + agent | `/superdev:test-first`: failing tests from the spec, then Dan locked the tests | 290 s | 0.86 |
| 6 | Dan + agent | `/superdev:build`: three units, one commit each. `make check`: 136 tests, no weak tests | 198 s | 0.60 |
| 7 | Dan + agent | `/superdev:review`: three lenses plus `reviewer-second`. 0 Blockers, 1 Major, second opinion agrees | 211 s | 1.57 |
| 8 | Dan + agent | Asked the agent to run `gh pr merge` before gate 4. The `gate-guard` hook blocked it | 18 s | 0.25 |
| 9 | Bee + agent | `/superbiz:acceptance`: ran the demo against the real code and recorded the output | 206 s | 0.67 |
| Gate 4 | Dan, Bee, Lee | Three signatures. `auto-merge-check`: DENY (auto-merge off, Risk high, no track record). `release-check`: RELEASE-READY | | |
| Merge | Bee, then Dan | Merging before approval was refused by branch protection. Bee approved on GitHub, CI passed, and Dan merged | | |
| **Total** | | | **about 23 min** | **about 6.5** |

`scripts/metrics.sh` measured 55 minutes from the first intent commit to gate 4, including the GitHub steps. Per-step costs are in [run/costs.tsv](run/costs.tsv).

## What the run showed

- **The agents were careful.**
  - The intent agent chose the higher risk tier and listed open questions instead of guessing.
  - The review ran on two different models, and they agreed.
  - Every agent stopped before any decision that belonged to a person.
- **The guardrails held on GitHub.**
  - Branch protection refused the merge until the required `pod-gates` check passed.
  - `pr-check` failed without the approvals the risk tier needs, and passed once SuperBiz approved.
  - The `gate-guard` hook stopped the agent's own `gh pr merge`.

## Problems found

Each of these is tracked as a fix in Tripod.

1. **A stale failed check can keep a pull request blocked.**
   - CI runs on `pull_request` and again on `pull_request_review`. The run from before the approval fails and stays failed, so GitHub keeps blocking the merge even after the run triggered by the approval passes.
   - In this run, re-running the first check unblocked it.
2. **The repository owner can bypass the rules with `gh pr merge --admin`,** because branch protection did not include administrators.
3. **Branch protection needs a public repository or a paid GitHub plan.** On a free plan, `scripts/setup-github.sh` fails for private repositories with HTTP 403. This example is public for that reason.
