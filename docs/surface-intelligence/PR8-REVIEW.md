# PR #8 engineering review and field acceptance

Maintainer: **Twisted Pixel**. Reviewed 25 October 2026. Engineering source: `778e7b5dc61840a242c9accf478358d5908f0880`. PR: https://github.com/twistedpixelpete/beam/pull/8.

**Review outcome: no unresolved blocker found after the fixes below. Ready for controlled Internal Production Beta use on the tested environment, subject to ordinary project verification.** This is an engineering self-review plus scripted/visual validation, not independent third-party certification or an unassisted-user study. No public/stable release or tag.

## Actual review and fixes

Reviewed the ray/plane Jacobian, flux conversion, additive visibility loop, nearest-source distance selection, apparent-pixel singular-value calculation, Observer properties/identities, per-mode invalidation, load/Undo/Redo handlers, GPU batches and legend ranges, saved-view export checks, additive schema and package references.

- **Correctness blocker found and fixed:** moving an Empty collection instance into the beam did not invalidate Surface Analysis. Reproduction changed freshly calculated coverage from 100% to 0% while the old result remained apparently current. The runtime now invalidates analysis when an instancer's evaluated transform/geometry changes. `blender_surface_review.py` reproduces and checks this.
- An initial overly broad collection-update fix also invalidated Distance after a photometric edit. The existing mode-specific integration test caught this; the final correction targets instancer objects. The original assertion was retained and now passes.
- Package wording now says **“Estimated incident illuminance is not photometrically calibrated.”** No photometric maths changed.
- Stretch and Acuity legends now explicitly state their fixed numeric colour ranges and saturation. Statistics still report the full range, including values outside the colour scale.
- Added independent shift and raster-resolution/constant-flux tests. No unrelated feature or UI redesign.

Illuminance is flux per raster pixel divided by local Jacobian area; inverse-square and incidence are not applied again. Stack and brightness scale flux, raster changes preserve total flux, and shift moves the footprint. Distance is Euclidean, nearest visible source, UUID retained, unlit excluded. Acuity uses eye-height/world position, observer first-hit visibility and the coarsest apparent visible source; 1 arcminute remains adjustable guidance. Heavy solving runs only on Analyse Surface; draw callbacks consume cached batches.

Observer workflow remains Add Observer → select OBS01 in viewport/Outliner → move base → set Eye Height/threshold → Analyse. The compact mode dropdown and conditional inputs remain unchanged. Additive schema fields are optional for older documents; legacy Density/Stretch fields and source rules remain intact. No PATCH code was modified.

## Exact validation

Environment: **Blender 5.2.2 LTS**, build `d13f752e3b9c`; **macOS 26.7**, Apple silicon / Metal.

- **71/71 Python tests PASS** (the original 69 plus two new independent flux/shift checks).
- **All 15 existing Blender milestone suites PASS**, native GPU session.
- **21/21 background scripts PASS**: the original 15 targeted regressions, plus instancer review, Surface Intelligence integration/12 workloads, Mapping Matter counterpart fixtures, production, parity and screen beauty. Exact names/exits: [regressions.json](../../examples/surface-intelligence/review-validation/regressions.json).
- Native GPU engineering review PASS: Position/Reflow Undo/Redo, Reverse Mapping, save/reopen, cleanup and repeated register/unregister.
- Native production benchmark PASS at 16 and 32 projectors, including analysis, view/package exports, movement and Reverse Mapping.
- All five synthetic-fixture GPU views and sidecars PASS; legacy three-view Density/Stretch export PASS.
- Architectural field build/export PASS; separate fresh-process persistence, deterministic recalculation and **Observer Undo/Redo PASS**.
- Four portable package checks PASS: five-mode synthetic schema/hashes, six-view field schema/hashes/units/UUID joins, newly generated legacy package, and unchanged committed legacy fixture.
- Extension/source ZIP build PASS. Final post-merge smoke results are recorded with the delivery merge SHA.

Logs and machine-readable evidence: [review-validation](../../examples/surface-intelligence/review-validation). Native GPU scripts' PASS markers/result files were inspected in addition to exit codes. The benchmark reported one unfreed allocation (0.062584 MB) on Blender shutdown; no orphan Beam wrappers/images or extra idle uploads were found, but allocation-level leak freedom is not certified.

## Architectural field scene

[Beam-Civic-Hall-Field.blend](../../examples/surface-intelligence/field/Beam-Civic-Hall-Field.blend): about 215 m² of connected angled, recessed and curved facade; four Christie 4K10-HS / 0.85–1.02 preset projectors at 0.95 throw ratio; portico column/lintel blockers; plaza and steps; a separate Beam Screen; one Blend Group; OBS01 at a plausible audience position with 1.65 m eye height. Nominal lens guidance and unverified shift-envelope limitations remain disclosed; no shifted optics solve is claimed.

| Mode | Field result and interpretation |
|---|---|
| Density | 24.46 / 137.39 / 189.72 px/m; low density on oblique returns; 97.7% coverage and 79.7% receiver overlap. Existing best-density source rule retained. |
| Stretch | 1.00 / 1.25 / 5.93:1; recessed sidewalls stand out, with explicit colour saturation above 3:1. |
| Illuminance | 0.00 / 107.22 / 192.15 lux; additive overlap, darker returns, zero-lit shadows. Min/average uniformity 0 because some receiver samples are unlit. |
| Distance | 13.62 / 17.13 / 19.80 m; 6.18 m variation; all four source UUIDs control different samples. No focus certification. |
| Acuity | 0.77 / 1.06 / 1.40 arcmin; 47.1% below / 52.9% at-or-above 1 arcminute; observer-occluded area excluded. |

Moving the Observer closer increased average angular pitch to 1.438 arcmin; moving farther reduced it to 0.687. Changing the threshold to 0.7 arcmin changed the classification as expected. All persistent identities/settings and six views survived a fresh process; transient results were absent and regenerated deterministically.

Visually inspected Overview, Density, Stretch, Illuminance, Distance and Acuity exports at 1600 × 1000, plus fixed-range lux. Legends are readable and unclipped. Palettes remain restrained and numeric changes are discernible on shaded geometry; overlays intentionally remain sampled points, with visible gaps, rather than interpolated continuous heatmaps. Grey unlit/unobservable samples are distinguishable from the coloured samples. Auto 0–192 lux and fixed 0–250 lux both work here; the 100 lux target is a labelled reference only. **No field evidence justified logarithmic scaling.**

Screenshots and a self-contained six-view package: [field folder](../../examples/surface-intelligence/field). The Overview shows projectors and frustums; technical views frame the facade more tightly. No user production scene was modified.

## Performance

Four-projector field shared solve, 8192 samples: **0.507 seconds** (GPU-session solve including display batch creation). New synthetic CPU measurements:

| Projectors | 512 | 2048 | 8192 |
|---|---|---|---|
| 1 | 0.012 s | 0.044 s | 0.216 s |
| 3 | 0.032 s | 0.125 s | 0.501 s |
| 16 | 0.158 s | 0.596 s | 2.257 s |
| 32 | 0.289 s | 1.102 s | 4.325 s |

These are one shared solve for all metrics, not five independent timings or viewport FPS. The original matrix was 0.010–4.274 s; the rerun is approximately 0.012–4.325 s. Different concurrent system load and single measurements prevent a statistically strong regression claim; no material slowdown was observed. The independent eight-projector native GPU check measured median idle refresh 1.76 ms, movement 4.15 ms and zero additional idle uploads.

The larger venue benchmark measured median 8192-sample analysis 0.418 s (16 projectors) / 0.647 s (32), and group movement 1.84 / 4.04 ms. This differs from the synthetic matrix because fewer sources cover the selected receiver and it has no Observer. Do not compare those workloads as equivalent.

## Comparison, handoff and remaining gaps

Preserve [Mapping Matter comparison](MAPPING_MATTER_COMPARISON.md): 494 lx nominal flat reference versus Beam approximately 493.746 lx. Angled/overlap/shadow visual evidence does not establish sampled spatial parity; Distance/Acuity definitions remain unknown. No new broad parity claim.

[0.13 manual delta](../manual/0.13-SURFACE-INTELLIGENCE-DELTA.md) covers the three modes, Observer workflow, exports, stale results and later manual section updates. Frozen 0.12 assets and documentation baseline are untouched.

[Follow-up gaps](FOLLOW_UP_GAPS.md) remain limited to logarithmic scale when needed, a separately defined blend-attenuated preview, multi-receiver summaries, Observer look-through, and future luminance with a proper reflectance model. No new features were added from that list. PATCH/Designer receiving GUIs and other OS/Blender combinations remain unverified.
