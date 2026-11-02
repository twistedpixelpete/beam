# Roadmap
Beam by Twisted Pixel

Reviewed: 2 November 2026.

## Current priority
**Feature freeze.** Beam's results have held up in real use; usability is what needs work. No new features until U1 is accepted by the maintainer. Beam 0.14.0 is the current Internal Production Beta release. R1 and the Reverse Mapping redraw fix are merged to `main`, but not yet in a release. No committed delivery dates are implied.

## How to read this
| Status | Meaning |
|---|---|
| COMPLETE | Released or merged, with its evidence recorded |
| ACTIVE | Being worked on now |
| ON A BRANCH | Implemented and awaiting review |
| PROPOSED | Recommended, not approved |
| OPEN | Needs testing or a decision rather than new code |
| FUTURE | Recorded as useful; deliberately not started |

Every feature is tested in the [feature test scene](TESTING.md). Classify new findings as BUG, POLISH, DOCUMENTATION or FUTURE FEATURE. Normal fixes branch from current `main`. This page doesn't claim exhaustive testing, zero bugs or production readiness.

## U1 — ACTIVE: Usability
Judged by planning a real job from start to finish, not by tests. From a review of the interface code on 2 November 2026; the maintainer's hands-on findings take priority over this order.

**Merged to `main`**
- Position and rotation fields for projectors, screens and Blend Groups, at the top of the inspector and in world space.
- Aim tools moved from a closed section near the bottom to the top.
- Selecting a helper camera or light offers a button to select its projector.
- Select Whole Group from a group member.
- The Beam workspace opens on the Move tool.
- Surface Analysis stays in one place, instead of jumping above the inspector once it has a result.

**Agreed direction (maintainer, 2 November 2026)**
Beam stays in the right-hand column. Tabs follow the job: Projector, Screen, Blend, Surface, Views, Export. Each stage is its own pull request with no change to calculated or export values.

1. **On a branch (`ux/compact-header`).** Shorter header, with warnings beside what they affect.
2. **On a branch (`ux/surface-tab`).** A Surface tab for Surface Analysis and Reverse Mapping, and a project dropdown for project details, units, display and mode. This removes the sections repeated on every tab.
3. **On a branch (`ux/tab-order`).** Order each tab by how often it's used, and choose what opens by default.
4. Plain names and clearer errors, using a word list the maintainer approves first.

**Next, proposed**
- Selecting in files with an existing Beam workspace can still land on Select Circle, where a click on a projector's body selects nothing. Decide whether Beam should warn or correct this.
- "Technical" is both a status and a button, and its meaning isn't obvious.
- "Active", "Selected" and "Pinned" can name three different objects at once. Make it clear what the controls are acting on.
- Display units apply to Beam's readouts, while position fields use Blender's scene units. Make them agree.
- Layout slots and helper objects clutter the Outliner.
- Exports need a clearer choice between the two CSV formats, and clearer feedback on what was written and where.
- Screen Builder shows every parameter at once. Show only those for the chosen type.

## R0 — COMPLETE: 0.14.0 baseline
Projector planning, Screens, Blend Groups, Auto Blend, Inverse Solver, Optics Guidance, Study Views, Reverse Mapping, Surface Intelligence, optional Cycles projection and the JSON, CSV and Study Package exports. See the [0.14.0 release notes](RELEASE-0.14.0.md).

## R1 — COMPLETE: Runtime resilience and scale
Merged to `main`, not yet in a release.

- A failing background update retries and shows in the Beam panel, instead of stopping live updates for the session.
- A copied Blend Group that can't be rebuilt keeps its objects and is no longer retried every tick.
- Surfaces are held in arrays, and moving an object no longer re-reads its mesh or rebuilds its ray-cast tree.
- Quiet timer ticks skip whole-scene scans. A heartbeat of at least one second catches anything Blender doesn't report.

Measured headless on Apple silicon with Blender 5.2.2, before and after:

| Case | Before | After |
|---|---:|---:|
| Idle tick, 5,000 objects and 32 projectors | 25 ms | 0.2 ms, plus a 10 ms scan each second |
| Idle tick, 20,000 objects and 32 projectors | 122 ms | 0.9 ms, plus a 45 ms scan each second |
| Move a 1M-vertex mesh | 1.2 s | 42 ms |
| Move a 4M-vertex mesh | 5.0 s | 172 ms |
| Edit a 4M-vertex mesh | 5.0 s | 1.1 s |
| Analyse 512 samples on a 4M-vertex mesh | 3.6 s | 0.7 s |

Peak memory for a 4M-vertex mesh falls from 2.4 GB to 1.0 GB, measured on Linux.

Validation: 75 pure tests and all background suites on Linux, plus milestones 1–15 and the projection, view export, review, planning and Reverse Mapping persistence GPU suites on Metal. Not yet covered: interactive use on a real production file.

## R2 — PROPOSED: Correctness follow-ups
From the code review of 2 November 2026.

1. **BUG, fixed on `main`.** Reverse Mapping redrew continuously while idle: 112 draws per second on Apple silicon/Metal before the fix, 0 after. Shader values were compared at a tolerance 32-bit floats can't meet, so they were rewritten on every draw.
2. **BUG, risk.** Reverse Mapping creates and removes materials and node groups during viewport drawing. Move this out of the draw callback.
3. **Decided, no change.** Surface Analysis "All projectors" keeps counting every projector in the scene, including those hidden, excluded from export or with output off. Reverse Mapping's "All Active" is a different rule and excludes inactive projectors.
4. **BUG.** The combined blend preview uses the first member's content in the viewport and the anchor's in Cycles.
5. **BUG.** Exported files are readable only by their owner (`0600`), study package folders likewise (`0700`), and overwriting a file changes its permissions.
6. **BUG.** Selecting a member of another Blend Group marks analysis stale even when its scope is not Group.
7. **POLISH.** `Venue_r1.5` and `Venue_r1.4` both export as `Venue_r1.csv`.
8. **POLISH.** Beam JSON export doesn't resolve `//` paths and is the only export written non-atomically.
9. **Risk, not reproduced.** Cycles `render_pre` edits scene data from a handler that can run alongside other threads.
10. **Risk, not reproduced.** `_owners` survives file load, so a reused memory address could rewrite projector identities. It took a forced swap to trigger, with no natural case in 100 reopens.

## R3 — PROPOSED: Open-source readiness
- Ship the full GPL-3.0 text and a root `LICENSE`. The current file is a short notice that still says "Projection Study".
- Move `examples/` and `output/` binaries (about 312 MB) to release assets. Rewriting Git history to remove them is a separate maintainer decision.
- Remove personal paths from tracked validation logs (25 files).
- Add a note that Beam isn't affiliated with or endorsed by Mapping Matter or disguise, and review the captured Mapping Matter CSV fixtures against its terms.
- Decide whether the original build request documents in `docs/` stay public.
- Add contribution guidance and bring `TEST_RESULTS.txt` up to date. It currently stops at 0.12.
- Run background suites in GitHub Actions using the `bpy` package.
- Format the source and break up the most complex functions (`cycles_projection.sync`, `screen_uv.diagnose`, `runtime.repair_identities`).
- Revise the onboarding package and training files for Cycles. They still describe 0.13.

## R4 — OPEN: Platform validation
Beam is validated primarily on Blender 5.2.2 LTS, macOS and Apple silicon/Metal.

- Windows and Linux in interactive use. Background suites pass on the Blender 5.2.3 `bpy` package for Linux, but that covers no GPU drawing.
- Cycles projection on Metal, CUDA and OptiX. Its recorded validation is macOS CPU.
- Other Blender versions, including a full pass on the declared 4.5 minimum.
- Large production scenes, extreme optics, and linked or animated workflows.

## R5 — OPEN: Interchange validation
- Direct import into the Designer application. Designer CSV is so far proven only through Mapping Matter's importer.
- Manual PATCH Study Package import through its interface. The automated importer test passed.
- Mapping Matter comparison on stepped and curved receivers, and its off-axis density and stretch definitions.
- Real shifted and coupled lens envelopes. Unknown limits stay explicit and are never assumed.
- Gimbal-boundary and wrapped-angle equivalents.

## R6 — PROPOSED: Further scale work
- Reduce rebuild cost for repeated geometry edits on venue scans, which still take about a second on a 4M-vertex mesh.
- Add progress and cancel to Surface Analysis, which currently blocks Blender until it finishes.
- Add a benchmark to CI so idle and heavy-mesh costs can't regress unnoticed.

## Future — not started
Recorded in [follow-up gaps](surface-intelligence/FOLLOW_UP_GAPS.md):

- Logarithmic photometric scale.
- Blend-attenuated brightness preview. It needs a defined attenuation model first.
- Per-surface analysis summary across several receivers.
- Observer look-through composition controls.
- Luminance, only with a clearly separate reflectance and observer model.

Beam won't copy an undefined focus metric or claim calibrated photometry.

## Stable release — criteria to be agreed
Beam remains a beta with no stable release date. Before one is set, the maintainer needs to decide the required platforms and which of R2, R4 and R5 are prerequisites.
