# New Surface Analysis modes · 0.13.0 internal beta

The 0.12.0 full guide remains frozen. This note covers the new build only.

1. Open **Surface Analysis** in the Beam inspector.
2. Choose **Heatmap**: Density, Stretch, Illuminance, Distance or Acuity.
3. Choose Receiver, Projectors (All / Active / Active Blend Group), and Samples.
4. Click **Analyse Surface**. Changing the displayed mode reuses the result.

**Illuminance** shows estimated incident lux. Visible projector contributions add. Read min/average/max and **Uniformity min / average**. Dark receiver samples count as zero. Choose Auto Scale or a Fixed Range maximum for revision comparisons. Target Illuminance is an optional labelled reference; it never changes the projector output. This is not calibrated photometry or luminance.

**Distance** shows the nearest visible projector's lens-to-surface distance. Read min/average/max and Variation. Unlit areas are grey. Values follow Beam's m/mm preference. This is depth planning, not a focus guarantee.

**Acuity**: click **Add Observer**, place its base at the audience position, set Eye Height and Acuity Threshold, then Analyse Surface. The default threshold is a nominal 1 arcminute. Higher angular values mean a coarser pixel structure is more readily resolvable under that assumption, not inherently a worse design. Viewer-blocked regions are excluded. The inspector reports below and at-or-above threshold percentages of the observable lit area.

If you move geometry or change a relevant source/Observer input, **Scene changed · Analyse again** appears. The tool stays explicit; no heavy continuous solve runs while moving objects.

In **Views**, choose **Analysis Overlay → Illuminance / Distance / Acuity** and export the view. The PNG includes a legend and relevant statistics; its `.analysis.json` sidecar includes assumptions and identifiers. **Export → Study Package** collects the same information. Existing CSV formats are unchanged. PATCH receiving-application compatibility is not claimed until its importer has been tested with these additive fields.

Open `examples/surface-intelligence/Beam-Surface-Intelligence.blend` for a flat, angled, curved and stepped receiver, three projectors, a movable blocker and OBS01. Choose a receiver and Analyse after opening; cached analysis is deliberately not saved. Five Study Views are included. Move the blocker or Observer and compare a fresh analysis.
