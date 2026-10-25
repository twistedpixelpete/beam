"""Focused 0.13 additions to the existing guide and training companion."""
def extend(pages,page,A,out):
 from pathlib import Path
 source=out/'screenshots/source'
 for key in ('illuminance','distance','acuity'):
  A[key]=str(out/(key.title()+'.png'))
 A['observer']=str(source/'observer-setup-crop.png')
 for item in pages:
  if item['title']=='Analyse a receiver surface':
   item['blocks'].insert(0,('table',[['Mode','Use it to understand'],['Density','Resolution and detail across a surface'],['Stretch','Pixel deformation on angled geometry'],['Illuminance','Estimated incident light level'],['Distance','Projector-to-surface distance variation'],['Acuity','Apparent pixel size from an audience position']]))
   item['img']=str(source/'five-modes-crop.png');item['width']=3.0;item['caption']='Actual Beam 0.13 Heatmap choices.'
  if item['title']=='Where is it':
   item['blocks'][0][1].extend([['Estimated light level','Surface Analysis → Heatmap → Illuminance'],['Projector distance variation','Surface Analysis → Heatmap → Distance'],['Add audience position','Surface Analysis → Acuity → Add Observer'],['Audience pixel visibility','Surface Analysis → Heatmap → Acuity']])
  if item['title']=='Install and enable Beam':
   item['blocks']=[(t,v) for t,v in item['blocks'] if not (t=='note' and 'workspace-menu correction' in v)]
  if item['title']=='Troubleshoot the current study':
   item['blocks'][0][1].extend([['Acuity has no result','Choose an Observer, check lit receiver and line of sight, then Analyse Surface.'],['No analysis after reopening or Undo','Results are transient. Run Analyse Surface again before export.']])
 page('Estimate incident illuminance','Lux is incident luminous flux per square metre: one lumen over one square metre equals one lux.',[
 ('steps',['Choose Receiver and source scope in Surface Analysis. Select Heatmap → Illuminance, then Analyse Surface.','Read minimum, average and maximum lux. The average includes the whole sampled receiver, including unlit samples at zero.','Move TRAINING_Occluder into the light path and reanalyse. A blocked source contributes zero; other visible sources still add light.']),
 ('p','Overlapping visible projectors add their estimated contributions. Uniformity min / average is explicitly the minimum divided by the average: 1 is equal sampled values; 0 means an unlit sample with a positive average. Exported min / max is separately named.'),
 ('note','Estimated Illuminance is a planning estimate, not calibrated photometric simulation or measured luminance.')],A['illuminance'],'Actual Beam 0.13 training scene analysis.',6.6)
 page('Compare lux ranges and assumptions','Use a common scale to compare revisions without changing the underlying calculation.',[
 ('steps',['Auto Scale uses the current sampled minimum and maximum.','Fixed Range uses zero to Maximum Lux. Use the same maximum for each revision. Values above it saturate; statistics retain their full values.','Enable Target Illuminance and enter Target Lux if useful. It adds a reference label only; it does not change output or certify a pass/fail result.']),
 ('p','Beam assumes uniform nominal flux per raster pixel. Lumens, stack quantity and brightness percentage determine that flux. Perspective and surface angle determine local illuminated area. Visible contributions add.'),
 ('note','The estimate excludes measured brightness distribution, lens transmission, ageing, calibration and colour-mode losses, edge falloff, gain, reflectance, ambient light, black level and colourimetry. Illuminance is incident light; luminance is light leaving a surface toward a viewer.'),
 ('p','Heatmaps are sampled points with gaps, not continuous measurements. Thin occluders may be missed. Zero lux uses the dark palette endpoint.')])
 page('Inspect projection distance','Projection Distance is the Euclidean distance from a projector lens origin to each lit receiver sample.',[
 ('steps',['Select Heatmap → Distance and Analyse Surface.','Read minimum, average, maximum and Variation. Variation equals maximum minus minimum.','In a multi-projector study, the nearest visible source controls each sample. Its UUID is retained for diagnostics. Unlit samples are excluded.']),
 ('p','Display uses Beam’s metres or millimetres preference; structured values use metres. Flat perpendicular walls still have radial distance variation toward their edges.'),
 ('note','This is a planning aid. It is not lens-specific focus or optical depth-of-field certification.')],A['distance'],'Actual training scene distance overlay; inspect the numerical range.',6.6)
 page('Place an audience Observer','An Observer is a lightweight viewing-position object. The training scene includes OBS01 at the audience side of the screen.',[
 ('steps',['In Surface Analysis choose Acuity, then Add Observer. New objects use OBS names and start at the 3D Cursor.','Select OBS01 in the Outliner or viewport. Move it with Blender’s move tool or Base Position controls.','Set Eye Height in metres above the base. The offset is world-up; the default is 1.6 m. The training example uses 1.65 m.','Choose the Observer in Surface Analysis. Set Acuity Threshold in arcminutes, then Analyse Surface.']),
 ('note','The default 1 arcminute threshold is adjustable planning guidance. It is not a universal prediction of eyesight, contrast perception, content readability or ambient-light effects.')],A['observer'],'Actual 0.13 Observer controls. One active Observer is analysed at a time.',3.0)
 page('Interpret Observer Acuity','Angular Pixel Size describes the apparent projected pixel pitch seen from the Observer eye position.',[
 ('p','Larger angular values mean a coarser apparent pixel structure. Moving closer normally increases angular pitch; moving farther away reduces it. Surface foreshortening is included.'),
 ('p','Overlap uses the coarsest apparent visible projector pixel structure. This differs from Density’s highest-detail rule. Viewer-blocked and unlit samples are excluded; percentages refer only to observable lit area.'),
 ('p','Read min / average / max arcminutes and below / at-or-above threshold percentages. The colour range is half to one-and-a-half times the threshold and saturates beyond it.'),
 ('note','After moving OBS01 or changing its threshold, Analyse again. A saved Study View recalls framing; it does not restore an analysis receiver or rerun the calculation.')],A['acuity'],'Actual 0.13 Acuity output with its threshold and source rule.',6.6)
 # Place the new analysis topics before Reverse Mapping; retain all existing topics.
 new=pages[-5:];del pages[-5:];index=next(i for i,p in enumerate(pages) if p['title']=='Reveal mapped content with Reverse Mapping');pages[index:index]=new

def training_additions():
 return [
 ('Estimate light and compare a shadow','Use the same receiver, sources and sample count for both runs.', 'illuminance',[
 ('19  Compare Estimated Illuminance','Set Receiver SCR001 and sources Active Blend Group. Move TRAINING_Occluder to X = -9. Choose Illuminance and Analyse. Record min/average/max. Move the blocker to X = 0 and reanalyse; average incident lux should fall. Try Fixed Range with Maximum Lux 1000, then return to Auto. Target Lux is an optional display reference.')]),
 ('Compare projector distances','Use a working copy; restore the projector position before the next exercise.', 'distance',[
 ('20  Inspect Projection Distance','Choose Distance and Analyse. Record the range and Variation. Select PJ02 and move it one metre farther from the receiver along Y. Reanalyse and compare; nearest-source control may switch locally. Restore its prior position. Inspect TRAINING_Curved_Receiver separately for geometric variation; restore Receiver SCR001 afterwards.')]),
 ('Check pixels from the audience','The original upgraded scene includes OBS01 at Y = -6 m with Eye Height 1.65 m.', 'acuity',[
 ('21  Move OBS01 and change threshold','Choose Acuity and Observer OBS01. Move its base to Y = -2, Analyse and record angular average. Move to Y = -12 and Analyse; angular pitch should decrease. Return to Y = -6, try threshold 0.7 arcmin and reanalyse. Restore 1 arcminute, then Analyse again. Export the Illuminance, Distance and Acuity views and the complete nine-view Study Package.')])]
