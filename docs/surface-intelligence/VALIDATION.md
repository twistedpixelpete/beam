# Surface Intelligence validation · 0.13.0 Internal Beta

Historical pre-review validation. See [PR #8 review and field acceptance](PR8-REVIEW.md) for the final corrected source, rerun results and refreshed example assets.

Maintainer: Twisted Pixel. Tested 25 October 2026 in Blender 5.2.2 LTS (d13f752e3b9c), macOS 26.7, Apple silicon / Metal.

Branch: `feature/beam-surface-intelligence`.
Starting stable main: `b4f8a7a172143f05d7f7998b58574c10e3611755`.
Engineering source commit: `0272f2aeb529bd8bf897e50abcfe404b0cbf3ffd`.
Documentation-generation commits and frozen 0.12.0 assets are not part of this branch. No merge, tag or release is performed.

## Results

- Pure Python suite: **69 tests passed** (all `test_*.py`), including independent illuminance proportionality/incidence and Observer angular-pixel tests.
- Existing Blender milestone runner: **all 15 milestones passed** in a native GPU session. The test harness explicitly updates the region's view matrix after scene switching, avoiding the previously stale startup camera-aspect assertion; assertions themselves remain intact.
- **15 named targeted regression scripts passed**: see `examples/surface-intelligence/regressions.json` and accompanying logs. These cover source maths/visibility, production surfaces, hardening lifecycle/migration/edges, UI context, pre-documentation UI, JSON contract, group lifecycle, screen builder/edges, helper frustums, review regressions, planning and theme.
- New integration passed: optional Observer, angular resolution/distance behaviour, conservative overlap-source selection, viewer-only occluder, native duplicate identity, mode-specific stale state, fixed/target display-only invariants, Observer and enum save/reopen, cache reset, and all 12 workload cases.
- New A/B integration passed: flat reference, Euclidean sample distance, lumens, stack, additive overlap, blocked zero contribution, deterministic samples, independent tilted-plane lux formula, stepped and curved distance checks.
- Matching Mapping Matter counterpart fixtures passed: flat, angled, two-source overlap, blocker and equivalent Observer. Numeric results are `reference/beam-counterparts.json`.
- **All five modes exported** as 1400 × 900 PNGs plus hash-linked sidecars and a Study Package. Schema validation, image hashes, source IDs, observer thresholds and uniformity bounds passed. Existing three-view Density/Stretch PATCH package validation also passed unchanged.
- Existing native GPU engineering review passed: Position/Reflow Undo/Redo, Reverse Mapping isolation and persistence, three GPU enable/disable cycles with no orphan wrappers/images, two unregister/register cycles with no surviving handlers or screen timer.
- Native UI inspected: dropdown lists all five modes; Observer fields appear for Acuity; Analyse Surface executed from the inspector at 512 samples and reported 1.63 / 1.68 / 1.70 arcmin and 0% below / 100% at-or-above the 1 arcminute threshold for the selected fixture. Screenshots are included. The original user Blender session was not used for testing.

## Performance

CPU solve wall time, one measurement per workload, with an Observer. One shared pass calculates all five metrics, so the listed solve time is the same cost whichever display mode is selected; it is not five separate measured solves. This synthetic plane stresses source count and sample budget, not a huge imported venue. GPU batch creation is excluded from this matrix. Explicit analysis may block Blender while it runs.

| Projectors | 512 samples | 2048 samples | 8192 samples |
|---|---|---|---|
| 1 | 0.010 s | 0.040 s | 0.176 s |
| 3 | 0.028 s | 0.103 s | 0.432 s |
| 16 | 0.136 s | 0.530 s | 2.133 s |
| 32 | 0.291 s | 1.081 s | 4.274 s |

Full per-mode records: `examples/surface-intelligence/performance.json`. GPU image export after the shared analysis took approximately 16–25 ms per view in the simple fixture; these are export timings, not viewport FPS. An independent eight-projector / 23-venue-mesh Reverse Mapping sanity fixture measured median idle refresh 1.84 ms and movement refresh 4.21 ms, with zero extra idle uploads. See `interactive-performance.json`; these are operation costs, not a guarantee for arbitrary scenes.

## Evidence and reproducibility

- `tests/test_surface_intelligence.py`: pure analytic checks.
- `tests/blender_surface_intelligence_ab.py`: evaluated geometry and visibility tests.
- `tests/blender_surface_intelligence.py`: integration, fixture authoring and workload matrix; run in disposable factory-startup Blender.
- `tests/blender_surface_reference.py`: matching reference geometry/photometry.
- `tests/verify_surface_intelligence_views.py`: native GPU five-view capture and package export; requires the generated fixture.
- `tests/validate_surface_intelligence_exports.py`: portable schema/hash/reference checks (requires jsonschema).
- `tests/run_blender_tests.py`: existing complete milestone suite, native GPU session.
- Logs: `examples/surface-intelligence/validation/`.

Review the exported PNGs and `Study-Package/index.html`; sample positions and distances in the structured package are explicit SI. The `.blend` deliberately contains no persisted analysis cache; re-analyse after opening. Fixture generation tests can replace the fixture; rerun the native GPU capture to restore its five Study Views.

## Issues and limitations

No known engineering blocker remains in the implemented modes. A final depsgraph test found that a luminous-flux edit also marked Density stale because Blender tagged the projector body geometrically. The analysis geometry handler now excludes projector bodies, while runtime still tracks their transforms; the post-update-cycle cache test passes. A zero-lux constant-scale edge case was also corrected to use the dark palette endpoint, with a regression test. During test expansion the save/reopen harness briefly lost its active-projector pointer after deleting a temporary coarse-resolution source; the harness now explicitly restores the intended active projector before saving. This was a test setup assumption, not a change to Beam selection behaviour.

Mapping Matter's nominal flat lux agrees to rounding; its blending ON/OFF semantics differ and its angled centre label remains nominal. Exact spatial min/avg/max lux, numeric distance and human-acuity parity were not available. See MAPPING_MATTER_COMPARISON.md for observed facts and limitations. A test-only box and Observer were removed and original geometry restored without saving the external scene.

PATCH's receiving GUI and Designer's receiving application were not tested in this milestone. Existing CSV and structured contracts passed their regression checks; the additive new data is supplied for importer review. Sampling can miss thin features. Materials are treated as opaque, two-sided. Illuminance is a planning estimate; distance is not optical focus certification; acuity is adjustable guidance. Fixed lux maximum starts at zero; no logarithmic scale is implemented.

## Recommendation

Recommend **0.13.0 as the next internal-beta candidate**, subject to PR review and user field testing. Keep the 0.12.0 onboarding baseline intact until the new build is accepted. Do not label this stable or claim end-to-end PATCH compatibility.
