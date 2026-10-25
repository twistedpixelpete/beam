# Beam Review v0.1 acceptance

Validated locally on macOS 26.7 / Chrome, exported with Blender 5.2.2 LTS. Internal prototype; no release/tag or hosting.

## First-slice acceptance

1. The upgraded training project exported successfully with fresh Authoring analysis.
2. The browser loaded the manifest, checksum-verified Beam JSON and GLB.
3. Venue wall, floor, stage, curved receiver, blocker and UV-textured screen rendered.
4. PJ01–PJ03 appeared as independent interactive Beam objects with labels, axis and frustums.
5. SCR001 appeared in the tree and inspector; 15 × 3.6 m / 4.167:1 verified.
6. BG01 showed all three members and the actual 240 px overlaps / zero gaps.
7. PJ02 visibility was toggled off and back on; its body, frustum and label followed.
8. Projectors were selected both from the tree and directly by clicking the 3D body.
9. PJ01 displayed Panasonic PT-RZ990 / ET-DLE105, 1920 × 1200, ratio 1, 6.4 m throw, 6.4 × 4 m image, 300 px/m, shift and lumens. Generic PJ02 was also checked.
10. All nine saved cameras were selected through the actual dropdown; see `study-view-ui.json`. Overview, Front and Acuity compositions were visually checked; the frame action also produced the expected changed composition.
11. Orbit drag, wheel zoom, keyboard pan, frame and reset were exercised. Standard Shift/right-drag pan is supplied by OrbitControls; the direct pan test used its keyboard path.
12. Viewer runs from static files plus Three.js, with no Blender runtime or Python on the viewer side.

No browser warning/error logs were reported at completion. Screenshot: `beam-review.png`.

## Engineering checks

- Five Node tests: package hashes/identity references; venue/screen UUID, UVs and embedded image; coordinate conversion; all nine camera orientation/projection contracts; invalid member/schema rejection. See `unit-tests.txt`.
- Blender fixture: centimetre authoring scene exports metre GLB and JSON; shifted orthographic matrix; operator path; stable project identity with distinct revision UUIDs; existing revision refusal; context/data-count restoration; injected failure cleanup. See `blender-tests.txt`.
- Training export: context restoration and existing-folder refusal (`training-export.txt`).
- HTTP checks: viewer GET 200; write request 405; traversal attempt 404. Server bound to loopback.

Scope stops at this vertical slice. No measurement tool, live heatmap rendering, hosting, password protection or authoring controls are claimed.
