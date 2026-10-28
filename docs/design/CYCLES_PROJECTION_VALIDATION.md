# Cycles Render candidate validation

2026-10-28 · feature/cycles-projection · Beam 0.14.0 internal beta candidate.
Base: main `03eeffaeea7274df370a5e473c297b846e75e618`.

## Scope and implementation

Optional Cycles spot-light projection, shared raster node group, content-image reuse,
bounded packed CPU patterns, tight frustum-enclosing cones, change-based parameter
synchronization and a pre-render hook. Separate owned helper collections preserve
source collection render/exclusion behaviour per view layer. User materials, lights
and source images are not rewritten. Planning calculations remain unchanged.

Unlike the initial study, this implementation now has rendered evidence. Names and
labels are rendered into generated calibration/identifier patterns; image and Blender
UV/colour-grid sources are used directly. Engineering annotation overlays remain
viewport/study-export features. No public release or tag is created by this work.

## Platforms and tests

Mac, Apple silicon, CPU renders on:

- Installed Blender 5.2.2 LTS.
- Official Blender 4.5.0 arm64 image, mounted read-only for testing. SHA256 verified
  against Blender's published checksum:
  `f03e5ae7813db62c8664176b62638e12c1413cd9d59a883bb7bfb67cbaa8c52e`.

Both versions pass:

- `tests/blender_cycles_render.py`: solid raster extents, signed H/V shift,
  asymmetric image orientation, rotated rig, centimetre/metre brightness parity,
  full-HD edge alignment, opaque receiver, alpha-image holes, fractional and layered
  transparency, all seven output modes, missing image, combined-canvas anchor
  selection, edge-weight inputs and switch-back cleanup.
- `tests/blender_cycles_lifecycle.py`: planning records and JSON engineering export unchanged, all output images,
  no idle graph rebuilding, independent duplicates, native copied light data,
  hide/show, non-Cycles engine suppression, source collection exclusions/render
  visibility, separate scene rigs, save/reopen, owned resource cleanup and preservation
  of user lights when disabling the add-on.
- `tests/blender_cycles_undo.py`: real Blender undo and redo of mode and generated rig.

Rendered full-HD edge error: **0.7875 projector pixels maximum** in the shifted flat
screen case on both versions (1920 × 1080 source, 3072 × 2048 render, box filter).
This is a measured test-case result, not a guarantee for every possible extreme lens
shift, aspect ratio or image filter.

A black 50%-transparent cloth gave **0.25** of the unobstructed pixel value: the light
and camera each traverse it. Two such cloths gave **0.0625** (within float tolerance).
The white opaque half receives the projected image at its own nearer throw distance;
the transparent half exposes the projected backdrop. Assertions use scene-linear EXR
pixels; PNGs are previews. Representative actual previews were visually inspected.

Existing 5.2.2 regression tests passed: projector body, frustum clipping, Blend Group
lifecycle, Surface Intelligence and JSON interchange contract. Generated historical
fixture changes were preserved in ignored work evidence and restored from the baseline,
so they are not included as unrelated changes in this branch.

The install ZIP was extracted to a temporary directory and imported there in a fresh
Blender process; creating and cleaning up its render rig passed.

## Small-scene performance

`tools/studies/benchmark_cycles_projection.py`: CPU, 256 × 160, 8 samples, persistent
data, fixed seed, three warmed trials after an initial render. Projectors overlap on
a simple backdrop. Wide-cone energy is adjusted to preserve angular intensity. All
cases share one raster node group. Values below are warmed medians in milliseconds.

| Blender | Lights | Tight cone | Nearly-180° cone | Idle sync |
| --- | ---: | ---: | ---: | ---: |
| 5.2.2 | 1 | 9.75 | 10.93 | 0.024 |
| 5.2.2 | 4 | 11.08 | 13.23 | 0.084 |
| 5.2.2 | 16 | 14.30 | 17.91 | 0.425 |
| 4.5.0 | 1 | 10.80 | 11.15 | 0.025 |
| 4.5.0 | 4 | 11.54 | 13.71 | 0.088 |
| 4.5.0 | 16 | 14.50 | 17.77 | 0.419 |

This small fixture supports tight cones and shared math as sensible defaults. It
cannot predict a venue scene's throughput or GPU behaviour. The timer checks at 5 Hz;
unchanged lights retain their nodes, images and parameters. Transform changes update
only transforms; source changes reuse images where possible. Background render
synchronization does not depend on timer execution.

## Limits and remaining acceptance

- macOS CPU only; Metal/CUDA/OptiX, Windows and Linux are not validated here.
- Generated grid/identifier patterns are limited to 2048 pixels per dimension;
  custom images retain their source. Grid line minimum width avoids disappearing
  lines on unusually small test rasters.
- Brightness is an approximate 300 lm/W default, with a look multiplier and angular
  mask/unit correction. It is not a calibrated illuminance simulation.
- Planning and analysis still treat alpha meshes as solid. This feature addresses
  material-aware rendering, not alpha-aware engineering analysis.
- Custom model geometry can physically shadow the Cycles light at the optical
  origin. This differs intentionally from Beam's model exclusion in engineering.
- A separate live Blender 5.2.2 window exported a 640 × 400 study PNG from
  Rendered shading, retained the planning overlay and restored Rendered shading.
  The actual exported image was visually inspected. Equivalent GPU export on 4.5
  and other platforms remains untested.
- Large production scenes, extreme aspect ratios, animated image sequences and
  linked-library workflows need further field testing. No claim of stable production
  readiness is made.

## Evidence locations

Reproducible tests and benchmark scripts are tracked. Machine-specific render assets,
EXRs, demo blends, logs and benchmark JSON remain in `work/issue-14/` (ignored).
Compact result JSON and representative PNG previews are in this document's adjacent
`cycles-validation/` directory. The onboarding package is unchanged.
