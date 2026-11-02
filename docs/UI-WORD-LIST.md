# Interface word list — proposal
Status: proposed, for the maintainer to approve. Nothing here has been renamed. Stage 4 of the [usability work](ROADMAP.md) applies only what's approved.

Rules used:
- Say what a control does in the words of a projection job.
- Keep Mapping Matter, Designer and disguise terms where an operator already expects them.
- Don't rename anything stored in a file or written to an export. These are display labels only.

## Worth changing
| Where | Now | Proposed | Why |
|---|---|---|---|
| Project dropdown | Technical | Clean View | It hides viewport guides. "Technical" reads like a status. |
| Header | Active | Editing | "Active" means something else in Blender, and the header can also say Selected. |
| Projector | TARGET / No Target | On Target / No Target: aim at a surface | Says what to do when it fails. |
| Projector | Output | Content | It chooses what the projector shows, and is easy to confuse with Projection Mode. |
| Projector | Study Colour | Helper Colour | It colours the frustum and labels. |
| Projector | Calculated | Image and Throw | Throw, image size, density and pixel size. |
| Projector | Solver · Lens | Solve By · Lens | The same words as the control inside it. |
| Projector | This Projector · Annotations | Labels and Helpers | Plainer, and the tab already says it's this projector. |
| Projector | Advanced | Brightness and Notes | Says what's inside: stack, lumens, export inclusion and notes. |
| Blend | New Blend | New Group of Projectors | Creates new projectors in a layout. |
| Blend | From Selection | Group Selected Projectors | Says what it uses. |
| Blend | New Auto Blend | Auto Blend onto Screen | Separates it from the two above. |
| Blend | New Projector | Add Projector to Group | It's in the member list, and looks like the Projector tab's button. |
| Blend | Reset Member | Reset to Layout Slot | Says what it resets to. |
| Blend | Preview / Editing | Preview and Group Tools | It holds preview toggles, duplicate and ungroup. |
| Screen | Editing / Diagnostics | Screen Tools | Plainer. |
| Views | This View · Export Annotations | Overlays in Export | Says what it affects. |
| Views | Camera / Editing | Camera and Remove | Says what's inside. |
| Export | Two explicit CSV formats · see export notes | Mapping Matter CSV for Mapping Matter · Designer CSV for Designer | The note points to nothing in the interface. |
| Export | Study Package · JSON + HTML + Views | Study Package | The contents move to the tooltip. |
| Surface | Enable on Receiver | Show Coverage on Receiver | Says what you'll see. |
| Surface | Receiver needs UVs | This mesh needs UVs for Reverse Mapping | Readable without knowing the section. |
| Surface | Unsupported receiver material | This mesh's material isn't supported: use node-based materials | Says what to do. Needs checking against what the code accepts. |

## Messages worth changing
Most of Beam's error messages already say what to do. These are the exceptions.

| Now | Proposed |
|---|---|
| A target hit is required | No target: aim the projector at a surface first |
| No active Beam object | Select a projector, screen or group first |
| No layout screen | Choose a flat screen for this group |
| Target context changed; edit the active projector value again | The selection changed. Click the pencil again to edit this value |
| No eligible surface hit, or rotation is locked | Nothing to aim at under the cursor, or the projector's rotation is locked |
| Group controller is missing | This group has lost its controller: use Reflow Group or make a new group |

The last proposed message needs checking: I haven't confirmed that Reflow Group recovers a missing controller.

## Leave as they are
Throw Ratio, H Shift and V Shift, Receiver, Anchor, Reflow Group, Solo, Frame, Study View, Observer, Planning, Cycles Render, Mapping Matter CSV and Designer CSV. These are either projection terms you'd expect or established Beam names.

## Questions for the maintainer
1. Is "Receiver" the right word, or would you say "Surface" on a job?
2. Is "Helper Colour" clear, given a frustum is the main thing it colours?
3. Should "Blend" stay as the tab name, given the feature is called Blend Group everywhere else?
