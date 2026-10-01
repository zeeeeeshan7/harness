# Copilot issues

Four independent modules. They share no files and depend only on `harness/types.py` and `harness/hooks.py` (tag `v0.1`), so they can be assigned in parallel.

| # | File | Module |
|---|------|--------|
| 1 | `01-loop-detector.md` | `harness/detect/loops.py` |
| 2 | `02-chaos-mode.md` | `harness/chaos.py` |
| 3 | `03-resilience-report.md` | `harness/report.py` |
| 4 | `04-telegram-steering.md` | `harness/steer/telegram.py` |

The first line of each file is the issue title; the rest is the body.

Create and assign (after reviewing the files):

```
gh issue create --title "<first line without #>" --body-file docs/issues/01-loop-detector.md --assignee "@copilot"
```

Review each PR for: only the listed files changed, tests that can actually fail, no new dependencies. Request fixes by commenting `@copilot` on the PR. If a PR needs more than two rounds, close it and write the module by hand.
