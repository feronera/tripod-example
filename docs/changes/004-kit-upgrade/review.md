blockers: 0
majors_open: 0
second_opinion: none
reviewed_head: ba7c715507b67b7a923bb8324b96f0bd92c9868d

# Review: Update the kit to Tripod 1.0.3

A mechanical kit update with no app code, so there was no reviewer run. The review is the check of each requirement below. Before the change, every replaced file was compared with the kit's release tags: each matched an earlier kit release exactly, and only pod.yml differed from all of them.

## Checks against the spec
| Req | Result |
|---|---|
| R1 kit files replaced | Re-running `pod-install.sh . --vendor-plugins` reports `No changes`. It skips only pod.yml, which is intended |
| R2 pod.yml kept | The diff adds only the comment and `bootstrap: on` |
| R3 only the three kit tests removed | `tests/`: 3 files changed, 1467 deletions. No other test file changed |
| R4 no app change | `git diff --stat main -- app/` is empty |
| R5 make check | Pass: the app's 108 tests, test strength (108 tests, no weak tests), CODEOWNERS, and `gate-check --all` with 001 to 003 OK |
| R6 no backups committed | `git ls-files '*.pod-bak'` is empty |

## Notes
- Change 003 passes only because of Tripod 1.0.3: its signed plan predates the `tests:` rule for parallel parts.
- `gate-check --all` warns while bootstrap is on, as the spec expects (E1).

## Code authors
64177747+hx-natthawat@users.noreply.github.com (kit files and test removal; no app code)
