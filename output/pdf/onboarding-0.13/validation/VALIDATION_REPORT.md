# Beam 0.13 onboarding acceptance

Status: complete for controlled internal beta use. Tested on Blender 5.2.2 LTS, macOS 26.7, Apple silicon.

## Provenance

Continues the completed 0.12 package from `docs/beam-onboarding-package` at `dd7d809`. The original package remains on that branch and in the local `output/pdf/onboarding-0.12` archive. All original inventory SHA-256 values were verified unchanged. The frozen `docs/manual` baseline and example assets are unchanged.

Engineering baseline: merged main `33bf7a48d3bbc983bed358ba07fc0f3957642011`. The existing workspace-menu integration fix was brought forward as `8fd7f38`, making the documented View / Menu Search route available. The supplied installation ZIP includes this fix; earlier ZIPs with the same 0.13.0 version may lack it.

## Results

- User Guide: 33 pages, editable DOCX plus content JSON and retained Python builder. PDF generated from the DOCX and all pages visually inspected in rendered page sheets, with full-size checks of dense/new control pages. No blank overflow pages or clipped content found.
- Quick Start: two pages. Blank-scene operator validation passed: screen positioning, target, inverse six-metre width and three-projector layout. This run uses actual Blender operators; it is not claimed as a second full manual mouse walkthrough.
- Training companion: nine pages / 21 exercises. All exercise workflows passed in a clean disposable UI Blender configuration, including actual view PNG, CSV and Study Package exports. Detailed numeric evidence: `../exercise-results.json`.
- Reopened the pristine training file in a separate clean background process using the unpacked supplied installation ZIP, not the development source import. Verified three projectors, original group, nine valid camera references, OBS01 position/eye height/threshold, original blocker position and packed chart. Beam JSON contract validation passed. See `reopen.txt`.
- Generated chart was originally stored as Blender generated-image data. It was explicitly packed for the deliverable, then verified after a second independent reopen.
- All 71 existing pure Python unit tests passed (`unit-tests.txt`).
- Five-mode dropdown and Observer controls captured from the real 0.13 Beam UI. Illuminance, Distance and Acuity images are actual 0.13 Study View exports. Unchanged workflow illustrations were retained from the validated real 0.12 session; they are not mockups.

## Scope and limitations

No public release or stable certification. Install-from-Disk interaction was previously accepted in the retained 0.12 report; the current pass validates archive contents and fresh-process registration/reopen. No changes to the engineering calculations were required. The projector grid is a planning overlay, not photometric certification; all documented analysis assumptions still apply. Analysis results are transient and must be rerun after reopen or scene edits. Study Views recall cameras, not receiver selection.

The saved training file is the starting state, not the modified state left by the exercises. Export examples show the exercised state. Work on a copy.
