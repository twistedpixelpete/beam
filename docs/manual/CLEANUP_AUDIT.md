# Pre-documentation cleanup audit

25 October 2026 - Twisted Pixel. Scope: consistency, existing-workflow verification and documentation freeze. No new product features, optics expansion, schema changes, release/tag or manual/training deliverables.

## Repository and code

PR #6 was reviewed at `b389d57eb80b433e977598d336675f20304e796e`, its hardening lifecycle/interop/migration and production tests rerun, and merged with Pete's explicit approval at `3ff2982b4fd5cdbd04eda2b7b5417c5079fc716b`. Clean main was fast-forwarded before `feature/beam-pre-doc-cleanup` was advanced to that base. Main protection/ownership was unchanged. PATCH PR #29 remains separate and unmerged.

Paused onboarding work was preserved under ignored `work/paused-onboarding/`. It is not part of this cleanup delivery. No further full manual, Quick Start or training project work was undertaken.

Removed seven unused imports after AST/name and repository-reference checks: `hypot`, `auto_layout.screen_objects`, `screen_objects.bmesh`, `analysis_runtime.Vector`, `screen_surface.Matrix`, `screen_ui.bpy`, `study_views.image_filename`. No module/operator was removed: the older Auto Blend operator remains the implementation delegated to by New Auto Blend; lifecycle and export compatibility paths remain used. Only one custom icon exists (`valid.png`), and it is used. The XML theme and build tool remain used. Cleanup exception handling for invalidated Blender references is intentional; no speculative exception rewrites were made.

## Confirmed user-facing bug

Repeated five-generation migration exposed a nondeterministic Projector-to-Blend inspector change after reopening a 0.6 scene. The selection cache was keyed by Blender RNA addresses and survived load/Undo/Redo; reused addresses could be compared against the previous file's selection. The existing context-reset handler now clears that cache. Saved context is respected until the user makes a new selection. A deterministic UI-context regression seeds old selection state, runs the real reset handler and checks the saved inspector/projector. The original migration assertion remains strict, now with field-level diagnostics; eight consecutive full migration runs passed after the fix. Originals were never overwritten.

## Labels, messages and tooltips

- Version footer reads the extension manifest instead of hardcoded `0.10 Beta`.
- JSON search/operator name is **Export Beam JSON**, matching the **Beam JSON** module button.
- Blend creation guidance says **Reflow Group**, not the obsolete **Apply**.
- Reverse Mapping status uses **Covered Only**, **Uncovered Dimmed**, **Uncovered Hidden**, **Overlap Diagnostic**, rather than internal enum names such as DIM.
- Established module names, icons and short **Technical / Presentation** toggle labels remain unchanged. Search calls the toggle **Presentation / Technical View**; these describe the same action.
- Common warnings were reviewed against their recovery paths. **No Target**, **Scene changed · Analyse again**, lens-range messages, **Shift limits unavailable**, **No Reverse Mapping source**, **Receiver needs UVs**, **Unsupported receiver material**, and GPU requirements remain accurate. Missing material/UV/source warnings disable Enable on Receiver. Existing error text was not churned solely for style.
- A real-lens preset can say **VALID · known limits** and **Shift limits unavailable** simultaneously: valid known ratio/raster checks are not certification of unknown shift limits. UST records remain explicitly unsupported and absent from conventional selectable lenses.

## Documentation and assets

Replaced the bundled 0.8.1 README (duplicate stale instructions, old Screen Builder paths and Export CSV wording) with a short current orientation and version-aware pointer. Root README's build instruction now follows the manifest, not hardcoded 0.9 ZIP names. Its older showcase is explicitly labelled historical. Planning/UI/theme/production/hardening reports retain their history with a banner directing current readers to the baseline.

[Asset inventory](ASSET_INVENTORY.csv) classifies every example PNG/JPEG/Blend. No historical regression fixture was removed. No tracked screenshot was confidently disposable. New current captures and a small screenshot source scene are in `examples/manual-baseline/`. Temporary benchmark/test files remain ignored under `work/`. The current source set is documented in [Screenshot Baseline](SCREENSHOT_BASELINE.md).

Product version 0.12.0, JSON contract/schema versions, CSV exporter 1.2.0 and transform convention IDs intentionally have different meanings. Historical fixture producer versions and hashes are preserved, not rewritten to pretend they were regenerated.

## First-use acceptance

The real extension ZIP was installed with Blender's **Install from Disk** operator into a local disposable extension repository. A fresh process loaded that enabled installation, not imports from the source checkout. Scripted native operators then exercised the same actions exposed by the UI:

1. Open Beam Workspace from Layout; repeat Open and switch away/back without duplicates.
2. Create SCR001; create PJ01, aim with 3D Cursor, enter resolution/ratio and verify forward dimensions; enable Calibration Grid.
3. Duplicate two projectors; create a selection-based Blend Group; create a separate New Auto Blend and Reflow Group.
4. Distinguish Selected/Active/Pinned/Receiver; choose another active projector.
5. Save a Study View; analyse the receiver at 512/2048/8192; export Density and Stretch; move a projector and verify stale invalidation.
6. Enable Reverse Mapping; test Active Projector / Blend Group / All Active Projectors across all four modes; restore original materials.
7. Export Mapping Matter CSV, Designer CSV, Beam JSON and a rendered Study Package.
8. Apply Theme twice without replacing the original backup; save scene/preferences; exit and reopen in a fresh process.
9. Verify extension registration, one Beam workspace, persisted context/receivers/groups/views, empty analysis cache and Restore Previous Theme availability.

Native workspace acceptance additionally walks real Outliner selection, tests inline solve Undo/Redo, group member add/remove, screen updates, Frame/Lock/Presentation, and viewport exports. Rail-layout contract tests exercise narrow/wide labels, icons, all active states/tooltips and hidden-toolbar action fallback. Screenshots were visually inspected for current controls; this is scripted acceptance plus visual review, not an independent unassisted operator study.

## Test harness incidents and recovery

An initial install test pointed `BLENDER_USER_CONFIG` at a directory that had not been created. Blender fell back to the normal configuration when saving preferences. Pete's already-open Blender process (started the previous day) retained the original theme and 13 enabled add-ons; its in-memory preferences were saved back successfully. No production scene or installed extension was overwritten. The accidental test preference file is retained locally for diagnosis. The test now asserts both resolved configuration and extension repository paths before writing, and directories are created first.

A theme rerun initially reused a screenshot profile with an active theme backup; restoring that earlier backup correctly differed from the test's newly assigned theme. Final Apply/Restore validation uses a newly created, separate configuration, not the screenshot profile. A screenshot harness also needed the native area's space and Retina pixel coordinates; these were test-harness fixes, not product changes.

## Boundaries for the forthcoming guide

Use the exact source commit in [Documentation Baseline](DOCUMENTATION_BASELINE.md). Keep internal-beta wording. Do not infer direct Designer, Windows/Linux or manual PATCH GUI validation from automated tests. Preserve sampled/opaque geometry and GPU limits. The known small Blender shutdown allocation diagnostic remains disclosed in the hardening report; this pass does not certify heap/GPU leak freedom.
