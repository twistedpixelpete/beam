"""Open work/planning-ui/Reverse-Mapping.blend in a disposable GPU session."""
import bpy,sys,traceback
from pathlib import Path
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root))
import projection_study as addon
from projection_study import reverse_mapping as reverse,runtime,projection_renderer,study_views
state={'count':0,'uploads':0};original=reverse.image_for
out=root/'work/planning-ui'
def tracked(obj,record):
 shadow=projection_renderer.shadow_map(obj,record);cached=reverse._images.get(obj.as_pointer())
 if not cached or cached[0]!=shadow['signature']:state['uploads']+=1
 return original(obj,record)
reverse.image_for=tracked
def step():
 try:
  if state['count']==0:
   addon.register();bpy.ops.wm.open_mainfile(filepath=str(out/'Reverse-Mapping.blend'))
   state['count']=1;bpy.app.timers.register(step,first_interval=3);return
  area=next(a for a in bpy.context.screen.areas if a.type=='VIEW_3D');region=next(r for r in area.regions if r.type=='WINDOW')
  with bpy.context.temp_override(area=area,region=region):
   area.spaces.active.shading.type='MATERIAL';runtime.refresh();reverse.refresh_gpu();assert not reverse._error,reverse._error
   wall=next(o for o in bpy.context.scene.objects if o.beam_reverse.enabled)
   if state['count']==5:state['baseline']=state['uploads'];state['wrapper']=wall.active_material.as_pointer()
   if state['count']==15:
    assert state['uploads']==state['baseline'],(state['uploads'],state['baseline'])
    assert wall.active_material.as_pointer()==state['wrapper']
    assert all(saved.material.name=='Original UV chart' for saved in wall.beam_reverse.slots)
    view=bpy.context.scene.ps_study.views[0];study_views.export_view(bpy.context,view,out/'reloaded.png')
    reverse.disable(wall);assert wall.active_material.name=='Original UV chart'
    (out/'persistence.txt').write_text(f'PASS save/load restore and ten forced idle redraws without depth uploads or material rebuilds. Initial uploads: {state["uploads"]}')
    bpy.ops.wm.quit_blender();return
   area.tag_redraw();state['count']+=1
  return .3
 except:
  text=traceback.format_exc();print(text,flush=True);(out/'persistence.txt').write_text(text);bpy.ops.wm.quit_blender()
bpy.app.timers.register(step,first_interval=2)
