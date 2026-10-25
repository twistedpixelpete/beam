"""Documentation-critical native rail modes and inspector fallback contract."""
import bpy,sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root))
import projection_study as addon
from projection_study import ui,projector_object
addon.register();pj=projector_object.create(bpy.context);bpy.context.scene.ps_study.inspector='PROJECTOR'
class Layout:
 def __init__(self):self.calls=[]
 def column(self,**kw):return self
 def grid_flow(self,**kw):return self
 def row(self,**kw):return self
 def operator(self,name,**kw):self.calls.append((name,kw));return SimpleNamespace()
for width in (60,200):
 for active in ('PROJECTOR','SCREEN','GROUP','VIEW','EXPORT'):
  layout=Layout();context=SimpleNamespace(region=SimpleNamespace(width=width),scene=SimpleNamespace(ps_study=SimpleNamespace(inspector=active)))
  ui.navigation(layout,context,True)
  assert len(layout.calls)==5 and sum(x[1]['depress'] for x in layout.calls)==1
  assert [x[1]['text'] for x in layout.calls]==(['']*5 if width==60 else ['Projector','Screen','Blend','Views','Export'])
  for kind,title,icon in ui.MODULES:
   assert ui.BEAM_OT_inspector.description(context,SimpleNamespace(kind=kind))==title+' inspector'
for visible,expected in ((True,0),(False,3)):
 layout=Layout()
 with patch.object(ui,'rail_visible',return_value=visible):ui.actions(layout,bpy.context)
 assert len(layout.calls)==expected
assert bpy.ops.ps.export_json.get_rna_type().name=='Export Beam JSON'
import tomllib
assert ui.BEAM_VERSION==tomllib.loads((root/'projection_study/blender_manifest.toml').read_text())['version']
addon.unregister();print('PRE-DOC UI PASS: five modules, narrow icons, wide labels, each active state/tooltips, hidden rail action fallback, current JSON search name/version')
