# PR #2 engineering review — Beam 0.9 beta

Reviewed on 14 October 2026. Maintainer: Twisted Pixel.

Scope: original PR head `ce9b7f3b0d1c6824eaa4cc503e9e3412686229ab`, based on `fee1b37d8871b7030b31071313c3c757ff31c437`, plus the review fixes. All changed source modules, tests, manifest, documentation and examples were inspected. Work stayed on the feature branch; no UI redesign or release publication is included.

## Assessment

The original draft needed correctness fixes before merge. With the changes and validation below, no unresolved merge blockers remain. This is suitable for merging as an **unreleased beta**, not a claim of production readiness or cross-platform certification. The published download remains 0.8.1 beta.

## Findings and resolution

| Class | Finding | Resolution / evidence |
|---|---|---|
| Blocker | Reverse Mapping restored by numeric material-slot index. Reordering slots could leave wrappers installed while clearing original restoration references. | Restore and rebuild match actual assigned wrapper identity. Regression failed before the fix; reorder/restore, replacement preservation and GPU mode-rebuild tests now pass. |
| Blocker | Explicit Screen inspector selection could display one screen while actions/Auto Blend used another selected screen. | Shared screen-context resolution prioritises the explicit choice for unchanged selection, recognises a newly selected screen before the selection timer, and synchronises programmatic screen selection. Original wrong-screen regression and native-duplicate Screen Builder tests pass. |
| Important | Changing an Auto Blend anchor reused cached overlap pixel/percentage scale. | Anchor identity is in the cache key. Switching between different throw ratios produces the expected doubled pixel scale in a deterministic test. |
| Important | Switching overlap units after manual optics edits used stale layout reference dimensions. | Attached-screen groups convert using the current anchor footprint; legacy unattached groups keep their existing semantics. Percent → metres → pixels remains physically consistent. |
| Important | Planarity/bounds alone accepted a screen with missing faces; stale coverage could survive same-count mesh edits. | Shared frame validation checks complete rectangular area as well as bounds/planarity. Geometry events and load/Undo/Redo invalidate measurements. Hole and same-count edit regressions pass. |
| Important | Scaled projectors could contribute misleading nominal coverage; invalid anchor planes could be exported with zero dimensions. | Invalid transforms are excluded and reported; unusable group measurement planes export as null. |
| Important | Reverse Mapping used only the first active-output flag, although Blender can resolve different EEVEE/Cycles output nodes. | Resolve outputs through Blender's node-tree API and wrap each effective output. Both engine-specific outputs are tested. |
| Important | A receiver error aborted all reverse refresh work; GPU state was not restored on the overlays-off path. | Per-receiver failure isolation, invalid masks disabled, technical errors logged, clear status shown; blend/depth/viewport state restored in finally. Two-receiver failure/recovery and GPU-state tests pass. |
| Important | Unused coverage images and deleted-projector offscreens could remain allocated, especially with overlays off. | Generated image/cache cleanup, stale RNA handling and unconditional deleted-map pruning. Three real GPU enable/disable cycles leave zero generated wrapper/group/image orphans. Deleted-map test passes with overlays off. |
| Important | The inverse dialog could commit to a newly selected projector rather than its preview subject; Cancel did not restore solve mode. | Capture the subject and display-unit factor, restore mode on Cancel, and report unavailable scene records clearly. Native Undo and live preview/Cancel checks pass. |
| Important | Missing template selection silently fell back to generic optics. | Explicit validation when template use is requested; opening Auto Blend without an active projector defaults to generic mode. |

The proposed fake-user wrapper leak did **not** reproduce. A defensive fake-user reset remains, but this is not counted as a confirmed defect. Early expanded test failures from incomplete fixture dependency-graph updates and shared test source materials were corrected in the fixtures, not misreported as product bugs.

## Architecture

- **Forward:** unchanged `projection_math.calculate` is the authoritative scalar projection model. Runtime owns scene hits and calculated records.
- **Inverse:** `planning_math` computes constraints; `inverse_solver` applies them transactionally and verifies the resulting forward values and first-hit target. Invalid solves roll back.
- **Layout:** pure planning searches count/grid/throw constraints. `auto_layout` creates ordinary editable projectors and ordinary group parents/slots, with unique IDs and colours. Shared `layout_geometry` validation removes live coverage's dependency on the creation-operator module.
- **Coverage:** `layout_coverage` measures nominal convex footprints on the attached screen plane; `coverage_math` computes their union. Existing first-hit depth maps remain authoritative for visual occlusion.
- **Reverse Mapping:** shader wrappers combine those GPU depth maps with original UV material evaluation. Projection-coordinate operations mirror the renderer necessarily in shader nodes; there is no second independent CPU targeting engine.
- **UI:** presents results and invokes operations. No engineering formula moved into panel drawing. Existing context/UI coupling is small and functional; navigation changes are deferred.

Handler registration/removal, timers, draw handlers, property callbacks and persistence were checked. Geometry and scene changes invalidate relevant caches; idle material refresh does not recreate shaders or upload depth images. New durable settings use Blender properties, pointers and UUID recipes, rather than Python-only caches.

## Validation actually run

Platform: **Blender 5.2.2 LTS**, build `d13f752e3b9c`, **macOS / Metal**. Disposable factory-startup processes; the user's live project and installed extension were not replaced.

| Validation | Result |
|---|---|
| Standalone Python discovery (`test_*.py`) | **49/49 passed**. Includes 5 new review methods: independent union cell oracle (40 seeded cases), both array axes across px/m/%, minimum Auto Count, portrait inverse roundtrips and invalid numeric limits. |
| `blender_review_regressions.py` | **10/10 passed**. Materials, explicit context, live anchor conversion/cache, screen edit invalidation, holes and invalid projector scale. |
| `run_blender_tests.py` | **All 15 existing milestones passed** in a GPU UI process. Covers projectors, numbering, duplicates, projection/occlusion, labels, units, groups, presentation, Study Views, CSV and JSON behavior. |
| Background acceptance | **8/8 scripts passed**: review regressions, planning milestone, group lifecycle, frustum helpers, JSON contract, Screen Builder, screen edges and screen beauty. These scripts contain assertions, not a separately counted unittest total. |
| `verify_planning_ui.py` | Native Lens solve, Auto Blend creation, Reverse Mapping enable/disable Undo/Redo; rendered pixel checks for UV continuity, dim/covered/hidden, union, overlap, movement, obstruction, restoration and overlays-off refresh passed. |
| `verify_review_gpu.py` | Native Position solve and group Reflow Undo/Redo; eight-projector performance sanity; GPU state; slot reorder followed by mode rebuild; repeated restore cleanup; exact save/reopen comparison; isolated receiver failure/recovery; deleted-map pruning; two register/unregister cycles passed. |
| `verify_reverse_persistence.py` | Saved material references restored; ten forced idle redraws caused no additional depth uploads or wrapper rebuilds. |
| `verify_group_ui.py` | Native duplicate Undo/Redo, real modal hierarchy copy and live group panel passed. |
| `create_planning_showcase.py` | Redirected into disposable work output: native dialogs, live inverse callback and Cancel rollback passed. Existing tracked images/examples were not overwritten. |
| Existing 0.9 `.blend` examples | Both opened successfully with unique projector IDs; Reverse Mapping original references restored. |
| JSON Schema | Auto Blend centimetre-scene export passed the frozen schema, finite JSON and UUID relationships; all three negative-schema checks passed. |
| Extension build | Installable and source archives built; Blender extension manifest/archive validation passed. |
| Static checks | Python compilation and `git diff --check` passed. |

CSV headers, UUIDs, units and filename behavior were not changed. Frozen PATCH JSON v1 schema/core fields were not renamed. Auto Blend uses existing group-plane fields; inverse locks and Reverse Mapping settings remain native `.blend` state, not a new interchange promise. External disguise/PATCH importer validation remains outstanding.

### Performance sanity

Eight projectors, one 4×2 Blend Group, a 24×6 m Screen Builder screen, 23 venue meshes, Reverse Mapping and overlays; 512 depth detail. Measurements are synchronous Beam work on this machine, not whole-viewport FPS or GPU latency guarantees.

| Work | Measured |
|---|---|
| 30 idle refresh calls | median **1.77 ms**, max **1.92 ms**, **0** extra depth uploads; wrapper identities unchanged |
| 8 projector movement refreshes | median **4.49 ms**, max **5.32 ms** |
| Live overlap recalculation | median **0.39 ms**, max **0.42 ms** |
| One lens solve | **1.46 ms** |
| 1000×600 Study View export | **145 ms** (earlier run: 657 ms) |

Save/reopen comparison covered projector/group UUIDs, PJ identifiers, optics, solve mode/locks, transforms, membership, anchor, layout screen, project/venue/revision, active screen, Reverse Mapping source/mode and original material references.

## Changed files

Correctness changes: `auto_layout.py`, `blend_groups.py`, `coverage_math.py`, `inverse_solver.py`, new `layout_geometry.py`, `layout_coverage.py`, `projection_renderer.py`, `reverse_mapping.py`, `screen_data.py`, `screen_objects.py`, `screen_ui.py`, `screens.py`, `viewport_display.py`.

New review tests: `tests/blender_review_regressions.py`, `tests/test_review_math.py`, `tests/verify_review_gpu.py`. Documentation: README, planning guide, this report and TEST_RESULTS. No external runtime dependency was added.

Commit and merge identifiers are recorded in the PR and final delivery report; this pre-merge report avoids self-referential commit identifiers.

## Remaining limitations / follow-ups

- Position solves still require zero lens shift. Auto chooses a deterministic mode, not a constrained rig/lens optimisation search.
- Auto Blend is for valid, flat rectangular managed screens. Coverage is nominal planar coverage; centre-hit validation cannot certify all partial obstructions. Contrived overlapping mesh faces balanced by holes are not a supported edited-screen topology.
- Reverse Mapping requires an interactive GPU viewport, supports at most 32 sources per receiver, and has finite-resolution/bias artifacts. Headless/final animation live masking is unsupported. Source shader edits require restore/re-enable; image pixels remain shared.
- Profile 16–32 projectors and dense real venue geometry at 1024/2048 detail before making stronger performance claims. This was a modest eight-projector sanity scene.
- Blender 4.5, Windows and Linux remain unverified. Blender reports the future removal of `Material.use_nodes` in 6.0; compatibility work is a later task, not evidence of failure on this runtime.
- No automated hosted CI checks are configured on this PR. Preserve reproducible Blender scripts; add appropriate platform CI when infrastructure is available.

## Next UI pass — notes only

1. Make selection, pinned active projector/screen, and the object receiving Reverse Mapping visibly distinct.
2. Consolidate duplicate Add Projector, units, metadata and Presentation controls.
3. Shorten the route from Calculated values to Set Target and make lock/mode restrictions visible before opening a dialog.
4. Keep requested/actual overlap summaries readable for large arrays; expose detailed pairs progressively.
5. Clarify that Auto Blend New Layout creates another group, while Reflow changes the existing one.
6. Distinguish per-projector, per-view and global annotation controls. Eight-projector labels can obscure coverage in Technical mode.
7. Improve visibility of missing GPU/source/unsupported-state messages without requiring users to search collapsed sections.

No navigation redesign was implemented in this review.
