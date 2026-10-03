# Beam 0.8 — Screen Builder

Maintained by Twisted Pixel. Tested in Blender 5.2.2 LTS on macOS/Metal.

## Start a screen

Open **3D View → sidebar → Beam → Screen Builder → Create Screen**. Choose a type and category, enter dimensions, then Create Screen. Create starts collapsed so existing projector controls remain accessible. Selecting a screen reveals its Edit controls. Parameters change only when you press **Update Screen**; this protects manual work from accidental regeneration. Export refuses pending parameter changes or a changed scene unit scale.

Inputs marked **(m)** are physical metres regardless of Blender's display unit. For a 500 mm cabinet, enter **0.5**. Mesh coordinates are converted using the scene's metres-per-unit. Local X runs horizontally, Z upwards, and the front of an ordinary generated wall faces −Y. This faces Beam's default projector, which points +Y. Translation/rotation work normally; Beam selections use the existing reversible Local orientation behaviour.

Bottom Centre is the default origin; Centre is optional. Open arcs use the midpoint of their endpoint chord at floor level; Closed uses the cylinder's axis. Curve and Surface origins use source-local bounds. Screen names are editable; permanent UUIDs and file-wide `SCRnnn` identifiers are independent of object names. Normal/linked duplicates and clipboard copies receive independent meshes and identities. The scene counter prevents reuse after deletion. External source curves/surfaces remain deliberate shared references; duplicate a source separately if you want independently editable source geometry.

## Types and UVs

| Type | Inputs and behaviour | UV convention |
| --- | --- | --- |
| Flat | Width, height, optional aspect preset/custom ratio and subdivisions | U left to right, V bottom to top |
| Arc | Choose arc length/radius, length/angle, radius/angle, chord/radius or chord/angle | U follows true circular arc distance, not chord projection |
| Curve | Select one Bezier, Poly or NURBS spline, Use Selected Source, set height | U accumulates evaluated 3D path distance; V is extrusion height |
| Closed | Radius, height and angle up to 360°; seam rotation | Continuous U; the 360° geometric seam is welded, with separate loop UVs at 0 and 1 |
| Surface | Copy an evaluated mesh or extract selected Edit Mode faces | Existing UV, planar Projected UV, or restricted Surface Distance mapping |

Arc calculations use `L = R × radians(angle)` and `chord = 2R × sin(angle/2)`. Chord/radius selects the minor arc (≤180°). Concave bends toward the intended viewer; Convex bends away. Full Closed normals point inward by default. **Flip** reverses winding and direction without duplicate faces. A circular display mesh is tessellated: the analytic arc length is exact; the mesh approximates it at the chosen segment count/target length. For R=10 m and 90°, analytic length is 15.707963 m and chord is 14.142136 m.

Curve tessellation follows the source's evaluation resolution, including its modifiers where they yield one unbranched path. Bevel/extrusion are disabled on a temporary copy for path evaluation. Raise source resolution for tighter curves, then Update Screen. Multiple/disconnected splines or branching output are rejected. Editing source geometry does not automatically rebuild the screen: press Update. Closed curve seams start near the first source control point; for explicit seam rotation use Closed or edit the source.

Surface creation preserves the source. Selected Faces Only uses the Edit Mode selection without modifying it; whole-object extraction includes evaluated modifiers. Choose the appropriate local X/Z, X/Y or Y/Z plane for planar mapping. Surface dimensions labelled **Bounds** are oriented bounding extents, not geodesic lengths. Hide the original source yourself when coincident surfaces are undesirable.

**Surface Distance** supports one rectangular quad grid with no holes, branches or cyclic seam. It accumulates distances along each row/column and normalises them. This is not an exact isometric unwrap of arbitrary double-curved geometry. Unsupported topology is rejected; varying density is reported by diagnostics. Use authored Existing UVs for sculptures, scanned meshes, complex facades or intentional seams. Manual UV editing remains available through Blender.

## Conform, convert and bake

Select a screen, expand Mapping / Surface, choose a mesh Conform Target, and use **Conform to Surface**. This adds a reversible nearest-surface Shrinkwrap. Start with a suitably subdivided display close to the desired part of the target. Original source geometry stays intact. UVs are retained; run Validate after conforming to check stretch and collapsed faces. This is nearest-point fitting, not a directional ray projector or a promise that arbitrary scans can be flattened without distortion.

**Make Surface** retains evaluated geometry as a managed, editable Surface snapshot and disconnects its procedural source. It changes the category to Projection; it does not infer a new cabinet system from deformed geometry. Update on a source-free Surface refreshes mapping and bounds without replacing manual mesh edits. **Bake Mesh** evaluates modifiers and removes Screen Builder editing, keeping a normal mesh and a historical screen ID custom property. Both actions explain the loss of procedural editing and support Undo.

## LED workflow

Choose LED with Flat, Arc or Closed. Set cabinet width, height, depth, pixel dimensions, columns and rows. Two explicitly generic example presets are included; no manufacturer specifications are claimed. Presets are plain records in `screen_operators.PRESETS`, ready for verified additions.

For 0.5 × 0.5 m cabinets at 192 × 192 pixels, 20 columns and 8 rows produce:

- 10 × 4 m unfolded canvas; 160 cabinets.
- 3840 × 1536 native pixels.
- 2.604167 mm horizontal and vertical pitch.

**Smooth Arc** uses a true cylindrical model with length `columns × cabinet width`, and derives angle from radius. Closed LED uses this same length/radius convention: for a full revolution choose radius `canvas width / (2π)`. Mesh segments control approximation quality independently of the cabinet count.

**Faceted Cabinets** keeps each cabinet front flat and joins consecutive columns. With N columns there are **N−1 joins**. Twenty columns at 2.5° have 47.5° heading change. For cabinet width w and joint angle a, equivalent vertex-circle radius is `w / (2 sin(|a|/2))`; endpoint chord is `|w sin(Na/2) / sin(a/2)|`. This equivalent circle subtends N×a between endpoints; it is not the (N−1)×a heading change. The true front length is N×w; the equivalent smooth arc N×R×|a| is a different quantity. The UI labels the radius as equivalent. A zero joint angle is a flat wall. Full faceted rings are rejected; use Closed for a welded cylindrical surface.

**Detailed Cabinets** creates one consolidated child mesh of backing/sides, never hundreds of objects or individual pixels. The display owns the front faces; detail has no coincident front faces. Smooth-mode cabinet backs are chordal previs approximations, not a manufacturer model or mechanical fit assessment. Conformed/deformed LED can export its Production Surface; detailed cabinet export is blocked because parametric backing does not follow display modifiers.

## Display, charts and validation

Display controls independently toggle labels, dimensions/resolution, outline, normal indication, wireframe, centre line, detail, cabinet lines and cabinet IDs. Cabinet divisions come from UV intervals rather than arbitrary mesh tessellation; IDs are limited to 400 cabinets to avoid overwhelming the viewport. Projection onto screens still uses normal Beam receivers, including arbitrary non-screen meshes. Cabinet backs are excluded from Beam's projection receiver/occluder cache; this keeps a previs-detail toggle from changing projection studies.

**Test Pattern** assigns a packed image/material with border, centre and quarter marks, grid, distinct corner colours and TL/TR/BL/BR coordinates, U/V directions, screen ID and native resolution. LED charts add cabinet boundaries and numbers where legible. Native coordinates describe edge extents: the right edge of a 3840-pixel canvas is x=3840, not the index of its last pixel. The chart is a bounded preview texture, not native-resolution pixel simulation. **Neutral Material** restores the simple screen/LED material. You can assign your own material without affecting geometry metadata. Pattern previews work in Solid mode through a depth-biased overlay and as a normal material in material/rendered views.

Validate checks missing/out-of-range/non-finite UVs, signed UV orientation, zero-area triangles, overlapping UV triangles, zero-area/duplicate faces and non-manifold edges with more than two incident faces. It reports min/max area-based texel density when this varies appreciably. It cannot infer the intended outward side of an arbitrary sculpture, or certify a self-intersection-free solid. Use Blender Face Orientation and the front-direction overlay to inspect arbitrary surfaces. A mixed/reversed UV winding needs deliberate correction before production export. Intentional UV overlaps/tiling outside 0–1 are blocked by this production-screen contract.

Measurements marked **Nominal** describe the authored canvas when modifiers or object scaling change the displayed mesh; they are not a claim of unchanged physical area. Production export uses evaluated geometry. There is no automatic fitting of projectors, photometric redesign, pixel geometry or stretch heatmap in this release.

## OBJ / FBX export

Select a screen and expand Export Geometry:

- **Production Surface:** evaluated front/display mesh only, one active UV map, no cabinet backing, preview materials, labels, helpers or unrelated objects.
- **Detailed / Previs:** display plus consolidated cabinet backing for LED; annotations and preview materials remain excluded.
- **World Metres:** bake the complete world transform and scene unit scale into vertices; exported object origin is world zero.
- **Screen Local Metres:** authored local geometry in metres at its screen origin; world position, rotation and object scale are omitted.

Both formats use Blender **+Z up / +Y forward** as an explicit neutral convention. FBX includes unit metadata; OBJ coordinates are metres and have no embedded unit declaration. Set matching import units/axes in the receiving system. No proprietary disguise, media-server or game-engine axis conversion is silently applied. Blender export/re-import is verified; independent playback packages still require their own acceptance test.

Export rejects stale parameters, changed scene units, invalid display geometry/UVs and existing files unless Overwrite is enabled. Temporary objects live in an isolated scene. Export preserves the working scene and selection, removes temporary datablocks, and replaces the output file only after successful export. No changes were made to the existing CSV or frozen JSON schema. Screen metadata currently lives in the blend file; geometry handoff is OBJ/FBX.

## Verification and demonstration

`examples/0.8/Beam-Screen-Builder.blend` contains all seven required types plus a conformed display, packed charts, saved study views and a projector blend. Screenshots show each type and the native sidebar. The guide's reference dimensions are retained in that showcase.

Reproducible checks:

- `python3 -m unittest discover -s tests -p 'test_*.py'`: 33 pure tests, including arc input pairs, invalid geometry, cabinet joins and seam/distance UVs.
- `blender --background --factory-startup --python-exit-code 1 --python tests/blender_screen_builder.py`: geometry, edits, duplicates, flip/bake, UVs and 14 OBJ/FBX round trips across seven families; projector targeting and blend-group integration.
- `blender --background --factory-startup --python-exit-code 1 --python tests/blender_screen_edges.py`: selected-face extraction, failure cleanup, Poly/NURBS, diagnostics, detail export/import, centimetre scenes, clipboard and save/reload.
- `tests/verify_screen_ui.py` in a disposable UI process with `--enable-event-simulate`: native sidebar and expanded panels.
- The core acceptance suite also ran through the live Blender MCP connection; the conformed display passed both export/import formats. Existing 15 Beam integration milestones, group lifecycle and first-hit frustum regressions passed.

Other Blender versions/platforms are unverified. Large scenes still need project-specific profiling. Limits are 4096 horizontal segments, 200,000 generated display quads, 20,000 cabinets and a bounded UV-overlap test; exceeding a limit reports an actionable error instead of silently dropping geometry or skipping validation.

## Internal extension points

New modules separate data (`screen_data`), pure geometry (`screen_math`), objects/identity (`screen_objects`), source/conform operations (`screen_surface`), UV diagnostics (`screen_uv`), charts (`screen_patterns`), overlays (`screen_display`), operators/UI, and export. `screens` registers their independent lifecycle. Existing projector property groups and JSON serializers are untouched.

The display mesh is the stable screen identity/relationship endpoint (`Object.beam_screen.uuid`). Future projector fitting or group assignment should reference that UUID and the evaluated display surface, not cabinet objects or an object name. Existing Beam projector output already renders on screen receivers; blend-plane overlays retain their existing nominal-plane meaning. A dedicated screen-space coverage analysis can be added without modifying mesh topology or the current projector solver.
