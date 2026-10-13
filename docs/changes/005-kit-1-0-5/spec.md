# Spec: Update the kit to Tripod 1.0.5

References: intent.md, ux-brief.md

## Requirements
- R1: The 16 kit files that match kit 1.0.3 must be replaced with 1.0.5's versions (`pod-install.sh . --vendor-plugins --force`), and the AGENTS.md pod section regenerated. (verified by: an installer re-run reports `No changes`, apart from pod.yml)
- R2: pod.yml, `app/` and `tests/` must not change. (verified by: `git diff --stat main -- pod.yml app/ tests/` is empty)
- R3: `make check` must pass, with 001 to 004 OK. (verified by: `make check`)
- R4: No `.pod-bak` file may be committed. (verified by: `git ls-files '*.pod-bak'` is empty)

## Edge cases
- E1: `--force` backs up pod.yml. It is restored from `pod.yml.pod-bak` before committing.

## Flagged concerns
- none

## Out of scope
- App changes.
