# Acceptance: Update the kit to Tripod 1.0.3

References: intent.md, spec.md

## Success measure check
| Success measure | How measured | Result | Pass? |
|---|---|---|---|
| Kit version from 0.5.x to 1.0.3, pod.yml kept | installer re-run, `git diff main -- pod.yml` | `No changes` (pod.yml skipped as intended); pod.yml adds only `bootstrap: on` | Yes |
| `make check` passes with 001 to 003 still OK | `make check` | 108 app tests pass; 001, 002 and 003 OK | Yes |
| CI passes on the pull request | `pod-gates` on the PR | to be confirmed on the PR | Pending CI |

## Demo steps
1. Open docs/ and plugins/ on this branch.
   - Expected: the same content as Tripod 1.0.3.
   - Actual: as expected. The installer reports no differences.

## Decision
Decision: accept (proposed by the agent; Bee confirms by signing gate 4)

Reason: the example now matches the kit readers install, and the app and its finished changes are untouched.
