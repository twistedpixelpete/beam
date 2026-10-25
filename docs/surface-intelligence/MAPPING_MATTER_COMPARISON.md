# Authenticated Mapping Matter comparison · 25 October 2026

Compared through the existing authenticated production.disguise.one Mapping Matter editor, using the existing “Beam Comparison — 16m Screen” fixture. No parity claim is made for undocumented formulas. Screenshots are in `examples/surface-intelligence/reference/`.

## Controlled photometric cases

Common source: Christie 4K10-HS, 10,000 lumens, 2716 × 1528, ratio 1.00, brightness factor 100%, horizontal/vertical shift zero. Lens axis +Y, source Z=1687.5 mm. Plane centre (0,6000,1687.5) mm, 16000 × 3375 mm, rotation X=90°. Three original source X positions −5000/0/+5000 mm.

| Case | Observed Mapping Matter result | Beam comparison / limit |
|---|---|---|
| Flat, non-overlap centre | 6000 mm throw, 6000 × 3375.6 mm nominal image; centre annotation **494 lx**, pixel 2.2 mm. | Uniform-raster model gives **493.7463642 lux**, rounding to 494. This compares a nominal centre value, not receiver-wide statistics. |
| Angled plane | Set receiver rotation Z=30°, selected centred Proj 2. Its annotation remained **494 lx**. Heatmap changed spatially. | Beam centre incident estimate is **427.5969 lux** under the cosine-incidence case. MM centre annotation appears nominal; no point-query or receiver min/avg/max lux readout was exposed here. No numeric spatial parity claim. |
| Two-source overlap | Moved Proj 3 to X=500 mm beside Proj 2. With Projection blending ON, overlap remained around the single-source colour. With it OFF, overlap moved to the approximately **960–1080 lx** band on a 0–1200 scale, while each centre label remained 494 lx. | Beam predicts additive **987.4927 lux** for two 493.7464 lux perpendicular contributions. Visually consistent with the unblended band; exact MM overlap value was not exposed. |
| Opaque blocker | Temporary 1000 mm cube centred (0,3000,1687.5) mm. A dark common shadow and single-source edge bands appeared on the receiver. | Beam's CPU first-hit tests independently verify zero blocked-source contribution and additive surviving sources. MM heatmap agrees qualitatively; no numeric shadow sample readout. |

At exactly coincident projector positions, MM briefly reported a very short 23.7 mm target distance and extreme nominal lux, apparently hitting projector body geometry. That is why the controlled overlap case separated the bodies by 500 mm. Beam excludes projector bodies from its shared receiver raycasts; this is a known implementation difference, not evidence of photometric parity.

Photometric panel exposes explicit minimum/maximum values, lx unit selection, **Scale Log**, and separate **Illuminance** / **Luminance**. Luminance includes the warning “All surfaces are treated as a perfect lambertian reflector”. Beam implements incident illuminance only. MM's palette is multihue; Beam deliberately uses restrained sequential palettes. No uniformity metric or receiver min/avg/max lux table was located in the inspected panel.

## Observer and distance sweep

**Add camera → Observer** exists. Default base is (0,0,0), Eye Height **1650 mm**, target (0,10000,1650), focal length 25.73, H/V FOV 79.317°/50°, raster 1920 × 1080. Temporarily placed it at Y=−5000 mm. The exposed workflow is camera-like. No arcminute threshold or angular-pixel statistics were found in Observer, Camera Settings, Projection Accuracy or Viewport Settings. An equivalent Beam viewing fixture can be set to base (0,−5,0), height 1.65 m; at the centre, a 6/2716 m pixel viewed at approximately 11 m subtends about 0.6904 arcmin. This is a Beam analytic prediction, not a verified MM value.

Projection Accuracy offered only Pixel Density and Pixel Stretch. It explicitly said density uses the max and stretch uses the min across overlaps. Its panel also warned that coverage/overlap assumes clear line of sight and does not account for a physically blocking object. Beam continues its existing sampled first-hit semantics and its original Density-selected Stretch rule; those definitions are not interchangeable.

Viewport Settings exposed Focus Mode (Off / Per Projector / All Projectors), T1=0.10 and T2=0.30, but no explicit SI projection-distance overlay or documented distance metric. A flat/angled/stepped/curved distance comparison and numeric acuity parity could therefore not be established in this session. We do not infer lens distance from a focus display with unknown definitions.

Temporary box and Observer were deleted, Proj 3 X restored to 5000 mm, plane rotation restored, blending restored ON, range restored to 0–250 lux. No scene save or publication was performed. The editor's unsaved-change marker can remain because reversible test edits occurred.
