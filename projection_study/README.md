# Beam

**Beam 0.8.1 — maintained by Twisted Pixel.** A lightweight Blender tool for projection studies, projector management and nominal blend-group planning.

Beam retains the tested Projection Study engineering and GPU projection core. It adds a reversible Presentation View, project metadata, practical blend groups, clearer image-export naming and management shortcuts. See [the 0.5 guide](UPDATE-BEAM-0.5.md) for architecture, changed files, migration and acceptance tests.

## Install / upgrade

Install `dist/beam-0.8.1.zip` through Blender **Preferences → Get Extensions → Install from Disk**, then restart Blender. Open the **Beam** tab in the 3D View sidebar. Maintainer metadata is **Twisted Pixel**.

This is an in-place upgrade: the technical extension ID remains `projection_study` so existing stored `Object.ps`, `Scene.ps_study`, operator identifiers and files continue to work. Do not install an additional copy beside an enabled older version. The source directory retains its existing `projection_study/` name for compatibility; the product, sidebar, About label and release archives are Beam.

Tested on Blender 5.2.2 LTS/macOS Metal. The manifest targets 4.5+, but other Blender versions and platforms remain unverified.

## Individual projectors

Add a projector at the 3D cursor; PJ01 starts facing world +Y with +Z up. Its origin is the lens centre, local −Z is forward and local +Y is up. Use ordinary Blender transforms. Native duplicate, linked duplicate and copy/paste receive fresh PJ identifiers, UUIDs and muted palette colours while preserving technical settings. Body meshes, materials and optical camera data are independent. Notes and identity survive renaming and file saves.

The active study projector stays in the panel when venue geometry is selected. Controls include Solo Active Projector, Frame Active Projector, explicit Lock/Unlock, target-marker visibility, centre rays, frustums, labels and output visibility. Projected Name is independent from Body / Measurement Labels. Projected text uses unboxed study-colour text; viewport annotations use readable white text with dark backing and coloured accents.

Output modes: Solid Colour, Calibration Grid, Identifier, Checkerboard, Blender UV Grid, Blender Color Grid and Custom Image. UV/Color Grid use Blender-generated images. Generated preview images cap their longest side at 4096 to bound memory while preserving aspect; engineering resolution remains native.

## Projection and engineering

One ray through the exact shifted raster centre finds the first evaluated geometry hit for nominal calculations. Any visible mesh-convertible geometry in the frustum receives its corresponding part of one continuous raster. Independent GPU depth maps provide per-ray occlusion: a foreground object blocks only its covered rays, and rays beside it continue farther. The target never clips the whole projection.

Engineering uses metres internally and respects scene unit scale. Width = axial target distance / throw ratio; height = width × resolution Y / resolution X. Pixel density = resolution X / width; pixel size = width / resolution X; DPI = density × 0.0254. Estimated lux = nominal lumens × brightness/100 × stack / nominal area. Lens shift uses percent of full image dimensions. Axial depth and centre-ray slant distance are shown separately.

Metres/millimetres is a display preference. Nominal width/height annotations follow it. A centre miss shows No Target and hides nominal values while off-centre projection remains active. These are nominal measurements, not surface-distortion or advanced photometric analysis.

## Presentation View

The one-click Presentation View preset uses neutral viewport shading and background, studio lighting and fewer native guides/gizmos. Beam projections and enabled study overlays remain. Technical View restores the previous settings, including the original lighting choice. Venue materials are never edited. Save handlers serialize the original technical viewport and then restore the live presentation preset; file load or extension disable clears the temporary preset.

## Blend groups

Select a projector and choose **Create Blend Group**. Configure Horizontal, Vertical or Array, count (or columns × rows), overlap and its input units. Beam duplicates the remaining members; the first projector is the anchor. Use **Create From Selected Projectors** to group existing projectors without moving them.

Overlap can be entered in pixels, percent or metres; switching representation preserves the desired value. Desired and actual nominal overlap are shown for adjacent pairs in pixels, percent and the selected physical display units. Input overlap is bounded to 0–95% for layout calculations.

Changing overlap moves layout slots from the anchor using uniform spacing. Individual projector local adjustments survive those changes and controller movement. **Apply Desired Overlap** recalculates spacing from current anchor optics/target depth and clears positional tweaks; individual aiming and lens shifts remain. **Reset Active Member to Group Position** clears only that member's positional tweak. The anchor is fixed by layout operations.

**Select Group Controller** exposes the parent for moving/rotating the entire arrangement. Keep controller/projector scale at 1. **Remove Active Member** and **Ungroup** leave projector world transforms and data intact. Native duplicates of grouped members become independent projectors rather than sharing the source layout slot.

Show Nominal Overlap draws subtle intersection regions and pair labels on the anchor's nominal plane. Preview Edge Blend adds simple linear feather ramps. Combined Blend Preview maps the anchor's output across the ideal combined canvas and uses an additive planning preview; Individual mode retains each member's own output/colour. Solo Blend Group suppresses unrelated study outputs without deleting data.

## Metadata, views and exports

Optional Project Name, Venue, Revision, Client and Author fields are stored per scene. Projector and group notes are plain text. JSON contains metadata, projector/group UUIDs, calculations, transforms, offsets, actual/desired overlap, views, filenames and CSV data. It adds fields to the existing schema 1.0 contract; the legacy schema key remains `projection-study` for compatibility. There is no live PATCH dependency.

Saved Study Views have View, Previous, Next and Exit controls; no numpad is needed. Export Current View captures the composited editor. Saved camera-view exports provide clean study images with configurable Beam overlays. Presentation styling is taken from the exporting viewport.

Default image names use `Project_Revision_View.png`, for example `Melbourne_Town_Hall_R02_PJ01_Coverage.png`; without project metadata, `Beam_PJ01_Coverage.png`. Spaces/invalid characters become clean underscores. Sanitized collisions get deterministic numeric suffixes.

Current/selected export dialogs show editable filenames and destination. Batch export selects one folder and shows editable proposed filenames in its options. The chosen PNG names are used exactly; invalid suffixes/duplicate batch names are rejected rather than silently changed after saving. Existing files require overwrite opt-in. Completion reports the destination and image count.

**Export CSV** writes a real `.csv`, with the unchanged 27-column Mapping Matter/disguise header, including `Projector_Trow-Ratio`, UUIDs, `Unit_Dim=mm` and `Unit_Illuminance=lux`. No-hit or non-rigid included projectors block CSV export. Designer position/rotation/lens-shift conventions remain unvalidated end to end; the isolated transform boundary still emits the documented raw Blender-axis baseline. No blend curves are exported to disguise.

## Validation and limits

Run `python3 -m unittest discover -s tests -p 'test_*.py' -v` for pure tests. Run `tests/run_blender_tests.py` in a disposable Blender UI session with a 3D View for all integration milestones. Standalone UI verification scripts create their own scenes and quit their own process; use separate Blender processes for them.

The 0.5 release includes a four-projector blend fixture, JSON/CSV examples and individual/combined/feathered screenshots under `examples/0.5/`. The guide describes the horizontal, vertical and 3×2 array acceptance procedure.

This is nominal layout and viewport planning, not calibration. Actual overlap is convex raster intersection on one anchor plane, expressed using anchor pixel scale. It does not measure dense warped coverage on curved/occluded surfaces. Desired placement assumes compatible parallel optics at similar depth; manually varied aim, throw ratio, resolution or lens shift can differ from the ideal. Apply again after anchor optics/distance changes when you want to recompute spacing.

Combined canvas mapping and feather widths follow the ideal layout, not an optimiser; manual deviations can produce seams. A source image fills the combined canvas, so choose a source aspect appropriate to it. The additive preview is not calibrated photometry, gamma/black-level correction or a disguise blend simulation. Changing group topology requires regrouping. Controller scaling, arbitrary transform constraints and simultaneous multiwindow/multiscene editing are unsupported.

Finite 512/1024/2048 shadow maps can alias thin edges; geometry is treated as opaque/double-sided. Projector bodies/helpers do not act as receivers. There is no material projection or F12-render output, volumetric transmission, manufacturer database, LED system or PDF reporting. Very dense scenes and high GPU projector counts need further profiling.

License: GPL-3.0-or-later.

When the anchor has no centre hit, group layout/overlap uses its no-hit preview plane. The group UI marks this explicitly, and JSON pairs report `reference_status` and `actual_plane_distance_m`. These are planned nominal overlaps, not measured receiver coverage.

## JSON Schema v1 freeze (0.5.1)

The PATCH handoff contract is in `docs/BEAM-JSON-V1.md`, audit findings in `docs/JSON-AUDIT-0.5.1.md`, and portable schema in `docs/beam-json-schema-v1.json`. Valid disguise rows now survive other projector errors. Producer versions, display colours, exact group transforms and explicit conventions are added without renaming schema 1.0 fields. Fresh examples and tests cover null targets, references and reconstruction. The separate CSV export remains atomic and its Designer transform convention remains unvalidated.

## Frustum helper termination (0.5.2)

Each displayed corner ray stops at its first visible evaluated scene-surface hit. Rays that miss end at the nominal centre-target depth, or the configured preview distance if the centre also misses. Helper endpoints are cached independently from the projection extent. Projection coverage, multi-surface occlusion, centre targets, engineering calculations and JSON schema are unchanged.

## Editable Blend Groups (0.6.0)

The group panel now lists members and supports Add Selected, Add New, Remove Selected, Reflow and Duplicate Blend Group. Existing-member add/remove preserves world poses. Copies have new controllers, UUIDs, PJ numbers and colours, with independent data and preserved local offsets. Native controller/hierarchy duplicate and paste are supported. Beam selections default to Local orientation and restore the previous orientation for unrelated objects. See `docs/UPDATE-BEAM-0.6.md` for implementation details, acceptance tests, migration and limitations.

## Beauty and usability (0.7.0)

Collapsible sidebar sections, compact calculated readouts, restrained PJ accents and discreet outside-edge dimensions. Display offers Off / Minimal / Full; Presentation temporarily selects Minimal. Group overlap controls are easier to scan. Engineering and export contracts are unchanged. See UPDATE-BEAM-0.7.md (under docs in the source archive) for modified files, test instructions and limitations.

## Screen Builder (0.8.0)

Create and edit Flat, Arc, Curve, Closed and Surface screens, plus cabinet-based flat/smooth/faceted LED walls. Includes distance-based UVs, source extraction/conforming, packed test charts, diagnostics, independent screen IDs, separate cabinet detail and isolated OBJ/FBX export. Open Screen Builder in the Beam sidebar. See `SCREEN-BUILDER.md` (under `docs/` in the source repository) for units, arc/joint conventions, export axes, practical limitations and acceptance tests. The demonstration file and screenshots are under `examples/0.8/`.

### Screen visual refresh (0.8.1)

Screen Builder now uses the Beam Clean pattern with bundled Inter typography, a restrained calibration grid, and separate edge measurements. Width comes before Height. Appearance and Labels have dedicated sections, sharing Beam’s existing Off / Minimal / Full detail and m / mm controls. Select an existing screen and click **Clean Pattern** to replace its previously packed chart. See `docs/SCREEN-BEAUTY.md` (or packaged `SCREEN-BEAUTY.md`) for screenshots and checks.
