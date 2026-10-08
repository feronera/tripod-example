# Tripod example

Real runs of [Tripod](https://github.com/feronera/tripod) on GitHub, using the real Claude Code plugins, real CI, branch protection and pull request approvals. Two changes go from the first intent to a merged pull request through all four gates:

- **Change 001, order status history (Risk: high).** People approve every step and a person merges. [PR #1](https://github.com/feronera/tripod-example/pull/1)
- **Change 002, order status report (Risk: low).** The agent checks the rules and merges by itself, and SuperBiz accepts afterwards. [PR #5](https://github.com/feronera/tripod-example/pull/5) and [PR #6](https://github.com/feronera/tripod-example/pull/6)

Where to look:

- The change folders, with intent, spec, plan, review, acceptance and `gates.log`: [001-order-history](docs/changes/001-order-history/) and [002-status-report](docs/changes/002-status-report/)
- The code the agents wrote: [app/orders.py](app/orders.py), [app/timefmt.py](app/timefmt.py), [tests/test_order_history.py](tests/test_order_history.py) and [tests/test_status_report.py](tests/test_status_report.py)
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

## Change 001: a high-risk change, merged by a person

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

## Change 002: a low-risk change, merged by the agent

An internal report for the support lead: the number of orders per status. It is not customer-facing, can be rolled back at once and holds no personal data, so the intent agent set Risk: low.

| Step | Who | What happened | Agent time | Cost (USD) |
|---|---|---|---|---|
| 1 | Bee + agent | `/superbiz:intent`: Risk: low, and 3 open questions that the PO answered before gate 1 | 25 s | 0.49 |
| 2 | Bee + agent | `/superbiz:spec` (no UI, so no UX brief). Two flagged concerns, both decided by people | 86 s | 0.61 |
| 3 | Dan + agent | `/superdev:plan`. It noticed a test lock left over from change 001 | 74 s | 0.49 |
| 4 | Dan + agent | `/superdev:test-first`, then Dan locked the tests | 270 s | 0.66 |
| 5 | Dan + agent | `/superdev:build`: two units, `make check` green | 222 s | 0.50 |
| 6 | Dan + agent | `/superdev:review`: 0 Blockers, second opinion agrees. Dan decided both open Majors | 231 s | 1.39 |
| 7 | Dan + agent | `/superdev:merge`: `auto-merge-check` printed **ALLOW**. The agent recorded `role=auto`, pushed it, and ran `gh pr merge --auto --squash`. CI accepted the auto record with no human approval, and GitHub merged PR #5 | 216 s | 0.84 |
| 8 | Bee + agent | `/superbiz:acceptance` after the merge, within the 48-hour window | 50 s | 0.49 |
| Gate 4 | Bee, Dan | Signed after the merge. `release-check`: RELEASE-READY. The acceptance went to `main` in [PR #6](https://github.com/feronera/tripod-example/pull/6), approved by Dan | | |
| **Total** | | | **about 20 min** | **about 5.5** |

`scripts/metrics.sh` measured 19 minutes from the first signature to gate 4.

## What the runs showed

- **The agents were careful.**
  - The intent agent chose the higher risk tier and listed open questions instead of guessing.
  - The review ran on two different models, and they agreed.
  - Every agent stopped before any decision that belonged to a person.
- **The guardrails held on GitHub.**
  - Branch protection refused the merge until the required `pod-gates` check passed.
  - `pr-check` failed without the approvals the risk tier needs, and passed once SuperBiz approved.
  - The `gate-guard` hook stopped the agent's own `gh pr merge` while gate 4 was incomplete.
- **Auto-merge worked end to end for low risk.** The agent merged only after all nine conditions passed, CI re-checked its record, and the person-only steps (acceptance, revert) stayed with people.

## Auto-merge demo settings

To test agent auto-merge for low-risk work, `pod.yml` sets `auto_merge: low` and `auto_merge_min_track: 1` (the default track record is 10 changes). Change 001 counts as that track record. A real team starts with `auto_merge: off`.

## Problems found

Each of these is tracked as a fix in Tripod.

1. **A stale failed check can keep a pull request blocked.**
   - CI runs on `pull_request` and again on `pull_request_review`. The run from before the approval fails and stays failed, so GitHub keeps blocking the merge even after the run triggered by the approval passes.
   - In this run, re-running the first check unblocked it. Tripod 0.5.2 now re-runs it automatically after an approval; [PR #3](https://github.com/feronera/tripod-example/pull/3) tested that fix here.
2. **Branch protection needs a public repository or a paid GitHub plan.** On a free plan, `scripts/setup-github.sh` fails for private repositories with HTTP 403. This example is public for that reason. Tripod 0.5.2 explains this instead of printing the raw error.
3. **The post-merge acceptance PR was blocked forever.** After the squash auto-merge, `pr-check` re-checked the docs-only acceptance PR against the auto record, and the reviewed commit was no longer in history. Fixed in Tripod 0.5.3: docs-only PRs follow the normal approval rules ([PR #7](https://github.com/feronera/tripod-example/pull/7) brought the fix here).
4. **A stale local `main` raised the risk.** The reviewers compared against an old local `main`, so an already-merged `pod.yml` change looked like part of change 002, which made it high risk. Since Tripod 0.5.3, the merge skill compares with `origin/main`.
5. **Lead time after a squash merge read 0 minutes.** Squashing drops the branch history, so the first intent commit on `main` came after every gate. Since Tripod 0.5.4, `metrics.sh` starts from the first gate signature and says so.
