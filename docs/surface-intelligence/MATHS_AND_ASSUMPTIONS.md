# Surface Intelligence · Beam 0.13.0 internal beta

Maintainer: Twisted Pixel. This engineering milestone starts from merged PR #7 (`b4f8a7a172143f05d7f7998b58574c10e3611755`). The frozen 0.12.0 onboarding branch and screenshots remain unchanged. No documentation-generation commits are included here.

## Shared engine

One explicit **Analyse Surface** operation creates equal-area deterministic triangle samples from evaluated geometry, tests each source's raster coverage, and uses the existing opaque, two-sided, first-hit CPU visibility test. All five modes share these samples and ray tests. No heavy analysis runs every frame. An Observer is optional for the first four modes and required for Acuity. When present, its viewing calculation is included in the same solve.

Density and Stretch retain their existing selection rule: pick the visible projector with the highest conservative worst-direction density; report that projector's principal pixel anisotropy. New metric calculation does not change target selection or projection rendering.

## Estimated Illuminance

Let Φ = nominal lumens × stack quantity × brightness percentage / 100. Assume luminous flux is uniformly allocated across Rx × Ry raster pixels. The existing perspective ray/tangent-plane Jacobian provides two surface displacement vectors per raster pixel, a and b. Pixel area is |a × b|, equal to the product of the two singular values. Therefore:

`E = Φ / (Rx × Ry × |a × b|)` lux.

For a perpendicular plane at axial depth z, throw ratio t, and aspect Rx/Ry:

`area = (z/t)² × Ry/Rx`, so `E = Φ / area` everywhere on that plane.

For unit surface normal n and lens-to-sample vector d in projector coordinates, z = −d.z:

`E = Φ × t² × (Rx/Ry) × |n · d| / z³`.

This is an independent equivalent expression used by the tilted-plane integration test. At the optical axis a 60° incidence gives half the perpendicular illuminance. Doubling image area halves illuminance; doubling flux or stack doubles it. Off-axis weighting follows the uniform-raster-flux model, not a uniform-candela source. Lens shift is incorporated into raster containment and the existing Jacobian.

Distance falloff and incidence are already represented by projected pixel area. There is **no additional inverse-square or cosine multiplier**. Contributions add only from projectors that see the sample. An occluded source contributes zero. No edge-blend attenuation is assumed.

Min/average/max include the whole sampled receiver, including unlit zeros. Average is surface-area weighted. Uniformity is explicitly **minimum / average**, with minimum / maximum also exported. Both are null for an entirely dark receiver, rather than an invented percentage.

Auto Scale uses current sample min/max; Fixed Range uses 0 to a chosen lux maximum. An optional Target Illuminance is a labelled display reference only. Changing scale or target rebuilds colour batches, not physics or ray casts.

This is a planning estimate. It does not model measured projector brightness distribution, lens transmission differences, ageing, calibration loss, colour-mode output loss, edge brightness falloff, screen gain, surface reflectance, ambient illumination, black level or colourimetry. Two-sided surfaces receive estimated incident flux on either side. Luminance in cd/m² is not implemented.

## Projection Distance

Each sample uses Euclidean lens-to-surface distance `|sample − lens|`, in metres. Among eligible sources, the **nearest visible projector** controls the displayed value. Ties break consistently by UUID. Samples with no visible projector have no distance result and are excluded from distance statistics; they are grey in the overlay. Average is weighted by sampled visible area. Variation is max − min.

A flat perpendicular wall has constant axial throw, but its Euclidean distance increases away from the centre. A constant-distance test surface is a sphere centred on the lens, not a plane. The pure tests include 3–4–5 and 6–8–10 geometry; integration checks every flat/tilted sample against direct Euclidean distance. Existing curved/stepped evaluated-geometry tests also pass.

The controlling source UUID is retained per sample in Study Package output. Display follows m/mm preference; structured distances remain explicit metres. Distance is useful for depth variation planning, but is **not lens-specific focus or depth-of-field compliance**.

## Observer Acuity

An Observer is a native Blender Empty, named OBS01, OBS02, etc. Its location is a base position. Eye position is base + world-Z eye height, with eye height stored in metres. Rotation/scale do not alter the eye offset. The default height is 1.6 m and threshold 1 arcminute; both are editable. One active Observer is analysed; additional planning positions can coexist. Native duplicates receive independent UUIDs.

For each projected pixel Jacobian, rotate tangent vectors a and b into world space. Let q be the unit sample-to-eye direction. Project both tangents onto the observer's image plane: `a' = a − q(q·a)` and similarly for b. Let p be the largest singular value of `[a', b']`, and D the eye-to-sample distance:

`angular pixel size = 2 atan(p / (2D))` radians; display = radians × 180/π × 60 arcmin.

This differential footprint model includes observer foreshortening. At overlap, choose the **largest apparent angular pixel pitch** among visible sources, a conservative coarsest-pixel-structure rule. It intentionally differs from Density's highest-detail choice. It does not simulate the superposition or phase of two raster grids.

Viewer visibility is tested from the eye using the same first opaque hit. Samples blocked from the observer, unlit samples, and zero eye distance are excluded from Acuity statistics. The percentage denominator is the area that is both lit and observer-visible, explicitly exported as `acuity_evaluated_area_m2`. Below-threshold and at-or-above-threshold percentages partition that area. No observable area gives null statistics. The palette spans 0.5× to 1.5× the threshold and saturates outside; near-threshold tones are a continuous diagnostic, not a pass/fail judgment.

One arcminute is nominal adjustable guidance, not universal eyesight. Contrast, content, eyesight, ambient conditions, and actual ability to resolve an image are not predicted.

## Cache and interchange

Geometry/source changes invalidate all modes. Flux/stack/brightness changes invalidate Illuminance; Observer position/height/threshold/selection invalidate Acuity. Appearance controls do not invalidate physical results. Display scale/target/unit changes update cached display data. Source selection changes require a fresh solve. File load clears transient analysis; Observer data and view mode choices persist.

Individual images refuse stale selected metrics. Unrelated stale metric fields are omitted from their sidecar; whole Study Packages require all cached metrics to be current. Existing Density/Stretch fields and strings remain, and schemas accept the new overlay enum values additively. The package includes Observer records, metric definitions, assumptions, sample positions in SI, controlling source IDs, timestamps, source/receiver UUIDs and hash-linked image metadata.
