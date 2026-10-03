# Beam JSON Schema v1 — PATCH importer contract

Frozen with Beam 0.5.1 / JSON exporter 1.0.0. Maintainer: Twisted Pixel.

`schema: "projection-study"` and `schema_version: "1.0"` are unchanged. Beam is the technical source of truth; PATCH consumes the supplied calculations for reporting. There is no PATCH runtime dependency.

## Version policy and compatibility

`producer` records `beam_version`, `exporter_version`, `blender_version` and `blender_build_hash`. The exporter version identifies serialization changes independently of the add-on. There is no exporter commit/build hash yet because the project has no Git/build identity; none is invented. `exported_at` is an ISO 8601 UTC timestamp.

Use `schema` plus `schema_version` for dispatch, then feature-detect additive fields. Unknown properties must be ignored or preserved. Existing field names, types, units and enum meanings are frozen. Additive optional properties may remain in 1.0; changed meanings, removed/renamed fields, new required data or incompatible enum/convention changes require an explicit schema migration. Do not reinterpret a historical file using the currently installed Beam version.

`beam-json-schema-v1.json` is a Draft 2020-12 schema. Audit additions are optional in the validator to accept pre-audit Beam 0.5.0 files, but exporter 1.0.0 always emits them. Files without `producer` are legacy: reporting is possible, but missing group transforms must not be guessed from names or desired overlap. Run semantic UUID checks as well as JSON Schema validation; JSON Schema alone cannot check foreign keys or matrix consistency.

## Identity and optional metadata

Projector, blend-group and study-view UUIDs are stable record identities and unique throughout a file. Group anchors, members, pair endpoints, disguise rows and per-projector errors reference projector UUIDs. PJ names, object names, target object names and camera names are display labels, not foreign keys. View identity is its UUID; camera pose is an embedded snapshot, not a separate camera entity.

`project_metadata` contains optional strings `project_name`, `venue`, `revision`, `client`, `author`. Empty strings and absent metadata properties are valid. Beam exports all five, including blanks. Projector and group `notes` may be blank.

The exporter rejects corrupt duplicate/dangling UUID relationships with an actionable error before writing. A legitimate no-target projector is not a corrupt relationship and remains in the file.

## Coordinates, rotations and units

All geometry outside `disguise.rows` uses metres, regardless of Blender scene scale or chosen display units. `position_m` is the projector's optical origin in Blender world space. World space is right-handed, Z up. A projector's local -Z is its optical forward axis, +Y is up, +X is right. World origin is the Blender scene origin, not a venue survey origin.

Projector `rotation` is world-space XYZ Euler angles in degrees. For column vectors, `R = Rz @ Ry @ Rx`; rotate local vectors into world space with R. Quaternions are normalized rotations in **[w, x, y, z]** order. Matrices are four arrays of four numbers (row-major storage), acting on column vectors. Matrix translation components are metres; the linear 3×3 block is dimensionless. Group and camera rotations are world rotations; member rotations are explicitly local.

| Fields | Meaning / unit |
|---|---|
| `position_m`, `target.point_m`, group/plane positions, local offsets | Metres in the declared frame |
| Resolution x/y | Pixels |
| `throw_ratio` | Nominal throw distance / image width, dimensionless |
| Lens shift horizontal/vertical | Percent of **full** image width/height, positive local +X/+Y |
| Brightness | Percent, 0–100 |
| Stack quantity | Number of identical contributing projectors |
| Nominal / total lumens | Lumens (lm); total = nominal × brightness / 100 × stack |
| `throw_distance_m` | Axial depth of current centre-ray hit along optical -Z |
| `centre_ray_distance_m` | Slant distance from optical origin to centre-ray hit |
| Image width/height | Metres on a nominal rectangle perpendicular to optical axis at axial depth |
| Pixel density | Horizontal resolution / nominal image width, px/m |
| Pixel size | Metres/pixel and millimetres/pixel, explicitly suffixed |
| DPI | Pixels/inch, pixel density × 0.0254 |
| Estimated illuminance | Total lumens / nominal image area, lux |
| Overlap `pixels`, `percent`, `metres`, `fraction` | px, percentage 0–100, m, dimensionless 0–1 respectively |
| Camera lens / ortho scale | mm / m respectively |

Calculated dimensions/density/lux are nominal planning values, not measured warped surface coverage. Lux does not model incidence angle, lens loss, receiver reflectance or calibrated blending. `transform_valid=false` means non-rigid projector transforms are unsupported: retain the record for reporting its issue; do not treat its nominal geometry or disguise transform as valid.

`target.space` is `blender_world`; `target.automatic=true` means the current centre ray selects the first eligible visible evaluated surface. `filter_object_name` remains null for compatibility. The target is a reference point, not a crop/receiver filter for the full projection.

For no hit, `target.status="no_hit"`, `point_m=null`, `object_name=null`, and **`calculated=null`**. Never replace these with zero or retain a previous export's values. Independent settings such as output lumens remain available.

## Blend groups and reconstruction

A group's members array is authoritative stored order. It is not sorted by object name, PJ number or spatial coordinates at export. `member_index`, `row`, `column` are zero-based. Horizontal layouts advance +X; vertical layouts advance -Y; arrays are row-major (+X across, -Y down) in group-local space. Grouping existing projectors preserves their positions, so logical left/right order is not a promise of physical placement. Removing a member compacts indices; identify persistent members by UUID, not index. `rows` reflects occupied rows; horizontal/vertical dimensions reflect current members; ARRAY columns retain the configured column count, including a partially occupied final row.

World projector poses are the authority for PATCH reporting and placement. Group settings describe layout intent, not an instruction to recalculate current positions. For a rigid study, exact reconstruction is:

```
projector_world_matrix = group.transform.matrix @ member.transform_in_group
```

`group.transform` is the current controller world transform. `member.transform_in_group` is the exact current projector transform relative to that controller. These include manually changed poses and existing-selection layouts, not just ideal spacing. Compare reconstructed translation/rotation with the projector's world pose within floating-point tolerance (e.g. 1e-5 m and matrix-component tolerance); warn on conflicts and prefer the world pose. Matrix data can preserve scale/shear, but a non-rigid projector remains technically invalid.

`layout_slot_transform` is the slot's exact group-local transform. To recreate the rig, create the group at its matrix, a slot at `layout_slot_transform`, and place the projector relative to that slot using `inverse(layout_slot_transform) @ transform_in_group` with identity parent inverse. Legacy `local_offset_m` and `local_rotation_quaternion_wxyz` describe Blender's stored projector basis relative to its layout slot; they are editing hints, **not** a complete group-relative pose. Do not add the offset again to `transform_in_group`. Slot/relative transforms are null when unavailable (including a singular group controller); use the world pose and flag reconstruction as unavailable.

`reference_plane` retains the last layout-reference distance/width/height, captured at group creation or layout updates; it is not a current measurement or a world-space plane pose. `role="last_layout_reference_dimensions"` makes this explicit. `measurement_plane` adds the current world origin, orientation, distance and dimensions used by adjacent overlap calculations. Its local XY plane has origin at the unshifted optical-axis point at the anchor's axial depth. `status="target"` uses the anchor's current hit; `status="preview"` uses the explicitly nominal no-hit preview depth. The plane may be null if unavailable. A preview plane does not turn null projector calculations into real measurements.

`desired_horizontal_overlap` and `desired_vertical_overlap` are raw user inputs in the unit selected by `input_mode`: PIXELS → px, PERCENT → percent, METRES → m. Pair `desired` values are converted using the current anchor dimensions/resolution and clamped to a 0–0.95 fraction. Raw inputs can exceed that effective range. Pair `actual` is the intersection polygon's extent along anchor-plane X (H) or Y (V); it is a nominal plane measurement, not surface-overlap area. Pixels/percent use the anchor's current axis resolution/dimension. Pair endpoints use UUIDs; `a` and `b` are labels. A pair absent from `adjacent_pairs` was not measurable (for example rays parallel to or behind the plane); absence is **not zero overlap**. A measurable empty intersection has zero overlap.

## Disguise diagnostics and validation

`disguise.validated` remains **false**. Convention ID is `blender_xyz_euler_xyz_unvalidated_v1`. Raw Blender world XYZ in mm and XYZ Euler degrees are diagnostic values, not a claim of Designer-compatible axis, handedness, rotation order, zero pose or lens-shift signs. Validation will require a controlled Designer round trip and a new convention identifier; this identifier must never be reinterpreted as validated.

The 27 column names/order remain unchanged. Map a row using `disguise.columns`; its final value is projector UUID. Legacy headers `Projector_Lumens(lux)` and `Projector_Total_Lumens(lux)` actually contain **lumens**, not lux. `Projector_Trow-Ratio` retains its legacy spelling. Do not derive physical units from those legacy header typos. Lens/target XYZ, distance, width and height are mm; angles are degrees; illuminance is lux; DPI is px/in; shifts/brightness are percent; resolution is px; stack is a count.

All projector records remain in `projectors`, including excluded and invalid ones. Only `include_in_disguise_export=true` projectors are considered for rows. Eligible rows are retained even when another projector fails. `disguise.validation.errors` has `projector_uuid`, `projector_name`, stable `code` and explanatory `message`:

- `NO_TARGET`: included projector has no current centre hit.
- `INVALID_TRANSFORM`: included projector has unsupported scale/shear/mirroring.
- `NO_ACTIVE_PROJECTORS`: scene-level export diagnostic; UUID/name are null.

A projector may have both errors; inactive/excluded projectors are intentionally absent from rows without an error. `scope="disguise_rows"` distinguishes row eligibility from JSON validity. Null targets are valid JSON records. `disguise.error` remains a legacy nullable summary; PATCH should use structured codes. Rows being eligible does not override `validated=false`. The separate CSV file export remains atomic: any invalid included projector prevents writing the CSV.

## Colours and output modes

`study_colour_linear_rgb` is retained unchanged. `study_colour_srgb` gives 0–1 standard sRGB components and `study_colour_hex` gives uppercase `#RRGGBB`, suitable for report swatches. Linear values are clamped to [0,1] for the display conversion only; standard sRGB encoding and nearest 8-bit rounding are used. These swatches do not include Blender AgX/Filmic, exposure, lighting or display-profile transforms.

Stable case-sensitive mode IDs:

| ID | Meaning |
|---|---|
| SOLID | Solid study colour |
| GRID | Calibration grid |
| ID | Identifier |
| CHECKER | Checkerboard |
| UV_GRID | Blender UV Grid |
| COLOR_GRID | Blender Color Grid |
| IMAGE | Custom image |

These are identifiers, not translated UI labels or Blender enum integer values. Image assets themselves are not packaged in v1; an IMAGE mode identifies intent, not enough data to reproduce the image content.

## Study views and presentation hints

`study_views` is always an array; empty is valid. Each record has UUID, name, camera name and optional embedded world pose/intrinsics snapshot, output resolution in pixels, overlay flags, `expected_image_filename`, actual `exported_image_filename` and `exported_at`. Actual filename/timestamp are null until an export is recorded. Expected names are proposals; never present them as proof an image exists. Recorded filenames do not guarantee the external image is still present. `current_view_image` has nullable actual filename/timestamp and is not a named study-view record.

Camera `type` is PERSP, ORTHO or PANO. Lens/ortho scale support reporting, but the snapshot does not yet promise exact camera recreation (sensor fit/size, shifts, clipping and panoramic settings are not all included). Additional optional view notes/type, camera fields and image metadata can be added without renaming existing fields.

Keep `helper_visibility`, projector `visibility`, view `overlays`, `preview_edge_blend` and `combined_preview`: they are useful presentation/reconstruction hints. They do not change projector existence, identity, optical settings, exported technical calculations or disguise inclusion. PATCH may ignore them for technical reports. `projection_model` describes Beam's current receiver/preview model, not a photometric calibration guarantee.

## Validation and fixtures

Validate JSON types/nulls/enums using the supplied schema, then check unique UUIDs and foreign keys (`projection_study/json_contract.py` is pure Python). Blender exports fail explicitly for corrupt UUID relationships. Export serialization uses `allow_nan=False`.

The `examples/0.5.1/` fixtures include a fully valid study with populated view, mixed row eligibility with blank metadata and empty views, a no-target group preview, and a fresh export of the original 0.5 acceptance scene. Negative tests reject stale target points, unknown UI-label enums, falsely validated transforms and dangling member UUIDs. Floating-point values are not rounded for interchange.
