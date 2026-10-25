# Beam Review v0.1 — local prototype

Twisted Pixel. A read-only browser review of a Beam study. This is an internal prototype alongside Beam 0.13, not a public/stable release.

## Open the supplied example

From this directory, with Node.js 18+ and npm installed:

```sh
npm ci
npm start
```

Open **http://127.0.0.1:8787**. Blender is not required to view the package. Three.js is pinned and served locally; after dependency installation the viewer does not use a CDN or cloud service.

The example contains the validated onboarding scene: PJ01–PJ03, SCR001, BG01, venue geometry, the embedded UV chart and nine saved Study Views. The original training starting state has 12.5% overlap; the documentation's later exercised export uses 15%. This is intentional.

Select items in the left tree or click a projector in the scene. Inspect technical information on the right. Use the checkboxes to hide/show individual projector helpers. Frame Selection includes the selected object's extent; Reset View returns to the first saved camera. Drag to orbit, Shift-drag or right-drag to pan, and scroll to zoom. Focus the 3D scene and use arrow keys for keyboard pan.

Saved Study Views restore the exported perspective/orthographic camera, including projection matrix and aspect ratio. Letterboxing preserves the saved composition. The geometry is a review representation; the training UV chart is the receiver's material, not a browser simulation of projected light.

## Export another study

1. Install `install/beam-0.13.0-review-prototype.zip` in a disposable/test Blender configuration. Restart after replacing another 0.13 installation. This archive includes the prototype export command; the separate onboarding ZIP intentionally remains the validated documentation build.
2. Open a working copy of your Beam study. If analysis is wanted, run Analyse Surface with the required receiver, source scope and Observer. Stale analysis is rejected; absent analysis is exported with a warning.
3. In Beam's Export module choose **Export for Beam Review · Prototype** (Menu Search: **Export for Beam Review**).
4. Enter a **new folder path** for this revision. Existing folders are refused, including empty folders. Save the Blender file after the first export to retain its new Review project UUID across sessions.
5. Start the viewer against that package:

```sh
node server.mjs --package /absolute/path/to/Beam-Review-R01 --port 8787
```

Each export receives a new revision UUID. Existing Beam projector, screen, group, receiver, Observer and Study View UUIDs are reused. Exporting never writes edits back from the viewer.

## Package

- `manifest.json`: version, project/revision IDs, coordinates and payload SHA-256 inventory.
- `beam.json`: the existing `beam-study` 1.0 contract plus a `review` presentation extension. Includes projectors, screens, groups, optics, cameras, Observers, warnings and current analysis.
- `scene.glb`: visible evaluated venue/receiver geometry with UVs, supported materials and embedded textures. Beam projector meshes and authoring helpers are excluded.
- `assets/`: reserved; current textures are embedded in the GLB.
- `thumbnails/`: reserved; thumbnail generation is outside v0.1.

## Prototype limits

The viewer consumes exported statistics; it does not rerun engineering analysis or reproduce Blender heatmap shaders. Saved analysis views change the camera; the inspector shows the one exported analysis snapshot. Arbitrary procedural Blender materials may not translate to glTF. Perspective and orthographic Study Views are supported; panoramic cameras are rejected. Analysis and nominal projector calculations remain subject to Beam's planning assumptions.

Measurement, publishing, passwords, accounts, comments, editing and live Blender connections are not implemented. The server binds only to this computer. Do not use it as an internet hosting service.

See [ARCHITECTURE.md](ARCHITECTURE.md) and [validation/ACCEPTANCE.md](validation/ACCEPTANCE.md). Run `npm test` for package/coordinate tests. The Blender fixture is `tests/blender_review_package.py` at the repository root.
