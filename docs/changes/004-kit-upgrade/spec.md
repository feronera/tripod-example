# Spec: Update the kit to Tripod 1.0.3

References: intent.md, ux-brief.md

## Requirements
- R1: The 19 kit files that match an earlier kit release must be replaced with Tripod 1.0.3's versions, using `pod-install.sh . --vendor-plugins --force`, and the new kit files it adds must be committed. (verified by: re-running `pod-install.sh . --vendor-plugins` reports `No changes`, apart from pod.yml)
- R2: pod.yml must keep its people, logins and settings, and add only `bootstrap: on` with a one-line comment. (verified by: `git diff main -- pod.yml`)
- R3: `tests/test_pod_scripts.py`, `tests/test_pod_v2.py` and `tests/test_pod_v3.py` must be removed. No other test file changes. (verified by: `git diff --stat main -- tests/`)
- R4: `app/` must not change. (verified by: `git diff --stat main -- app/` is empty)
- R5: `make check` must pass: the app's tests, test strength, CODEOWNERS and `gate-check --all`, with 001, 002 and 003 still OK. (verified by: `make check`)
- R6: No `.pod-bak` file may be committed. (verified by: `git ls-files '*.pod-bak'` is empty)

## Edge cases
- E1: `gate-check --all` warns that bootstrap is on. This is expected and documented in the comment.
- E2: The installer's AGENTS.md section is replaced between `pod:begin` and `pod:end`. Lines outside it stay.

## Flagged concerns
- Removing tests: these three files test the kit, not this app. The kit's tests live in Tripod (391 pass on 1.0.3). Auto-merge would refuse a deleted test line, but this change is high risk, so people merge it.

## Out of scope
- App changes, and new example changes using the 1.0.x features (Autonomous mode, the loop).
