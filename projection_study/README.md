# Beam 0.14.0 - Twisted Pixel

Pre-release beta, still in testing. The installed version is shown in Blender Preferences and Beam's **Project / Workspace** section. The extension manifest is authoritative for the package version.

## Start here

Install this extension ZIP through **Edit > Preferences > Get Extensions > Install from Disk**. Enable Beam, then restart Blender after an upgrade. Do not enable two copies.

In Blender's Layout workspace, open **Edit > Menu Search**, enter **Open Beam Workspace**, and run it. F3 is the search shortcut where the keyboard configuration allows it. Alternatively, open the 3D View sidebar with N, choose **Beam**, expand **Project / Workspace**, and click **Open Beam Workspace**.

The five modules are **Projector**, **Screen**, **Blend**, **Views** and **Export**. Blender's native navigation and Outliner remain available. **Apply Beam Theme** is optional and application-wide; **Restore Previous Theme** restores the saved theme backup.

## New in 0.14.0

**Projection Mode > Cycles Render** creates managed projector lights for Cycles rendered viewports and F12 renders. Select Cycles in Render Properties, then use Rendered shading. Native material transparency lets light pass through cut-outs onto surfaces behind them. Planning remains the default; analysis and study image exports still use geometry-based planning output. Render intensity is approximate, not calibrated photometry.

Projector bodies can be shown or hidden independently from projection output. New-projector defaults and custom model geometry are supported. Custom geometry can cast real shadows in Cycles, including at the lens origin.

Cycles rendering has CPU test coverage on Blender 5.2.2 and 4.5.0 on macOS Apple silicon. GPU rendering and other operating systems remain unverified for this mode. The 0.13 onboarding PDFs and training package remain applicable to the core workflow but do not cover the new render mode.

Use **Mapping Matter CSV** and **Designer CSV** for their respective conventions; they are not interchangeable. **Beam JSON** exports technical data. **Study Package · JSON + HTML + Views** exports the review/handoff package. Analysis samples must be regenerated after reopening.

For the current source build, workflow notes and validated limits, see the [repository documentation](https://github.com/twistedpixelpete/beam). Earlier release downloads and screenshots may represent older UI versions. Confirm that instructions match the version installed.

Blender 4.5+ is the declared minimum; validation is on Blender 5.2.2 LTS/macOS. Windows/Linux and direct Designer application imports are not yet validated. Use copies of studies and independently verify production measurements.
