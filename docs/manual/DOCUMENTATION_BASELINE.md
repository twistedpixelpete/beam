# Beam documentation baseline

**READY FOR DOCUMENTATION** - 25 October 2026.

Maintainer: **Twisted Pixel**. **Beam Internal Production Beta, 0.12.0**. Unreleased candidate; no public/stable release or tag was created. This baseline authorises accurate documentation of the tested build, not additional platform/compatibility claims.

| Item | Frozen value |
|---|---|
| Product/source commit | `15e054ae7d7d7700549bbeb0dc4d54c18779d39c` |
| Branch | `feature/beam-pre-doc-cleanup` |
| Base main / merged PR #6 | `3ff2982b4fd5cdbd04eda2b7b5417c5079fc716b` |
| Extension version | `0.12.0`, authoritative `projection_study/blender_manifest.toml` |
| Blender | 5.2.2 LTS, build `d13f752e3b9c` |
| OS / renderer | macOS 26.7 (25G229), Apple M5 Max / Metal |
| Current screenshot set | [Screenshot Baseline](SCREENSHOT_BASELINE.md) |
| Screenshot source scene | [Beam-Documentation-Baseline.blend](../../examples/manual-baseline/Beam-Documentation-Baseline.blend) |
| Audit and recovery notes | [Cleanup Audit](CLEANUP_AUDIT.md) |
| Machine-readable results | [VALIDATION.json](VALIDATION.json) |

Later commits on this branch may add baseline documentation/assets only. The source commit above identifies the product code that was tested. Re-freeze if product behaviour or labels change. Historical reports and fixture producer/schema/exporter versions retain their original meanings.

## Final verification

- **55/55 standalone Python tests PASS.**
- **Blender milestones 1-15 PASS:** projection, targeting, outputs/GPU, exports, inverse operations, persistence and native Undo/Redo.
- **13 background suites PASS:** review regressions, planning, group lifecycle, frustum helpers, JSON contract, screen builder, screen edges, screen beauty, UI context (now eight cases), theme, parity, production and surface production.
- **Apply/Restore PASS across processes**, using a newly created configuration; repeat Apply preserves the original backup. Registration/workspace opening do not apply the theme automatically.
- **Native workspace and engineering GPU acceptance PASS**, with result files checked, not only process exit codes.
- **Fresh ZIP install/use/reopen PASS.** Installed extension loads in a fresh Blender process; all first-use operations, two CSV formats, JSON/package, analysis and Reverse Mapping exercised. One Beam workspace persists without duplicates. Isolated config/repository paths are asserted before writes.
- **Rail contract PASS:** narrow icons, wide labels, all five active states/tooltips, hidden-toolbar fallback. Fresh native screenshots verify rendered controls.
- **Hardening lifecycle and 24 interop edge cases PASS.**
- **Five-generation migration PASS eight consecutive times after the cache fix.** Historical files remain unchanged; only disposable copies are saved.
- **32-projector / 360-edit soak PASS after the fix**, including group moves, overlap/lens changes, analysis exports, Undo/Redo, save/reopen, stable counts and UUID checks. Four unfreed blocks / 0.001907 MB reported at Blender shutdown; allocation-level leak freedom is not certified.
- **Reverse Mapping persistence PASS:** original materials restored after reopen, no extra depth uploads/material rebuilds across ten forced idle redraws. Installed-build acceptance also tests all three main source choices and all four modes.
- **Study Package schema/asset/reference checks PASS**, including the unchanged committed PATCH fixture and newly exported first-use package. No schema or convention changes.

These results combine scripted native-operator workflows, UI interaction tests and visual inspection. They do not claim an independent unassisted-user study. Test-harness incidents, including the recovered preference write, are disclosed in the audit.

## Exact documentation terminology

| Area | Current labels / important distinction |
|---|---|
| Modules | Projector, Screen, Blend, Views, Export |
| Workspace / theme | Open Beam Workspace; Apply Beam Theme; Restore Previous Theme |
| State | Selected = native Blender selection; Active = Beam context; Pinned = retained Beam context; Receiver = surface being inspected |
| Projector | New Projector; Duplicate; Projection; Calculated; Optics Guidance; Aim / Position; This Projector · Annotations |
| Solver | Pencil beside Calculated value; Solve By; checkmark applies (tooltip Apply Target); X cancels |
| Screen | New Screen toggle; Create Screen; Update Screen; Test Pattern; Neutral |
| Blend | New Blend; From Selection; New Auto Blend creates a group; Reflow Group changes the current group |
| View | New Study View; View; Exit; Previous; Next; Export This View |
| Analysis | Surface Analysis; Receiver; Projectors; Samples; Analyse Surface; Show Heatmap; Heatmap: Density / Stretch |
| Analysis source | Active projector; Active Blend Group; All projectors |
| Reverse Mapping source | Coverage From: Active Projector / Selected Projector / Blend Group / All Active Projectors |
| Reverse Mapping modes | Covered Only; Uncovered Dimmed; Uncovered Hidden; Overlap Diagnostic |
| Reverse Mapping actions | Enable on Receiver; Restore Materials |
| Display | Technical / Presentation toggle; Global · Viewport Display |
| Export | Mapping Matter CSV; Designer CSV; Beam JSON; Study Package · JSON + HTML + Views |

There is no universal flat receiver filter on projector targeting: its centre ray uses the first eligible geometry hit. Reverse Mapping appears when an eligible receiver is selected or already enabled. Analysis source and Reverse Mapping source menus intentionally differ because Selected Projector is an additional explicit Reverse Mapping option. Do not invent identical menus in the guide.

## Documentation limits

Retain standard pinhole/opaque geometry assumptions, sampled analysis gaps, local automatic Density scale, unknown lens-shift envelopes and unsupported conventional UST/mirror modelling. Reverse Mapping requires a GPU viewport and supports at most 32 coverage sources. Reanalyse after opening a file; the analysis cache is transient.

Direct disguise Designer application import and Windows/Linux remain **not validated**. PATCH's application importer is tested programmatically in its integration branch; manual GUI acceptance remains outstanding. Do not present the HTML reader as a finished report-layout system. Narrow Properties areas can truncate long labels: widen the editor before taking final manual close-ups.

The full user guide, Quick Start and training project remain paused. Their next pass should start from this baseline after review; no further feature work is needed to begin documentation.
