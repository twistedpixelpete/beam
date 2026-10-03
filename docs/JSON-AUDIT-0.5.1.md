# Beam JSON audit — ready for PATCH implementation

Audited 3 October 2026. Changes released as Beam 0.5.1, JSON exporter 1.0.0. Schema name `projection-study` and version `1.0` are retained.

## Reference and scope

The supplied attachment was the audit request, not a separate JSON file. The actual on-disk `examples/0.5/Beam_example.json` was used: 4 projectors, 1 blend group, 1 study view, 4 disguise rows. SHA-256: `a8018ff3db8cbc3c5aab7b3bf3b947c19a93d790fd7813bd47f407db396f77d6`. Its matching saved Blender acceptance scene was re-exported with the updated exporter. The original JSON remains unchanged.

The audit inspected the exporter, CSV conversion boundary, projection calculations, group hierarchy/layout/overlap calculations, view serializer and actual output. Changes are confined to interchange serialization, validation, version metadata, documentation and tests; projection/rendering algorithms are unchanged.

## Must fix before PATCH — completed

| Actual finding | Resolution |
|---|---|
| No producer versions; schema version alone could not identify which Beam/exporter wrote a file. | Added Beam/exporter/Blender versions and Blender build hash. |
| One included no-target or scaled projector erased all JSON disguise rows. | Preserve valid rows and provide per-projector UUID/name/code/message diagnostics; retain the legacy summary. Standalone CSV remains atomic. |
| Group local offsets omitted layout-slot transforms. In the reference all offsets were zero despite different projector positions, so offsets plus controller alone could not reconstruct the group. | Added exact SI group/member/slot matrices, documented world-pose authority and composition. |
| Reference-plane dimensions were cached layout values, but actual pair overlaps used the current anchor plane. | Labelled the cached role and added the current world measurement plane with target/preview status. |
| Member order and frame conventions were implicit; stored horizontal group dimensions could become stale after member removal. | Added explicit zero-based index/row/column and documented stored row-major logical order. Serialized dimensions now reflect current membership. |
| Some units/frames were inferable only from implementation: local offsets, quaternion order, Euler composition, overlap input units and nominal calculations. Legacy CSV lumen headers incorrectly said lux. | Added machine-readable conventions/units and a precise field contract; preserved existing CSV names while documenting their actual lumen units. |
| No exported cross-reference integrity check. A missing/deleted group member could leave a cached dangling UUID. | Added semantic validation that rejects duplicate/dangling references explicitly before writing. This does not reject legitimate no-target records. |
| Linear colours required a conversion for report swatches. | Added standard sRGB and HEX alongside unchanged linear RGB. |
| No portable formal schema or frozen importer contract. | Added Draft 2020-12 JSON Schema, documented enums/nulls/version policy and reusable validation tests. |

Colour convenience was not itself a technical blocker, but the small additive conversion avoids duplicated downstream interpretation and is included in this freeze.

## Confirmed already sound — preserved

All requested projector reporting fields were present: UUID/name/notes, resolution, throw ratio, shifts, stack, brightness, nominal/total lumens, pose, targets, dimensions/density/pixel size/DPI/lux, mode and linear colour. No manufacturer/library placeholders were necessary.

No-target records already used null target points and null calculations; they remain valid. The export now refreshes receiver data once before creating projector records and rows, keeping both parts on the same snapshot. Blank metadata is valid. Existing view UUIDs, filenames, timestamp, camera snapshot and dimensions support empty and populated arrays. Output IDs are stable enums. UUID relationships remain authoritative; labels are not keys.

Retain visibility/preview fields as optional-to-consume presentation hints. They are useful for reproducing a study's presentation and do not determine technical record inclusion. `disguise.validated=false` stays prominent and now has a stable diagnostic convention ID.

## Nice to improve later — deliberately deferred

- Validate axis/rotation/lens-shift conventions in disguise Designer. Until then, rows remain explicitly diagnostic and unvalidated.
- Add an exporter commit/build identity after Git/build provenance exists.
- Add custom-image asset references and packaging if PATCH needs to reproduce projected artwork, rather than report mode/colour.
- Extend camera snapshots (sensor/shift/clip/panoramic settings) only if exact camera reconstruction becomes required; optional view notes/type can be additive.
- Add explicit per-adjacency unavailable-measurement records if reporting needs them. The current contract documents that absent pairs mean unmeasurable, not zero overlap.
- An interchange file is not a full venue/Blender scene archive. Geometry/materials and calibrated photometric data remain outside this schema.

## Before / after

| Area | Before (0.5.0) | After (0.5.1) |
|---|---|---|
| Schema identity | projection-study / 1.0 | Unchanged |
| Existing field names | Existing projector/group/view fields | Preserved |
| Provenance | Product/maintainer only | Added `producer` |
| Units/frames | Partial | Added explicit `conventions`, expanded `units`, frame labels |
| Display colour | Linear RGB | Linear RGB + sRGB + HEX |
| JSON disguise failure | All rows discarded, one message | Valid rows + structured errors + legacy summary |
| Disguise convention | Unvalidated text + false flag | Both retained + stable unvalidated convention ID |
| Group reconstruction | Controller pose + incomplete offsets | Exact controller/member/slot matrices, explicit member order |
| Reference plane | Cached dimensions only | Cached role + current measurement-plane pose/status |
| Null target/calculations | Explicit null | Unchanged, schema-enforced and regression-tested |
| Views/metadata/UI hints | Present | Preserved and documented |
| Integrity | No semantic reference check | UUID checks before writing + portable schema |

New fields are optional in the schema to keep the actual 0.5.0 reference valid; the frozen exporter always emits them. PATCH must feature-detect missing legacy reconstruction fields rather than inventing data. The changed partial-row behavior is intentional and identified by exporter provenance; use `disguise.validation.errors` to determine completeness, and never use row presence as a claim of Designer compatibility.

## Verification

- 27 standalone Python tests passed.
- All 15 existing Blender integration milestones passed in a disposable Blender 5.2.2 LTS process, including CSV refusal, JSON export, groups, save/reload and view export.
- New background Blender contract test passed: non-default 0.01 m scene scale, transformed groups, manually offset/rotated member, world-pose reconstruction, horizontal/vertical/array order, removal dimensions, mixed row eligibility, excluded projectors, stale target clearing, preview planes, blank metadata, empty/populated views and empty scenes.
- Fresh reference re-export: 4 projectors, 1 group, 4 rows.
- Mixed fixture: 5 projector records; 2 valid rows retained; one NO_TARGET error and one INVALID_TRANSFORM error; the deliberately excluded no-target projector has no row and no error.
- All fresh JSON files parse with finite values and validate against Draft 2020-12. UUID uniqueness, group anchors/members/pairs, row UUIDs and error UUIDs resolve. The old 0.5.0 reference also passes the backward-compatible schema.
- Negative checks reject stale no-hit target points, display-label output enums, a false validated-transform claim and dangling member UUIDs.

See `BEAM-JSON-V1.md` for the full importer contract and `beam-json-schema-v1.json` for the portable schema. Fixtures are in `examples/0.5.1/`; the clean `Beam_reference_reexport.json` is the direct continuation of the reference study, and `Beam_mixed_validity.json` exercises null/error handling.
