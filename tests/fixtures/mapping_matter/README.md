# Live Mapping Matter CSV fixtures

Captured 24 October 2026 from the user's authenticated comparison scene using Mapping Matter's **Export → Projectors (CSV)**, not reconstructed CSV strings. These are technical measurements from the user's controlled test elements; no model assets or proprietary library database is bundled. Original columns/values remain unmodified, including `Projector_Trow-Ratio` spelling.

Scene: 16 × 3.375 m plane centred at world `(0,6000,1687.5)` mm. Original Proj 1/2/3 sit at X −5000/0/5000, Y 0, Z 1687.5, neutral forward +Y, ratio 1. Native Christie 4K10-HS raster 2716×1528, 10000 ANSI lm. Baseline has three rows; subsequent files have a fourth temporary projector. The automated comparison checks the last row. Temporary elements were removed and the original scene restored; no save/publish was performed.

All non-baseline fixtures use lens position `(1234,2345,789)` mm. Unlisted rotations/shifts are zero. Angle columns below are CSV pitch/yaw/roll, not UI XYZ.

| File suffix | Pitch / yaw / roll ° | Ratio | MM H / V % | Raster |
|---|---|---|---|---|
| baseline | 0 / 0 / 0 | 1 | 0 / 0 | 2716×1528 |
| translation | 0 / 0 / 0 | 1 | 0 / 0 | 2716×1528 |
| pitch | 11 / 0 / 0 | 1 | 0 / 0 | 2716×1528 |
| yaw | 0 / 23 / 0 | 1 | 0 / 0 | 2716×1528 |
| roll | 0 / 0 / 17 | 1 | 0 / 0 | 2716×1528 |
| combined | 11 / 23 / 17 | 0.9 | 18 / −24 | 2716×1528 |
| hshift | 0 / 0 / 0 | 1 | 18 / 0 | 2716×1528 |
| vshift | 0 / 0 / 0 | 1 | 0 / 24 | 2716×1528 |
| shift | 0 / 0 / 0 | 0.9 | 18 / −24 | 2716×1528 |
| aspect16x10 | 0 / 0 / 0 | 0.9 | 18 / −24 | 1920×1200 |

See [validation report](../../../docs/MAPPING-MATTER-PARITY.md) for coordinate/shift/target semantics and remaining uncertainty. The actual Designer CSV importer rejected Beam's export-style header; no successful roundtrip claim is made. Reference UUIDs are opaque fixture IDs, not authentication identifiers. Equivalent Beam files deliberately have independent UUIDs.
