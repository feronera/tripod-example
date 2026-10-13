# Intent: Update the kit to Tripod 1.0.3

Status: draft

## Problem
This example still runs the kit from Tripod 0.5.x, last updated on 2026-10-09. Tripod is now at 1.0.3, and its README links here as the place to see the practice in action. Readers see older docs, older plugins and a different `make check` from the ones they install.

Evidence:
- 19 kit files differ from 1.0.3. Each matches an earlier kit release exactly, so the team edited none of them. Only pod.yml is our own.
- The repository carries copies of the kit's own 0.5.x tests (`tests/test_pod_*.py`). They test the kit, not this app, and they fail against the new kit. Since 1.0.x the kit's tests live in Tripod.
- A trial upgrade on 2026-10-13 found two things. One GitHub login holds SuperBiz and escalation, which needs `bootstrap: on`. Change 003's signed plan failed a newer plan rule, which Tripod 1.0.3 fixed.

## Users
- Readers of the Tripod README who follow the link to see real changes.
- Workshop facilitators who show this repository.

## Success measure
- Kit version in this repository: from 0.5.x to 1.0.3. All 19 old kit files are replaced, and pod.yml keeps our people and settings.
- `make check` passes: the app's 108 tests, test strength, CODEOWNERS, and `gate-check --all` with changes 001 to 003 still OK.
- CI (`pod-gates`) passes on the pull request.

## Risk
Risk: high

1. Law or regulation: no.
2. Seen directly by customers or external users: no app behavior changes, but readers of this public example see it.
3. Rollback within minutes without data loss: yes, `git revert`.
4. Personal or sensitive data: no.

It touches `scripts/**` and `pod.yml`, which `docs/risk-paths` makes high.

## Constraints
- No change to `app/`, or to the app's tests.
- Remove only the three kit test files (`tests/test_pod_scripts.py`, `test_pod_v2.py`, `test_pod_v3.py`).
- Keep pod.yml. Add only `bootstrap: on`, with a comment saying why.

## Open questions
- none
