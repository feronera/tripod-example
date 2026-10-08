I ran `gh pr merge 5 --auto --squash`. It exited successfully but printed nothing.

Normally `gh` prints either "will be automatically merged via squash when all requirements are met" or a merged confirmation. The output may have been filtered by the RTK hook, so I can't tell from this whether auto-merge was queued or the PR merged straight away. You asked for only this one command, so I didn't run anything else to check.

To see the current state, run `gh pr view 5 --json state,autoMergeRequest,mergedAt`. If you want, I can run it.
