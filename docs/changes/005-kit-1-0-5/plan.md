# Plan: Update the kit to Tripod 1.0.5

References: intent.md, spec.md

## Data shape
- Each kit path maps to Tripod 1.0.5's content. Ours is either equal, or kit 1.0.3 (replace). pod.yml is kept.

## Throughput checkpoint
- Blocking first steps: none: no app behavior, so no new tests; R1 to R4 are checked by commands
- Independent workstreams: n/a: one installer run
- Shared mutable state: pod.yml, which the installer must not overwrite
- Smallest safe decomposition: one commit for the kit files, then `make check`

## Parallel parts
none: one installer run

## Files to change
| File | What changes | Requirement |
|---|---|---|
| 16 kit files, AGENTS.md pod section | replaced by the installer | R1 |

## Order of work
1. `pod-install.sh . --vendor-plugins --force` from a Tripod 1.0.5 checkout.
2. Restore pod.yml from `pod.yml.pod-bak`, delete every `.pod-bak`.
3. `make check`, then open the pull request.

## Risks
- The installer overwrites a team edit. Mitigation: every replaced file matched kit 1.0.3 exactly before the change.

## Proof
- R1: installer re-run. R2, R4: git commands. R3: `make check` and CI.

## Rollback
- `git revert <merge commit>`.

## Summary for SuperBiz
1. The example shows the kit readers install from Tripod 1.0.5.
2. The app and its finished changes are untouched.
3. Risks: none for the app.
