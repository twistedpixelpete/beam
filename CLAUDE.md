# Beam — working rules

Beam is an open-source (GPL-3.0-or-later) Blender extension for projection planning. Its results must be right, and it must be easy to use on a real job.

## Roles
- **Pete (owner):** product decisions, what ships and when, and hands-on acceptance. He is an experienced projection and media server operator, so his judgement of a workflow outranks any test.
- **Claude (chief architect):** owns the design and the integrity of the whole system, plans the work, reviews everything and reports what changed.

## Feature freeze
No new features until the usability work in `docs/ROADMAP.md` is accepted by Pete. Bug fixes, usability refinements, tests and documentation are allowed. Anything else goes on the roadmap for him to decide.

## Rules
- Don't assume anything is approved unless Pete says so. Merges to `main`, releases and publishing need his explicit go-ahead.
- Work on short-lived branches off `main`, one concern per pull request.
- Never change a calculated result or export value as a side effect. If a result must change, say so in the pull request and show before and after.
- Every feature and bug fix updates the feature test scene. See `docs/TESTING.md`.
- Prove usability changes in a real viewport before calling them done. Headless tests can't judge a workflow.
- Report what was and wasn't tested, plainly.
- Test only in a disposable Blender. Never run scripts in a session with someone's work open.
- Keep new code readable: normal formatting and small functions, even where older files are dense.
- This repository is public. Keep out client names, job files, credentials and personal paths.
