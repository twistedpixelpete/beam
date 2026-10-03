# Beam 0.7.0 — beauty and usability

Maintainer: Twisted Pixel

## Changes

The sidebar now groups controls into collapsible sections. Projector, Projection and Calculated start open; Blend Group, Study Views, Display, Export, Aim / Position and Project Details start closed. Common projector actions and Create Blend stay at the top. Calculated values use compact right-aligned readouts, sensible display precision and a combined image-size row. Internal precision is unchanged.

Projector body badges use white text on neutral translucent backing with a thin Study Colour accent. The active projector gets slightly stronger backing. Width and height use small neutral translucent text without backing plates, offset outside the nominal image edges. A simple placement check prefers edges away from neighbouring projections. Existing dimension annotations did not have separate dimension/extension lines; none have been added. Frustum styling and first-hit termination remain unchanged.

Display → Label Detail offers Off, Minimal and Full. Minimal is the default and shows width/height. Full adds throw-distance and blend labels. Off hides those annotations while retaining enabled PJ badges. Show Labels remains the master gate. Projected calibration-grid identifiers and resolution text remain independently controlled and unchanged.

Presentation View selects Minimal and retains the existing neutral geometry, background and reduced native overlays. Returning to Technical View restores the previous detail preference and viewport state; choose Full explicitly for all annotations. Blend controls now separate desired overlap from actual overlap using the selected unit, with compact member actions and useful tooltips.

Projection maths, targets, occlusion, multi-surface projection, group spacing, UUID logic, CSV structure and JSON schema are unchanged.

## Modified files

- projection_study/ui.py: sidebar hierarchy, layout, actions and calculated readouts.
- projection_study/blend_ui.py: compact group/member/overlap controls.
- projection_study/blend_groups.py: overlap-unit and group-action tooltips only.
- projection_study/projector_data.py: input display precision only.
- projection_study/study_data.py: saved scene Label Detail preference and orientation tooltip.
- projection_study/typography.py: neutral badge emphasis and discreet annotation drawing.
- projection_study/viewport_display.py: detail filtering and measurement placement/style.
- projection_study/presentation.py: reversible Minimal preference in Presentation View.
- projection_study/blender_manifest.toml: version 0.7.0.
- tests/verify_beauty.py: disposable Blender UI/export acceptance checks.
- README.md, projection_study/README.md, TEST_RESULTS.txt, this guide and its packaged copy: release documentation.
- examples/0.7/: sidebar and Off/Minimal/Full/Presentation screenshots.

## Install and inspect

Install beam-0.7.0.zip through Blender Preferences → Get Extensions → Install from Disk, replacing the existing Beam extension, then restart Blender. The extension ID remains projection_study. Source stays in Documents/projection-study; no Git repository was created.

1. Open the 3D View sidebar → Beam. Confirm common controls and calculated values are visible; expand Blend Group, Display, Study Views and Export as needed.
2. Add two projectors aimed at a wall, or create a two-projector blend. Observe the dark PJ badges and small colour accents; select a different active projector to compare emphasis.
3. In Display, select Minimal: only width and height measurements appear outside the nominal image edges. Select Full: throw and available blend annotations return. Select Off: PJ badges remain. Disable Show Labels to hide all these overlays.
4. Select Full, enter Presentation View and confirm it switches to Minimal with a clean background. Return to Technical View and confirm Full is restored.
5. Compare sidebar.png, labels-minimal.png, labels-full.png and presentation.png in the supplied screenshots. labels-off.png demonstrates retained IDs. Screenshots were generated in a disposable scene, not your open working file.

## Validation

Blender 5.2.2 LTS on macOS/Metal: 27 pure Python tests and all 15 Blender integration milestones passed. The new beauty test verifies Off/Minimal/Full annotation counts, retained IDs, unchanged technical JSON values across display-mode changes, unchanged materials, and Presentation/save restoration. Native sidebar and GPU-export screenshots were inspected.

## Known UI limitations

Label placement uses nominal image edges and a simple screen-space neighbouring-bounds check, not full collision or occlusion avoidance. Dense or strongly oblique layouts can still overlap. Small annotations have fixed, bounded screen-space sizes; very distant projections may be smaller than their labels.

Label Detail is scene-wide and saved in the blend file, not per viewport or saved Study View. Image exports use the current scene preference. It is deliberately absent from the frozen JSON schema. Presentation restores the previous detail preference rather than forcing Full on exit. Simultaneous multiwindow/multiscene editing remains unsupported.

Blender remembers section expansion; older saved UI state may differ from initial defaults. Narrow sidebars may need widening. Other Blender versions/platforms are unverified (manifest minimum remains 4.5).
