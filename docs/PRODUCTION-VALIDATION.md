# Beam 0.11 production validation — development beta

Maintainer: **Twisted Pixel**. Tested 24 October 2026 on Blender 5.2.2 LTS, macOS/Metal. Still in testing; not a stable release. PATCH Documents owns client-facing document generation. This pass adds technical exports and evidence, not a document-layout engine.

## Branch and review

Mapping Matter parity PR [#4](https://github.com/twistedpixelpete/beam/pull/4) was reviewed, retested and merged to main at `5f35a250bb202da912cdf16af0ce04a78dad5e18`. The working tree was clean before this milestone. All subsequent work is on `feature/beam-production-validation`. No changes to the owner-only main branch policy were needed.

## Two explicit CSV formats

Export → Projector Data provides Mapping Matter CSV, Designer CSV and Beam JSON; the Study Package remains available below. Both CSV exporters share authoritative Beam state and `transform_conversion.py`.

| Property | Mapping Matter CSV | Designer Projector Study CSV |
|---|---|---|
| Convention | `beam_mapping_matter_transform_v1` | `beam_designer_transform_v1` |
| Position | Blender XYZ, millimetres | Blender XZY, metres |
| Neutral frame | Forward +Y, up +Z | Same physical frame, imported through Designer study schema |
| Rotation | `Rz(yaw) Rx(pitch) Ry(roll)` | CSV X=pitch, Y=−yaw, Z=−roll, derived from the same canonical rotation |
| Lens shift | Twice Beam full-image percentage | Beam percentage / 50 (fraction of half-image size) |
| Target | Virtual optical-axis point at shifted centre-hit axial depth | No target columns; receiving scene determines first hit |
| Validation | Controlled Mapping Matter exports | Actual Mapping Matter Designer-CSV import and re-export |

Designer columns are exactly: Name, Resolution X, Resolution Y, Brightness (lum), Throw Ratio, Lens Shift Horizontal, Lens Shift Vertical, Position X (m), Position Y (m), Position Z (m), Rotation X (deg), Rotation Y (deg), Rotation Z (deg). They were verified against the live importer, not inferred from similar schemas. [Designer documentation](https://help.disguise.one/designer/stage-setup/projector-simulation/projector-studies) provides context; live import is the compatibility evidence.

Ten generated Beam fixtures were imported into Mapping Matter and individually re-exported. Position, aim/target, throw, orientation, shifts, ratio and raster match within 0.02 per numeric field (mm/degrees); maximum observed difference <0.001770. Count and names matched. [Raw fixture provenance](../tests/fixtures/designer/README.md). **The disguise Designer application itself was not tested.** Internally tested gimbal cases are not externally validated.

Euler output uses Blender's deterministic YXZ canonicalisation after removing Beam's base optical rotation. Equivalent wrapped inputs may export different angle triples from their original input but preserve the rotation. At singularity roll/yaw are not independently identifiable. Twenty-eight ±90°/near-90°/wrapped/combined cases reconstruct within 5×10⁻⁵ matrix-element tolerance; Blender's near-singular canonicalisation can lose about 0.002° in this region. Consumers should compare rotation matrices, not raw Euler triples.

Each CSV has a `.metadata.json` with exporter version, separate convention ID, timestamp, UUID/name references and SHA-256 of exact CSV bytes. Verify the hash before trusting a sidecar. Two files cannot be atomically replaced together; interrupted replacement is detectable. Earlier exports are not reinterpreted: retain their original convention or re-export from the original Beam scene. A missing sidecar means unknown provenance, not permission to assume current semantics.

## Sourced optics

Small deliberately conservative library: four real projector models, seven compatible lenses. Generic / Manual stays unrestricted. Choosing a preset does not silently change the raster/light output; Use Preset Values does. Unknown shifts block nonzero shifted solves/layouts; no guessed clamping or automatic lens substitution.

| Projector | Native raster / nominal light | Lenses / throw ranges | Official reference |
|---|---|---|---|
| Panasonic PT-RZ990 | 1920×1200 / 9400 lm normal ISO | ET-DLE150 1.30–1.89; ET-DLE170 1.71–2.41 | [RZ990series_G2 pp1–2](https://docs.connect.panasonic.com/projector/download/catalog/pdf/PT_RZ990_S_2P_ctlg_Eng_PC.pdf) |
| Epson EB-PU2010B | 1920×1200 / 10000 lm normal | ELPLM15 1.57–2.56; ELPLW08 0.86–1.21 | [r1.02 pp5,10,26](https://files.support.epson.com/pdf/specs/specifications_ebpu2010series_en_r102.pdf) |
| Christie 4K10-HS | 2716×1528 / 10000 ANSI lm | 0.85–1.02 | [July 2023 p2](https://www.christiedigital.com/globalassets/resources/public/4k7-4k10-hs-datasheet.pdf) |
| Barco G100-W22 | 1920×1200 / 18500 ANSI lm | GC 1.2–1.5; GC 1.5–2.0 | [G100-W22 specification sheet](https://assets.barco.com/m/65f051bcac7e2970/original/G100-W22-en-Spec-sheet.pdf) |

Source revision (where available), checked date, light-output basis and shift convention are embedded in presets and exported packages. Panasonic's centre-lumen rating and Barco's ISO-lumen rating are not substituted for the listed figures. Epson ELPLM08 is not included as a PU2010-compatible lens. Epson distance-formula intercepts are not modelled. Lens throw ranges remain nominal planning guidance; physical offsets, coupled shift envelopes and installation tolerances require manufacturer verification. All real shift envelopes are explicitly unknown.

Valid width, height and position solves pass for all seven lenses. Below/above-range, unknown shift and locked solves fail without partial mutations. A real Barco Auto Blend preserves raster/model/lens; invalid selected optics rejects creation without adding objects/groups.

## Analysis images and PATCH contract

Analyse Surface, then Views → This View · Export Annotations → Analysis Overlay: None, Density or Stretch. Export This View or the Study Package. A current GPU analysis is required; absent/stale results reject before image output. Camera/helper changes no longer spuriously invalidate analysis; receiver/projector changes still do. Drawing reads cached samples only and uses the saved camera with a depth pass.

Images include sample heatmap, compact gradient legend, min/average/max, visible coverage and overlap. Density uses best visible projector's conservative worst-direction density. Stretch reports that same projector's anisotropy; colours saturate at 3:1, while statistics retain the full value. Density colour endpoints are the current sample minimum/maximum. Grey is uncovered. Overlap is percent of total sampled receiver area.

Additive v1 JSON fields: `export_formats`, `study_guidance`, view `analysis_overlay` / `analysis_image`, analysis `analysis_uuid` / `generated_at`, and min/average anisotropy. Existing fields and convention identifiers remain. Image metadata includes source analysis UUID, receiver/projector UUIDs, statistics/sample count, generation time, opaque first-hit method and limitations. PNG sidecars include file hash; package view records repeat the same metadata. Reference validation rejects mismatched analysis source/statistics/mode. UUIDs, not names, are authoritative.

The [PATCH development fixture](../examples/production/PATCH-study-package/beam-study.json) contains project/venue/revision, one screen, four Panasonic projectors, a Blend Group, overview/density/stretch images, sourced optics and warnings. Both analysis images refer to the same analysis UUID. Assets are UUID-named; committed UUIDs are stable for consumers (regenerating the fixture creates a new study). This validates Beam's package contract and assets; **an actual PATCH application import was not performed**. The existing HTML reader is unchanged.

Guidance defaults are centrally defined in `study_guidance.py` and exported: 100 px/m minimum, 99.5% coverage, 2:1 anisotropy. These are **Beam study guidance thresholds**, not universal industry pass/fail specifications. No new configuration panel is added.

## Surface acceptance and limits

Stepped, curved, disconnected and flat receivers pass at 512/2048/8192 samples, including two-projector overlap. A 0.2 mm-thick blocker reduces visible coverage while nominal coverage remains; a closed box exposes its front, not its hidden rear faces. Existing angled/synthetic/MM reference tests remain. Analysis is deterministic equal-area sampling, opaque two-sided evaluated geometry, not exact integration. Small features and between-sample occluders may be missed. Transparent materials are treated opaque; excluded/hidden geometry is untested. Optional extra external curved-surface comparison was not performed.

## Performance

Disposable scene: 288 curved auditorium seats, stage steps, trusses (32,968 venue vertices / 36,946 polygons), 4/8 screens and Blend Groups, 16/32 projectors, labels/frustums/output, one Reverse Mapping receiver and a Study View. Three timed repetitions per operation, ten idle repetitions. Blend overlap caches are cleared before each timed recalculation. Fresh-process reopen includes loading plus Beam rebuild; repeated reads benefit from OS cache. Analysis measures one receiver against all projectors. View/package exports use 1200×750 images. Interactive refresh and Reverse Mapping numbers measure CPU update/submission, not GPU-completed display latency. No FPS claim.

Platform: macOS-26.7-arm64-arm-64bit-Mach-O; Blender 5.2.2 LTS; Apple M5 Max; GPU backend Metal API.

| Operation | 16 projectors median / max (ms) | 32 projectors median / max (ms) |
|---|---:|---:|
| idle update | 0.37 / 0.41 | 1.04 / 1.08 |
| projector transform refresh | 1.04 / 1.17 | 2.41 / 2.56 |
| blend overlap recalculation | 0.81 / 0.95 | 1.57 / 1.63 |
| multi group movement | 1.66 / 1.68 | 4.07 / 4.10 |
| analysis 512 | 23.93 / 23.96 | 41.67 / 43.49 |
| analysis 2048 | 88.33 / 97.59 | 153.82 / 156.09 |
| analysis 8192 | 350.68 / 353.25 | 591.86 / 613.64 |
| reverse mapping refresh | 1.34 / 6.33 | 2.90 / 9.59 |
| study view export | 169.28 / 245.63 | 206.18 / 211.08 |
| study package export | 221.65 / 222.48 | 243.99 / 249.35 |
| save | 15.13 / 21.72 | 20.74 / 25.31 |
| reopen and rebuild | 56.99 / 63.70 | 62.26 / 64.98 |

No speculative projection-engine optimisation was warranted: interaction costs were small in this workload. Analysis remains explicit. Results are machine/scene-specific and do not guarantee arbitrary production scenes. The initial benchmark harness retained invalidated Blender collection references and crashed; reacquiring group references after construction fixed the harness. Final measurements above come from completed runs.

## Validation summary

- 55 pure Python tests.
- Blender milestones 1–15, including CSV/JSON, Undo/Redo, persistence, GPU projection and image exports.
- Engineering regression, planning, Blend Group lifecycle, frustum, JSON contract, screen builder/edges/beauty, UI context, theme and apply/restore suites.
- Native workspace and engineering GPU suites; actual result files checked, not just process exit codes.
- Ten live Mapping Matter roundtrips; current exporter regenerates the imported CSV byte-for-byte. Twenty-eight internal Euler edge cases.
- Seven real lenses, inverse failures/rollback, real Auto Blend and invalid-layout rollback.
- Further sampled surface fixtures; 16/32-projector benchmark and reopen persistence.
- Native density/stretch Study View export, stale rejection, image hashes and metadata joins. JSON schemas and negative validation claims pass.

The former milestone-12 assertion expected “Export CSV”; it now expects the intentionally renamed “Export Mapping Matter CSV”. No projection-behaviour assertion was removed.

## Changed components

New Designer exporter and shared conversion helpers; sourced optics library/feedback; cached analysis image drawing and metadata; saved-view controls; additive JSON schemas/report relationships; central study-guidance definitions; regression and benchmark scripts; PATCH fixture and evidence. Version advances to 0.11.0 development beta. No installation into the user's live Blender session and no release publication are performed by this milestone.
