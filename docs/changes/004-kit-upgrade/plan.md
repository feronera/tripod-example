# Plan: Update the kit to Tripod 1.0.3

References: intent.md, spec.md

## Data shape
- Kit files: each path in the installer's manifest maps to Tripod 1.0.3's content. Our copy is either equal, an older kit release (replace), or edited by us (only pod.yml, kept).
- pod.yml: the existing keys plus `bootstrap: on`.

## Throughput checkpoint
- Blocking first steps: none: no new tests, because the change adds no app behavior and R1 to R6 are checked by commands
- Independent workstreams: n/a: one installer run
- Shared mutable state: pod.yml, which the installer must not overwrite
- Smallest safe decomposition: one commit for the kit files and the pod.yml line, one commit removing the three kit test files, then `make check`

## Parallel parts
none: one installer run

## Files to change
| File | What changes | Requirement |
|---|---|---|
| kit files (scripts/, plugins/, docs/, AGENTS.md, .gitignore) | replaced or added by `pod-install.sh . --vendor-plugins --force` | R1 |
| `pod.yml` | kept; adds `bootstrap: on` and a comment | R2 |
| `tests/test_pod_*.py` | removed | R3 |

## Order of work
1. Run `~/tripod/scripts/pod-install.sh . --vendor-plugins --force` from a Tripod 1.0.3 checkout.
2. Restore pod.yml from `pod.yml.pod-bak`, add the bootstrap line, and delete every `.pod-bak`.
3. Remove the three kit test files.
4. `make check`, then open the pull request.

## Risks
- The installer overwrites a file the team edited. Mitigation: every replaced file was compared with the kit's release tags before the change. Only pod.yml differs from all of them, and it is restored from the backup.

## Proof
- R1: the installer re-run reports `No changes`.
- R2, R3, R4, R6: `git diff --stat main` and `git ls-files`.
- R5: `make check` and CI.

## Rollback
- `git revert <merge commit>`.

## Summary for SuperBiz
1. The example now shows the same kit readers install from Tripod 1.0.3.
2. The app does not change, and changes 001 to 003 still pass their gates.
3. Risks: none for the app. Three kit test files leave, because the kit's tests live in Tripod.
