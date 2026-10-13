blockers: 0
majors_open: 0
second_opinion: none
reviewed_head: 3116757aad4b90310ca85574d96fc8b10606538f

# Review: Update the kit to Tripod 1.0.5

A mechanical kit update with no app code, so there was no reviewer run. Before the change, each of the 16 replaced files matched kit 1.0.3 exactly.

## Checks against the spec
| Req | Result |
|---|---|
| R1 kit files replaced | Installer re-run: `No changes`. Only pod.yml is skipped, as intended |
| R2 pod.yml, app/ and tests/ unchanged | `git diff --stat main -- pod.yml app/ tests/` is empty |
| R3 make check | Pass: 108 app tests, and 001 to 004 OK |
| R4 no backups committed | `git ls-files '*.pod-bak'` is empty |

## Code authors
64177747+hx-natthawat@users.noreply.github.com (kit files only)
