# Projection Study 0.4.1

Projected identifiers now use smaller study-colour text without a dark backing plate. The projected resolution caption also has no plate. Body labels and distance annotations retain their high-contrast UI badges.

Output → Projected Name controls the active projector's projected name independently of Body / Distance Labels. Helpers → Projected Names is a global switch; each saved Study View also has its own Projected Names checkbox. These controls do not hide the calibration grid or its resolution caption. The output/overlay master switches still hide all projected content. New projected-name controls default to enabled.

Existing Show Identifier data now controls body/distance labels only. New projected-name fields are included in JSON. No UUIDs, optics or engineering calculations change. Install the 0.4.1 ZIP and restart Blender to replace loaded Python modules.

Modified modules: typography.py, projection_renderer.py, viewport_display.py, projector_data.py, study_data.py, study_views.py, ui.py, export_json.py and blender_manifest.toml. Updated GPU acceptance tests verify that hiding body labels leaves projected names intact and that per-projector, global and saved-view projected-name controls independently suppress the name. GPU projection/occlusion pixel tests and 22 pure tests pass on Blender 5.2.2/macOS Metal. The projection limitations documented in UPDATE-0.4.md remain.
