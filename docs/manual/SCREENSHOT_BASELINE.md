# Screenshot baseline - Beam 0.12.0

25 October 2026. Blender 5.2.2 LTS / macOS 26.7 / Metal. Actual native UI captures, not mockups. See [Documentation Baseline](DOCUMENTATION_BASELINE.md) for the source freeze.

## Current candidates

All paths below are relative to `examples/manual-baseline/`. Full-window captures are 3600 px wide; pair them with inspector crops in the manual so text stays legible. Keep the original PNGs. These are baseline candidates, not a finished annotated manual.

| Subject | Preferred image | Source |
|---|---|---|
| Workspace, module rail, native tools, Outliner | `projector.png` | Fresh native workspace acceptance |
| Projector controls / calculated values | `projector-inspector.png` | Same |
| Inline pencil target / checkmark Apply | `inline-target-inspector.png` | Same |
| Screen creation/editing | `screen-inspector.png` | Same |
| Blend members / overlap / Reflow | `blend-inspector.png` | Same |
| Study Views | `views-inspector.png` | Same |
| Export | `export-inspector.png` | Same |
| Reverse Mapping receiver state | `reverse-inspector.png` | Same; receiver section may require scrolling for mode controls |
| Surface Analysis / Density | `analysis-inspector.png`, `analysis.png` | Fresh baseline capture |
| Stretch mode | `stretch-inspector.png`, `stretch.png` | Same; planar fixture has little stretch by design |
| Real model/lens / known vs unknown limits | `optics-inspector.png` | Native disclosure opened; narrow Properties truncates Projector Preset label, so widen for the manual |
| Hidden toolbar action fallback | `hidden-toolbar.png` | Native toolbar hidden; Frame/Solo/Lock remain in inspector |

`Beam-Documentation-Baseline.blend` is the small, deterministic four-projector, one-screen, one-group source scene based on the existing PATCH fixture. It contains real Panasonic optics, Study Views, valid UV/pattern material and analysis settings. Open with Beam enabled; run Analyse Surface after loading. Select the screen to expose Reverse Mapping; use Test Pattern if reviewing mapped content. This is a screenshot fixture, **not the final training project**. Other module captures come from the deterministic workspace test scene; neither is client data.

Regenerate module captures with `tests/verify_ui_workspace.py -- --beam-theme --beam-refinement` in a disposable native Blender process. Regenerate analysis/optics/fallback captures with `tests/capture_pre_doc_baseline.py` and `--enable-event-simulate`. The disclosure click is calibrated to the captured 3600 x 2084 desktop; inspect the result if display dimensions differ. Pre-create and verify the disposable configuration folder before starting Blender.

## Asset classification

[ASSET_INVENTORY.csv](ASSET_INVENTORY.csv) inventories every repository example PNG/JPEG/Blend file with its classification and hash. Classification describes provenance and suitability, not a claim that every historical control was revalidated.

- **CURRENT:** new `manual-baseline` captures and source scene; appropriate reference for the documentation build.
- **TEST EVIDENCE:** `parity`, `production`, `hardening`; retain fixture hashes, numerical comparison images and earlier analysis evidence. Do not relabel old test screenshots as new UI captures.
- **HISTORICAL:** numbered milestones and earlier UI/theme-workspace directories; still valuable for migration and design history. README's 0.8.1 hero is explicitly labelled historical.
- **OBSOLETE:** no tracked screenshot/scene was confidently disposable. None was deleted. Temporary test output stays in ignored `work/`; paused onboarding output is preserved there separately.

The UI uses native icons. Wide rail labels, narrow icons, five active-module states and hidden-toolbar fallback are covered by `blender_pre_doc_ui.py`; fresh native screenshots and workspace acceptance cover the real renderer and inspector navigation. Future manual annotations must distinguish the left Beam rail from Blender's native tools above it.
