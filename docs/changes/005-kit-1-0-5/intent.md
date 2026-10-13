# Intent: Update the kit to Tripod 1.0.5

Status: draft

## Problem
This example runs kit 1.0.3, from change 004. Tripod 1.0.5 has a shorter merge skill (plugins 1.0.1), and `auto-merge-check` now defaults to pod.yml's base branch. It also has the 1.0.4 fix that stops a change from pointing `base_branch` at itself. Readers who compare this example with what they install would see the older skill and scripts.

Evidence:
- 16 kit files differ from 1.0.5, and each matches kit 1.0.3 exactly, so the team edited none of them. Only pod.yml is ours.

## Users
- Readers of the Tripod README who follow the link to see real changes.
- Workshop facilitators who show this repository.

## Success measure
- Kit version in this repository: from 1.0.3 to 1.0.5. A re-run of the installer reports `No changes`, apart from pod.yml.
- `make check` passes, with changes 001 to 004 still OK.
- CI (`pod-gates`) passes on the pull request.

## Risk
Risk: high

1. Law or regulation: no.
2. Seen directly by customers or external users: no app behavior changes, but readers of this public example see it.
3. Rollback within minutes without data loss: yes, `git revert`.
4. Personal or sensitive data: no.

It touches `scripts/**` and `plugins/**/hooks/**`, which `docs/risk-paths` makes high.

## Constraints
- No change to `app/`, the app's tests or pod.yml.

## Open questions
- none
