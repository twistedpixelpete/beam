# Projection Study 0.4.2

Added Nominal width and Nominal height annotations at the top and right edge midpoints of the image plane at the centre target. They update from existing engineering calculations, use the selected metre/millimetre display, and appear in current/saved study image exports.

Body / Measurement Labels controls these annotations alongside the projector body label and target distance. Global Labels and saved-view Labels also apply. Projected Name remains independent. Dimensions are hidden when there is no target or projected output is disabled for that projector.

The values describe the nominal image at centre-target axial depth, not measured coverage over angled or multiple receiving surfaces. Projection geometry and calculations are unchanged.

Modified viewport_display.py, projector_data.py and the extension manifest. Visually checked the exported annotations and passed the GPU projection/occlusion and independent-name visibility acceptance suite on Blender 5.2.2/macOS Metal.

Install the 0.4.2 ZIP and restart Blender. Existing files require no migration.
