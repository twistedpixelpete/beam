# Beam 0.8.1 — Screen Builder visual refresh

Maintainer: Twisted Pixel

The Screen Builder now follows Beam’s existing projector-label visual language. No projector rendering, engineering calculations, screen geometry, transforms, UVs, identifiers, schema, or export code changed.

## Before and after

Previously the generated chart used 5×7 bitmap glyphs, prominent coloured corner text and a dense technical grid. Screen measurements and resolution were combined below the object origin, and Flat Screen creation placed Height before Width.

The **Beam Clean Screen Pattern** uses Blender’s bundled Inter font, a neutral dark field, quiet minor grid lines, clearer major divisions and boundary, a small centre cross/ring, muted corner references, and a clear hierarchy: screen ID, physical size, then resolution. No external fonts or dependencies are required. CPU font rasterization also works in background Blender.

The sidebar groups the existing controls into **Screen**, **Appearance**, **Labels**, **Actions**, and collapsed technical/mapping/export sections. Flat screens show Width before Height. Screen naming remains SCR001, SCR002, and so on.

Viewport badges reuse the projector badge component. Width sits below the screen’s visible extent and height beside its right edge, using the shared m/mm formatting. The active screen gets a modestly stronger border. Measurements use no extension lines or arrows, keeping the image unobstructed.

## Try it

1. Install `beam-0.8.1.zip` and restart Blender if Beam was already loaded.
2. Select a managed screen. Under **Screen**, check Width, Height, Aspect, then Update Screen.
3. Under **Appearance**, click **Clean Pattern**. Existing packed charts retain their previous content until regenerated with this button (or a screen update). **Neutral Surface** returns to the existing non-emissive material.
4. Under **Labels**, toggle Screen ID and Dimensions independently. Choose the shared **Detail**:
   - **Off:** ID only, if enabled; no measurement or metadata overlays.
   - **Minimal:** ID plus width and height, if enabled.
   - **Full:** screen name, resolution, existing pitch information, and enabled technical markers/cabinet IDs as applicable.
5. Switch Metres / Millimetres. The two viewport measurements update immediately. These controls are the same scene settings used by projector annotations.
6. Enter **Presentation View**. Minimal labels and the Clean chart remain readable. Exit to restore the previous detail setting.
7. Open Technical Overlays and choose Full detail to inspect the optional existing markers. Wire visibility remains an independent native mesh display control.

The optional second Technical raster pattern was intentionally omitted: Clean is the single default pattern, and Full viewport detail provides existing technical annotations without introducing another saved screen setting.

## Screenshots

Repository examples in `examples/0.8.1/`:

- `sidebar.png`: native Blender controls, width-first ordering, Appearance and Labels.
- `clean-pattern.png`: full-resolution generated chart.
- `minimal.png`: screen badge and separate edge dimensions in metres.
- `full.png`: name/resolution and dimensions in millimetres.
- `off.png`: no measurement/metadata overlays.
- `presentation.png`: clean Presentation View.
- `Beam-Screen-Beauty.blend`: disposable demonstration scene with saved views.

The prior appearance is retained in `examples/0.8/flat-projection.png` and `examples/0.8/sidebar.png` for comparison.

## Files modified

Implementation is confined to `projection_study/screen_patterns.py`, `screen_display.py`, and `screen_ui.py`; the release manifest and READMEs identify 0.8.1. New tests are `tests/blender_screen_beauty.py` and `tests/verify_screen_beauty_ui.py`. This guide is also packaged inside the extension.

## Validation and limits

- 33 existing pure-Python tests pass.
- Screen Builder Blender integration: all seven screen examples and 14 OBJ/FBX round trips pass.
- Screen edge cases pass, including scene units, faceted geometry, detailed export, UVs and save/reopen identity.
- New checks verify antialiased text, the file-backed text-buffer fallback, image reuse, unchanged geometry/UV/identity, independent ID/dimension controls, Off/Minimal/Full and m/mm.
- Native sidebar and expanded panel branches render without exceptions. Presentation restores Full after exiting.

Visual validation uses Blender 5.2.2 LTS on macOS. The Blender 4.5-compatible buffer fallback is exercised in 5.2; a full run on Blender 4.5 and other operating systems has not been performed.

Pattern text is packed image content: its printed physical size stays in metres, while viewport annotations follow Beam’s live display-unit selector. Label Detail controls overlays, not text printed inside the chart. Screens with modifiers or non-unit scale retain **Nominal** measurement qualification; arbitrary mapped surfaces retain **Bounds**. On curved screens, the width is the existing surface-width metric, not the visual chord. Label placement follows the projected screen envelope; dense scenes can still have overlapping labels, and labels may leave the viewport when zoomed very close. No new collision-avoidance system was introduced.

Normal surfaces retain the existing neutral materials. The explicitly selected chart retains the existing unlit material behaviour so calibration content stays legible; neutral screens do not glow. Existing LED functionality is preserved, with no new LED features.
