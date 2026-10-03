# Beam 0.6.0 — Blend Group lifecycle

Maintainer: **Twisted Pixel**. Existing projection engine and JSON schema `projection-study / 1.0` retained.

## What changed

The Blend Group panel now has a clickable member list, **Add Selected Projector**, **Add New Projector**, **Remove Selected Projector**, **Duplicate Blend Group**, **Reflow Group (Preserve Local Offsets)** and **Reset Active Member to Group Position**. The list shows the anchor, member number, row and column.

Adding an existing selected projector preserves its world pose, UUID, colour and settings. Membership edits capture spatial order in the controller frame: horizontal +X left-to-right; vertical -Y top-to-bottom; arrays -Y rows then +X columns. That stored order remains stable during movement/rotation and is exported as zero-based member index/row/column. The UI displays one-based numbers. Reflow is explicit; changing overlap also updates layout spacing while retaining manual member offsets.

Add New uses the native Beam projector factory, inherits the anchor's technical settings and places only the new member in the next layout cell. Existing members do not move. Remove disconnects the relationship and keeps the projector at its world pose. Removing the anchor promotes the next valid member. Removing the last member retires the empty group/controller; projectors survive. Outliner deletion of a member also cleans its stale relationship.

Reset recalculates only the chosen member's slot and clears its local position/rotation basis. It does not reset other members, UUID, settings, colour or notes. The group controller continues to provide overall translation/rotation; layout slots provide spacing; projector basis transforms provide individual fine corrections.

## Duplication implementation

Use **Duplicate Blend Group**, or select the controller and use native Shift-D / Alt-D / copy-paste. Selecting the entire hierarchy also works. Copying only a projector remains an independent-projector copy, not an implicit whole-group copy.

Each duplicate receives the next BG number, a new group UUID, its own controller and entirely new projector/slot objects. Projectors use the same creation factory as + Projector: new sequential PJ numbers, UUIDs and palette colours, independent meshes, materials, optics and custom-image datablocks. Resolution, throw ratio, shifts, brightness, lumens, stack, output, notes and display settings are preserved. Palette colours cycle after the palette is exhausted; identity never relies on colour.

The controller stores a versioned copy recipe containing group configuration, each layout slot's group-relative matrix, projector basis and parent-inverse matrices, anchor membership and technical settings. Translations in the recipe use metres. Image datablock dependencies are attached to the controller, so Blender's clipboard can carry them. Reconstructing this hierarchy preserves local nudges/rotations instead of treating absolute world positions as the layout. Group notes, overlap/input mode, rows/columns and preview settings are retained.

The dedicated duplicate starts 1 m along the controller's local +X axis and selects the new controller. Native copies retain a displacement supplied by Blender; coincident copies receive the same 1 m offset. Internal spacing is unchanged. Reconstruction happens on Beam's update tick after an interactive duplicate transform finishes, so it never replaces objects owned by a live transform operation. Blender exposes running modal operators via [Window.modal_operators](https://docs.blender.org/api/4.5/bpy.types.Window.html#bpy.types.Window.modal_operators).

Native copies of selected projectors may retain source-slot parents when hidden slots were not included in Blender's selection. The importer recognises copied member UUIDs, excludes registered source members and removes only the temporary Beam-owned copies before building the independent group. Non-Beam child objects are preserved. Linked duplicates are made independent. Identity repair preserves membership in explicitly stored groups when a saved scene is appended/reloaded.

## Local-orientation implementation

Selecting a Beam projector or group controller defaults Blender's active transform orientation to Local. The previous scene orientation is saved and restored on selection of an unrelated object, scene switch, add-on disable or file-save preparation. Save-post restores the live Beam selection behaviour. Users can temporarily choose another orientation while keeping the same selection; selecting another Beam object defaults back to Local.

Projector-local X is pitch/tilt, local Y is yaw/pan and local Z is roll (the optical forward direction is -Z). Native move/rotate tools use those local axes, including when the projector is parented to a group. This applies to + Projector, Add New, group copies, native duplicate and paste paths.

This is selection-scoped use of Blender's existing scene orientation slot, not a permanent application preference or replacement transform tool. Blender shares the orientation slot between windows showing the same scene; this release does not introduce independent per-window orientations.

## Frustum behaviour

The 0.5.2 first-hit helper remains in place: each corner ray ends at its first visible evaluated-surface intersection. Misses end at the nominal centre-hit depth, or at configured preview depth when the centre also misses. Helper endpoints remain separate from projection extent, receivers, GPU occlusion, centre targets and engineering calculations. No projection engine redesign was made.

## Files changed

| File | Purpose |
|---|---|
| `projection_study/group_lifecycle.py` (new) | Membership, ordering, independent copies, controller recipes, native-copy reconciliation and cleanup |
| `projection_study/local_orientation.py` (new) | Temporary Local orientation and restoration lifecycle |
| `projection_study/blend_groups.py` | Anchor-relative layout, removal/promotion, reset and new group actions |
| `projection_study/blend_ui.py` | Member list and lifecycle controls |
| `projection_study/projector_object.py` | Local-orientation activation and independent custom-image data for factory copies |
| `projection_study/runtime.py` | Native group reconciliation, deferred modal-copy handling, recipe refresh and safe identity repair |
| `projection_study/study_data.py` | Keep panel group selection in step with selected members/controllers |
| `projection_study/__init__.py` | Register lifecycle UI and orientation hooks |
| `projection_study/blender_manifest.toml` | Release 0.6.0; maintainer unchanged |
| `tests/blender_group_lifecycle.py` (new) | Membership/copy/local-axis/persistence/operator acceptance |
| `tests/verify_group_ui.py` (new) | Live UI, native undo/redo and interactive duplicate safety |
| `tests/create_lifecycle_example.py` (new) | Reproducible BG01/BG02 fixture |
| `tests/blender_json_contract.py` | Test exports now go to work/ instead of overwriting historical release fixtures |
| README files, TEST_RESULTS.txt, this guide, `examples/0.6/` | Release documentation and sample study |

Frustum helper and projection-renderer files were not changed in this pass.

## Automated verification

Tested with Blender 5.2.2 LTS, macOS/Metal.

- 27 standalone Python tests pass.
- All 15 existing Blender integration milestones pass, including GPU multi-surface/occlusion tests, native projector copy/paste, groups and view exports.
- New lifecycle test passes existing-member preservation, adding new, removal, anchor promotion, empty-group cleanup, independent meshes/materials/images, group/controller independence, manual offsets, linked/hierarchy duplicates, clipboard into another scene, actual local X movement and X/Y/Z rotations, reset, ungroup, non-default scene units and save/library-reload duplication.
- Live UI test passes native duplicate undo/redo and a real modal hierarchy duplicate followed by Escape. It confirms the expected group/projector counts after deferred reconstruction. The group draw function was visually inspected in a disposable test panel.
- Frustum tests pass first-hit/near-occluder/partial-hit/moving/hidden geometry and verify technical records match when helper clipping is disabled/enabled.
- Example JSON passes the existing portable v1 schema, UUID uniqueness and anchor/member/adjacency/row/error reference validation.

Useful commands from the source folder:

```
python3 -m unittest discover -s tests -p 'test_*.py'
/Applications/Blender.app/Contents/MacOS/Blender --background --factory-startup --python-exit-code 1 --python tests/blender_group_lifecycle.py
/Applications/Blender.app/Contents/MacOS/Blender --background --factory-startup --python-exit-code 1 --python tests/blender_frustum_helpers.py
/Applications/Blender.app/Contents/MacOS/Blender --factory-startup --enable-event-simulate --python tests/verify_group_ui.py
```

Run tests only in disposable Blender sessions. The full existing integration runner is `tests/run_blender_tests.py` and needs a 3D View. JSON Schema validation uses the development-only `jsonschema` package; the add-on has no new external dependency.

## Manual acceptance procedure

1. Create PJ01, then a three-member horizontal BG01. Give PJ03 a 150 mm local offset and set custom overlap/notes.
2. Create PJ04 separately and position/rotate it elsewhere. Select BG01 in the group list, select PJ04 and use Add Selected Projector. Confirm its pose, colour and UUID are unchanged. Use Reflow only when alignment is desired.
3. Remove PJ02, then anchor PJ01. Both remain in the scene; a remaining member becomes anchor. Add New Projector and confirm it joins the layout without moving peers.
4. In a fresh three-member study, duplicate BG01. Confirm BG02 has PJ04–PJ06, new UUIDs/colours, copied technical settings and the matching 150 mm local offset. Move BG02 and edit PJ05; BG01/PJ02 must remain unchanged. Repeat with controller Shift-D/Alt-D and copy/paste, including an entire selected hierarchy.
5. Reset an offset/rotated member. Only that member returns to its calculated group position. Ungroup BG02; its projectors remain intact.
6. Rotate a free projector and a grouped projector away from world alignment. Use Local X movement and local X/Y/Z rotations. Select an ordinary object and confirm the previous orientation returns.
7. Aim at a wall, then move an edge off it. Hit helper rays stop at the wall; missed rays use finite fallback. Projected content still reaches unobstructed geometry.
8. Export JSON and validate group/member/anchor UUID relationships. The included example has BG01/PJ01–PJ03 and BG02/PJ04–PJ06.

## Migration and known limitations

Install `beam-0.6.0.zip` as the existing extension and restart Blender; do not enable a second copy. Technical extension ID `projection_study`, `Object.ps`, `Scene.ps_study` and JSON schema 1.0 remain unchanged. Existing groups keep their UUIDs, settings and poses; copy recipes are populated automatically when Beam refreshes them. No user-data migration or renaming is required. Old files should be opened with Beam enabled before copying their controllers so the recipe is present.

Membership edits can renumber logical member indices as spatial order is captured. Consumers must use UUIDs for persistent identity. Native copies finalise after the drag ends, so complete copied projection helpers may appear after confirmation rather than during the drag.

Custom-image datablocks are independent; their external image paths may still refer to the same disk asset. Saving over that shared external file is not an asset-management feature of this release. Arbitrary third-party constraints, animation, custom projector body edits and external parenting rigs are not cloned by the Beam group recipe; the supported model is Beam controller → layout slot → independently editable projector. This is a static study workflow, not an animation-rig duplicator.

Other Blender versions/platforms have not been runtime-tested here. Disguise transform convention remains explicitly unvalidated. No manufacturer library, new optical maths, advanced blending or reporting integration was added.
