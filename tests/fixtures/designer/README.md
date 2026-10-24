# Actual Mapping Matter Designer-CSV roundtrip

Captured 24 October 2026 using the authenticated Mapping Matter editor and its **Import → Projectors from Designer CSV** workflow. This tests Mapping Matter's importer, not the disguise Designer application.

`Beam-Designer-fixtures.csv` was produced by Beam (`tests/create_designer_fixtures.py`), not hand-authored. The matching sidecar records its hash, exporter and transform convention. Ten projectors were imported; count and names were checked. Each imported projector was then exported using Mapping Matter's Projectors CSV command. Other imported housings were temporarily hidden to prevent co-located fixtures blocking each other's rays; the original co-located projector was hidden for the neutral case. Original scene visibility was restored and all ten temporary projectors removed afterward.

`MM-return-*.csv` retain the actual downloaded header and corresponding projector row. Unrelated scene rows were removed. Comparisons use `../mapping_matter/Beam-MM-*.csv` as known-good references. Position, Euler orientation, target/aim, throw distance, image dimensions, raster, lens shifts and ratio agree within 0.02 per numeric field (millimetres/degrees); largest observed error 0.001770. Names and count match. See `tests/blender_production.py` for repeatable checks.

Fixtures include neutral, translation, pitch, yaw, roll, combined rotation, H/V/combined shift, 1.0/0.9 ratios and 1920×1200 raster. Near-gimbal cases are internally tested only, not externally imported.
