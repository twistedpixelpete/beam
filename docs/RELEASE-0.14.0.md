# Beam 0.14.0 — Internal Production Beta

Still in testing; this is a prerelease, not a stable release.

## New since 0.13.0

- Optional **Cycles Render** projection mode for rendered viewports and F12 renders. Each projector uses a managed light and shared raster math, with source images, lens shift, aspect ratio, blend weights and generated calibration patterns.
- Native Cycles material transparency: opaque cloth receives projection while transparent cut-outs allow light to reach the backdrop. Fractional and layered transparency are covered by rendered tests.
- Independent projector-body visibility, a default for newly created projector bodies, and custom model support. These controls were merged after the 0.13 release and are included here.
- Managed render-rig duplication, visibility, scene isolation, save/reopen, undo/redo and cleanup. Planning calculations and technical exports remain unchanged.

## Install and use

Download **beam-0.14.0.zip**, leave it zipped, then use **Edit > Preferences > Get Extensions > Install from Disk**. Replace the existing Beam extension, keep one copy enabled, and restart Blender after upgrading.

Run **Open Beam Workspace** from Menu Search. In the Beam inspector, expand **Projection Mode**, choose **Cycles Render**, choose **Cycles** in Render Properties, and use **Rendered** viewport shading or F12. Planning remains the default.

**SHA256SUMS.txt** accompanies the installer. GitHub's generated source archives are developer source, not the installable extension. The retained 0.13 onboarding bundle contains an older installer and has not been updated for Cycles; use this release's installer separately.

## Validation

Release checks repeated on 2 November 2026 on Blender 5.2.2 LTS/macOS Apple silicon: all 71 Python tests, rendered Cycles alignment/transparency tests, lifecycle and save/reopen, undo/redo, and projector-body regression passed. The installable ZIP is checked in a fresh Blender process before publication.

The feature's recorded validation also covers Blender 4.5.0/macOS CPU renders and existing planning/export regressions. The measured maximum edge error was 0.7875 source pixels in the documented full-HD shifted flat-screen fixture, not a guarantee for arbitrary scenes. See [validation details](design/CYCLES_PROJECTION_VALIDATION.md).

## Limits

- Cycles feature validation is macOS CPU; Metal/CUDA/OptiX rendering and Windows/Linux are not validated for this mode.
- Brightness uses an approximate efficacy conversion and intensity multiplier, not calibrated illuminance.
- Planning/analysis still treat receiving meshes as solid. Material transparency applies to Cycles rendering.
- Custom body geometry can shadow the projector light, including at its optical origin.
- Generated calibration patterns are capped at 2048 pixels per dimension. Large production scenes, extreme optics and linked/animated workflows need field testing.

Use copies of studies and independently verify production measurements and handoffs.
