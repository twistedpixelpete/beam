# Cycles projection: engineering study for issue #14

Date: 2026-10-28. Baseline: `03eeffaeea7274df370a5e473c297b846e75e618` (main after PR #15).
Implementation branch: `feature/cycles-projection`.
Status: design and capability study; no production rendering feature implemented.

## Recommendation

Add an opt-in scene-level **Cycles Render** mode alongside default **Planning**.
Use one managed zero-radius spot light per projector and a shared shader group for
perspective mapping, raster clipping and edge weights. Keep existing geometry,
engineering analysis, targets and exports unchanged. Use native Cycles material
transparency; do not attempt to interpret arbitrary receiver materials ourselves.

This is the most practical architecture based on the current code and Blender's
light shader support. It is not yet a measured performance winner. Rendering cost
will depend on scene complexity, light count, transparency bounces, samples and GPU.

## Options considered

| Approach | Transparency | Costs / limitations | Decision |
| --- | --- | --- | --- |
| Cycles textured spot lights | Native material shading and transparent shadows | Requires rendered viewport/F12; noise and render cost; new light lifecycle | Recommended |
| Alpha-tested GPU planning pass | Simple cut-out image materials only unless a shader interpreter is built | UV/material uploads, per-material batches, invalidation; must change both depth and colour passes; threshold cannot represent transmission | Separate future feature, not the first fix |
| Inject projection nodes into receiver materials | Possible with substantial material changes | Modifies user shader trees, difficult rollback and multi-projector scaling, does not itself solve first-hit lighting | Reject |
| CPU alpha-aware raycasts | Limited material subset | Texture sampling and multiple-hit traversal; does not supply final-render projection; expensive per-sample analysis | Reject for this issue |
| OSL projector shader | Expressive perspective model | Adds device/backend portability and deployment concerns | Avoid for first implementation |

Planning remains geometry-based even when a render looks transparent. Explicitly
label this in the UI and documentation: rendered appearance and engineering coverage
are different outputs. Do not describe the new mode as calibrated photometry.

## Mapping and alignment

Reuse Beam's optical frame: lens-centred origin, local -Z forward, +Y up; discard
non-rigid object scale just as the existing runtime does. For a forward local ray
`d`, aspect `a = resolution_y / resolution_x`, ratio `t`, shifts as fractions:

```
u = d.x / (-d.z) * t + 0.5 - shift_h / 100
v = d.y / (-d.z) * t / a + 0.5 - shift_v / 100
```

Reject rays behind the projector and outside the unit rectangle. The depth divide
requires a safe denominator near the horizon. Determine Cycles Incoming's direction
sign with an asymmetric corner-marked image; do not guess from the node's label.
Use vector direction transforms, without translation. Test rotated and parented
projectors, scene units and shifts with both signs.

Compute the smallest cone covering all four shifted raster corner directions:
`2 * atan(max(sqrt(x*x+y*y)/(-z)))`, with a small numerical margin. A fixed nearly
180-degree cone is a useful initial correctness baseline but may waste light
sampling. Very wide/shifted rasters approach the spot limit; report unsupported
configurations instead of silently clipping. Keep `spot_blend=0` and radius zero.

The probe in `tools/studies/cycles_projection_probe.py` compares the inverse formula
with Beam's GPU projection matrix for 10,000 deterministic cases. Blender 5.2.2 LTS
returned a maximum difference of **0.001982 projector pixels** at nominal 1920-wide
rasters. This establishes algebraic consistency, not the required rendered one-pixel
alignment: texture filtering, Cycles vectors and raster-edge sampling remain untested.

## Content and blend integration

Use existing images directly for Image, UV Grid and Color Grid. Respect image colour
space; do not apply viewport `displayRGB()` conversion to scene-linear light output.
Do not copy the viewport's cosmetic alpha strengths (0.45, 0.85, combined-preview
0.35) into light energy. Define transparent image pixels as zero emitted energy.

Implement Solid and Checker procedurally. For Grid and Identifier, prefer reusable
CPU-generated/persisted pattern images; current GPU typography textures are not a
portable source for background/F12 rendering. Cache by content, colour, identifier,
resolution and grid settings, with explicit ownership and bounded memory. Avoid
rebaking user images or one full-resolution image per projector on every update.

Use `blend_groups.preview()` for local edge fractions and combined-canvas mapping.
Apply clipping and edge weights in local projector UV, sample combined content in
mapped canvas UV. Use the actual group's anchor, not simply the first member:
current viewport code selects the first member for combined content, whereas the
layout logic resolves `anchor_uuid`. Cover reordered groups in tests. Do not alter
that existing path as an incidental part of this feature.

All seven current modes, including Identifier, need a documented outcome. The issue
lists six sources but omits Identifier; silently dropping it would be a regression.

## Efficient implementation and lifecycle

- One shared, versioned math group; per-light parameters and image bindings. Reuse
  image datablocks. Do not construct a separate large group for each projector.
- A dedicated render-light owner tag plus projector UUID. Do not identify generated
  assets by name alone or delete unrelated lights. Existing `ps_helper` can be used
  for exclusion, but cleanup must be coordinated with runtime orphan handling.
- Reconcile creation/deletion only on enable, load, undo/redo and relevant scene
  changes. Transform updates only move lights; lens updates only change parameters.
  Image/pattern regeneration runs only for content changes. No work in draw callbacks.
- Stage synchronization on the main thread and debounce bursts. Include a synchronous
  pre-render reconciliation so background/F12 renders do not depend on timer ticks.
- Handle native duplicate, Beam duplicate, Blend Group duplication, shared scenes,
  linking/appending, hidden projectors and removed projectors. Never mutate a linked
  library asset. Copy ownership correctly and avoid cross-scene mode contamination.
- On switch back, remove owned light objects, unused owned light datablocks and
  unused generated groups/images only. Repeated toggles must not leak assets.
- A saved file must retain sufficient generated nodes/images for normal rendering;
  reload with the add-on enabled reconciles them. Decide and document disable-addon
  cleanup explicitly, including effects on subsequent saves.

Suppress Beam's projected raster overlay only in Cycles rendered viewports while
render-light mode is effective. Keep planning overlays in Solid/Material Preview,
where Cycles lighting is unavailable, with a clear mode indication. Study-view PNG
exports currently capture viewport output: explicitly preserve planning export
behaviour rather than allowing it to change with whatever viewport shading is active.
Never silently change the user's render engine. Show a clear Cycles requirement.

## Brightness and physical limits

Lumens are photometric; Blender light energy is radiometric. There is no universal
lumens-to-watts conversion without a spectral/luminous-efficacy assumption. Expose
a clearly documented approximate efficacy and separate look-development multiplier;
include brightness and stack count once. Establish whether Blender's normalized
spot energy is defined over the cone before applying raster masking: masking can
reduce total flux, and changing cone angle can otherwise change apparent brightness.
Measure with white flat-screen probes; do not promise a nominal lux match yet.

Distance in Blender coordinates changes with unit scale. Validate energy scaling
for 1 m/unit and 0.01 m/unit rather than assuming the unit display setting changes
Cycles attenuation. Exposure, colour management, bounce lighting and materials
also affect appearance; engineering lux remains the existing independent estimate.

Custom projector models introduced by #13 are ignored by Beam geometry sampling,
but remain real Cycles geometry. They may shadow the lens. Do not globally disable
their shadows as a hidden side effect. Test lens-origin placement and document this
boundary; consider a later explicit render-shadow option only if needed.

## Compatibility and evidence

Local probe: Blender **5.2.2 LTS**, CPU-side node construction, no rendered benchmarks.
All required Geometry, Vector Transform, Separate XYZ, Math, Image, Emission, Light
Output and Group nodes instantiated. Spot maximum angle is approximately pi, and
`normalize` exists. `use_nodes` raises a Blender 6.0 removal deprecation: isolate
version-specific setup and do not assume that property always exists.

Beam's declared minimum is **4.5.0**. Run the same checks and rendered suite on 4.5
before claiming compatibility. This study does not establish that version's runtime
behaviour. No external implementation code was copied into Beam.

Reference inspection: Ocupe/Projectors uses a Cycles spot node graph, Incoming for
Blender 4+, perspective division and almost-pi cone. The repository advertises GPL-3.0,
compatible in broad licensing terms with Beam's GPL-3.0-or-later; independently
implement the small mapping formula and retain attribution if any code is later
adapted. Reading that code is not evidence of Beam correctness or efficiency.

## Implementation sequence and acceptance gates

1. Isolated proof: one projector, marked image, alpha cloth and solid backdrop.
   Verify orientation, shifts and hard raster edge before integrating lifecycle.
2. Add mode, managed-light lifecycle and change-based synchronization. Confirm
   switch-back cleanup, reopen, undo/redo, duplicates and background rendering.
3. Add all outputs, combined canvas and edge feathering. Preserve engineering
   snapshots and study-view export behaviour.
4. Measure 1, 4 and 16 lights with identical scene, resolution, samples, device and
   seed; separate initial compilation, warm render, parameter-update and pattern
   rebuild time. Compare tight cones to the nearly-pi baseline. Record memory and
   node/image counts; use repeated trials, not one noisy timing.
5. Test opaque cloth, binary alpha holes, fractional alpha and multiple transparent
   layers; document transparent-bounce limits. Compare flat-screen corner locations
   at sufficient render resolution to resolve one projector pixel. Test extreme
   lens shifts and both supported Blender versions.
6. Only after those pass: expose the finished feature for operator review and PR.

No timing claims or rendered transparency results are asserted by this study.

## Sources

- https://docs.blender.org/manual/en/latest/render/shader_nodes/output/light.html
- https://docs.blender.org/manual/en/latest/render/cycles/light_settings.html
- https://github.com/ocupe/Projectors (README and GPL license)
- https://github.com/ocupe/Projectors/blob/main/projector.py
- Beam: projection_math.py, projection_renderer.py, blend_groups.py, runtime.py,
  scene_geometry.py, viewport_display.py and blender_manifest.toml at the baseline.

The official manual's light-shader descriptions were available through search;
direct page fetches failed during this study. Runtime API claims above come from
the local probe, not an assumed version of the manual.
