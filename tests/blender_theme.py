"""Native XML load, semantic state preservation and text contrast checks."""
import bpy,sys
from pathlib import Path
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root))
import projection_study as addon
p=bpy.context.preferences;t=p.themes[0]
def colors(obj):
 return {v.identifier:tuple(getattr(obj,v.identifier)) for v in obj.bl_rna.properties if v.type=='FLOAT' and v.is_array and v.subtype in {'COLOR','COLOR_GAMMA'}}
state=colors(t.user_interface.wcol_state);selection=(tuple(t.view_3d.object_active),tuple(t.view_3d.object_selected));before=tuple(t.user_interface.wcol_regular.inner)
addon.register();assert tuple(t.user_interface.wcol_regular.inner)==before,'Register must not apply theme'
assert bpy.ops.script.execute_preset(filepath=str(root/'projection_study/themes/Beam.xml'),menu_idname='USERPREF_MT_interface_theme_presets')=={'FINISHED'}
assert selection==(tuple(t.view_3d.object_active),tuple(t.view_3d.object_selected))
for k,v in state.items():
 if k not in {'success','info'}:assert tuple(getattr(t.user_interface.wcol_state,k))==v,(k,v)
def lum(c):
 vals=[v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in c[:3]]
 return sum(a*b for a,b in zip(vals,(.2126,.7152,.0722)))
def contrast(a,b):
 a,b=sorted((lum(a),lum(b)));return (b+.05)/(a+.05)
for name in ('wcol_regular','wcol_tool','wcol_text','wcol_num','wcol_menu','wcol_menu_back','wcol_tab','wcol_list_item'):
 w=getattr(t.user_interface,name)
 for fg,bg in ((w.text,w.inner),(w.text_sel,w.inner_sel)):
  ratio=contrast(fg,bg);assert ratio>=4.5,(name,ratio)
assert contrast(t.outliner.space.text,t.outliner.active)>=4.5
new=tuple(t.user_interface.wcol_regular.inner);addon.unregister();assert tuple(t.user_interface.wcol_regular.inner)==new,'Unregister must not change global theme'
print('THEME PASS: native XML load, opt-in lifecycle, preserved warning/key/selection states, 17 text contrast pairs >=4.5:1')
