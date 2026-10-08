blockers: 0
majors_open: 2
second_opinion: agree
reviewed_head: 1ec0ad047057347577950547dd635cd56373d3c8

# Review: 002 status report

The first 4 lines are a header read by `scripts/auto-merge-check.sh`. Do not rename the keys.
`second_opinion: agree` means reviewer-second found no Blocker that the main reviewer missed and does not dispute the "no Blocker" result.

Lenses: security, correctness, tests and edge cases (three `reviewer` agents in parallel), then `reviewer-second`.
Diff reviewed: `git diff main...HEAD` (app/orders.py, tests/test_status_report.py, pod.yml, README.md, change docs).

## Blocker
- none. R1-R8 and E1-E8 each have code in `app/orders.py:77-92` and a test in `tests/test_status_report.py`. R9 is a demo proved at gate 4 in acceptance.md. The result holds only status keys and int counts (R6/E7). The code uses only the standard library (`collections.Counter`). `git diff ef55042 HEAD -- tests/` is empty, so no test was edited after the lock.

## Major
- `pod.yml:17,19` and `README.md:65-67` (commit dd1968f, from branch `config/auto-merge-demo`): `auto_merge` changes from `off` to `low` and `auto_merge_min_track` from `10` to `1`, and README gains a section about it. Neither file is in plan.md "Files to change". This is beyond the scope of plan.md (all four reviewers found it).
  - `pod.yml` is listed in `docs/risk-paths`, so with this commit in the diff the change is effectively Risk: high, not the Risk: low in intent.md. Gates 2 and 3 have no escalation signature.
  - The rollback in plan.md (`git revert` of the 002 merge) would also silently turn `auto_merge` back to `off`. The post-revert check does not cover that.
  - It also loosens the same merge policy that would decide whether this PR may auto-merge.
  - **Not fixed.** This is a change to merge policy, and removing it means rewriting branch history, so a human must decide. Options:
    1. Merge `config/auto-merge-demo` to main as its own change first, then rebase 002 onto main. The diff then shows only app/ and tests/.
    2. Drop dd1968f from this branch.
    3. Keep it here, re-tier 002 as Risk: high, and re-sign the gates with escalation.
- `app/orders.py:86` (spec E5, Open question in `plan.md:82`): E5 says a non-string status "must not raise", but an unhashable status (for example a list set through `set_status`) makes `status_label` raise `TypeError`. No test records the behavior.
  - plan.md (approved at gate 3) scoped this out on purpose and left it as an Open question. No human answer is recorded yet.
  - **Not fixed.** Tests are locked, so a guard would have no test. Human decision:
    1. Accept it as out of scope, to be handled by the `set_status` validation change.
    2. Narrow E5 in spec.md. This makes the gate 2 approval stale.
    3. Unlock the tests, then add a guard and a test.

## Minor
- `app/orders.py:82`: one docstring line is about 115 characters, much longer than the lines around it. Rewrap it in a later change. It is not fixed here, because any code change would make this review stale.
- `app/orders.py:86`: `True`, `1` and `1.0` are equal dict keys, so `Counter` merges them under the first one it sees. The sum (R8) is still correct, and no such data exists.
- `app/orders.py:90`: string `"3"` and int `3` stay as separate keys, with strings first. This looks intended, but no test covers it.
- `app/orders.py:90-91`: raw status values become keys as they are. If a free-text status contained customer data, the data would appear in the report. Spec Decision 1 accepts raw codes, and validating `set_status` is a separate change.
- `tests/test_status_report.py:56`: plan.md:65 says the E8 test should "change back", but the test only moves forward. E8 as worded in the spec is still covered. The tests are locked.
- `tests/test_status_report.py:116`: nothing tests where `""` sorts next to other raw string codes.
- `tests/test_status_report.py:1`: the module docstring still says "Failing tests". The tests are locked.
- `tests/test_status_report.py:32-47`: `setUp` does not reset `_ORDERS` to the demo data. The demo-data tests rely on the other test files cleaning up after themselves (spec Flagged concern 4). They do today.
- Some tests overlap with the demo-data test (reviewer-second). The overlap is harmless.
- `docs/changes/002-status-report/acceptance.md` does not exist yet. It needs the R9 demo call and its output before gate 4.

## Second opinion (reviewer-second)
- verdict: no-blocker, so `agree`. reviewer-second found no Blocker and did not dispute the "no Blocker" result.
- It raised the same pod.yml/README scope Major on its own. It rated the unhashable-status question a Minor (documented, no human answer yet); it is counted here as a Major to stay on the safe side.
- It was given only the diff, spec.md, plan.md and the checklist.

## Checks
- `make check`: pass. 150 tests OK, CODEOWNERS matches docs/risk-paths, and `gate-check --all` is OK (002 passed up to gate 3).
- `scripts/test-strength.sh`: pass. It checked 47 tests and found no weak tests.

## Decisions on open Majors (SuperDev, before merge)
- Major 1 (pod.yml and README in the diff): false positive. The reviewers compared against a stale local `main`. Those commits are already on `origin/main` through PR #4, which was approved by a person; against `origin/main` the diff contains only this change's files.
- Major 2 (unhashable status raises): accepted as out of scope, as recorded in spec.md decision 1. Status validation in `set_status` is a separate change.
