"""PR #2 engineering review repros; disposable background Blender."""
import bpy,bmesh,sys,unittest
from pathlib import Path
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root))
import projection_study as addon
from projection_study import screen_objects,screen_data,auto_layout,projector_object,runtime,reverse_mapping as reverse,blend_groups,layout_coverage
addon.register()
class Review(unittest.TestCase):
 def setUp(self):
  bpy.context.scene.ps_study.blend_groups.clear()
  for obj in list(bpy.data.objects):bpy.data.objects.remove(obj,do_unlink=True)
  runtime.reset();layout_coverage._cache.clear()
  for mat in list(bpy.data.materials):
   if mat.get('beam_reverse'):mat.use_fake_user=False
  reverse.cleanup_orphans()
  p=bpy.context.scene.beam_screen_draft;p.width=12;p.height=6;p.aspect='FREE'
  self.wall=screen_objects.create(bpy.context,p);self.wall.location=(0,10,-3)
  self.pj=projector_object.create(bpy.context)
  screen_objects.select(bpy.context,self.wall);bpy.context.scene.ps_study.active_screen=self.wall
  self.mats=[];self.wall.data.materials.clear()
  for name in ('Original A','Original B'):
   mat=bpy.data.materials.new(name);mat.use_nodes=True;self.mats.append(mat);self.wall.data.materials.append(mat)
  bpy.context.view_layer.update();runtime.refresh(True)
 def test_restore_after_slot_reorder(self):
  reverse.enable(bpy.context,self.wall);self.wall.active_material_index=1
  bpy.ops.object.material_slot_move(direction='UP')
  reverse.disable(self.wall)
  self.assertEqual([s.material for s in self.wall.material_slots],list(reversed(self.mats)))
 def test_fake_user_does_not_leak_wrappers(self):
  self.mats[0].use_fake_user=True
  for _ in range(3):reverse.enable(bpy.context,self.wall);reverse.disable(self.wall)
  self.assertFalse([m for m in bpy.data.materials if m.get('beam_reverse')])
  self.assertTrue(self.mats[0].use_fake_user)
 def test_explicit_screen_context_wins(self):
  other=screen_objects.create(bpy.context,bpy.context.scene.beam_screen_draft)
  bpy.context.scene.ps_study.active_screen=other
  self.assertEqual(screen_data.active(bpy.context,persistent=True),other)
  self.assertEqual(auto_layout.screen(bpy.context),other)
 def test_anchor_cache_invalidation(self):
  second=projector_object.create(bpy.context);second.ps.throw_ratio=2
  bpy.context.view_layer.update();runtime.refresh(True)
  g=blend_groups.create(bpy.context,[self.pj,second],'HORIZONTAL',2,1,10,'PERCENT',preserve=True);g.layout_screen=self.wall
  first=layout_coverage.report(g,bpy.context)
  g.anchor_uuid=second.ps.uuid;new=layout_coverage.report(g,bpy.context)
  self.assertIsNot(first,new)
  self.assertAlmostEqual(new['pairs'][0]['actual']['pixels'],2*first['pairs'][0]['actual']['pixels'],delta=.01)
 def test_geometry_edit_invalidates_cached_coverage(self):
  bpy.context.view_layer.update();runtime.refresh(True)
  g=blend_groups.create(bpy.context,[self.pj],'HORIZONTAL',1,1,10,'PERCENT',preserve=True);g.layout_screen=self.wall
  bpy.context.view_layer.update();first=layout_coverage.report(g,bpy.context)
  # Same vertex/face counts and bounds, but missing area after an in-plane edit.
  vertex=next(v for v in self.wall.data.vertices if v.co.x<0 and v.co.z==0)
  vertex.co.x+=.1;self.wall.data.update();bpy.context.view_layer.update()
  result=layout_coverage.report(g,bpy.context)
  self.assertIsNot(result,first);self.assertIn('Screen changed',result['status'])
 def test_screen_hole_rejected(self):
  bm=bmesh.new();bm.from_mesh(self.wall.data);bm.faces.ensure_lookup_table();bm.faces.remove(bm.faces[0]);bm.to_mesh(self.wall.data);bm.free();self.wall.data.update()
  with self.assertRaises(ValueError):auto_layout.screen_frame(bpy.context,self.wall)
 def test_overlap_unit_switch_uses_live_anchor(self):
  second=projector_object.create(bpy.context);bpy.context.view_layer.update();runtime.refresh(True)
  g=blend_groups.create(bpy.context,[self.pj,second],'HORIZONTAL',2,1,10,'PERCENT',preserve=True);g.layout_screen=self.wall
  bpy.context.view_layer.update()
  self.pj.ps.throw_ratio=2;bpy.context.view_layer.update();runtime.refresh(True)
  expected=layout_coverage.report(g,bpy.context)['pairs'][0]['desired']['metres']
  g.input_mode='METRES'
  self.assertAlmostEqual(g.overlap_h,expected,places=5)
  g.input_mode='PIXELS';self.assertAlmostEqual(g.overlap_h,192,places=4)
 def test_all_active_material_outputs_wrapped(self):
  mat=self.mats[0];out=next(n for n in mat.node_tree.nodes if n.type=='OUTPUT_MATERIAL');out.target='EEVEE'
  other=mat.node_tree.nodes.new('ShaderNodeOutputMaterial');other.target='CYCLES';other.is_active_output=True
  shader=next(n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED');mat.node_tree.links.new(shader.outputs[0],other.inputs['Surface'])
  reverse.enable(bpy.context,self.wall)
  wrapped=reverse.surface_outputs(self.wall.active_material)
  self.assertEqual(len(wrapped),2)
  self.assertTrue(all(n.inputs['Surface'].links[0].from_node.type=='MIX_SHADER' for n in wrapped))
  reverse.disable(self.wall);self.assertEqual(self.wall.active_material,mat)
 def test_user_material_replacement_preserved(self):
  reverse.enable(bpy.context,self.wall)
  replacement=bpy.data.materials.new('User replacement');self.wall.material_slots[0].material=replacement
  reverse.disable(self.wall)
  self.assertEqual(self.wall.material_slots[0].material,replacement)
  self.assertEqual(self.wall.material_slots[1].material,self.mats[1])
 def test_scaled_projector_not_reported_as_valid_coverage(self):
  g=blend_groups.create(bpy.context,[self.pj],'HORIZONTAL',1,1,10,'PERCENT',preserve=True);g.layout_screen=self.wall
  self.pj.scale=(2,2,2);bpy.context.view_layer.update();runtime.refresh(True)
  result=layout_coverage.report(g,bpy.context)
  self.assertIn('Invalid projector transform',result['status'])
  self.assertEqual(result['coverage'],0)

result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Review))
addon.unregister()
if not result.wasSuccessful():raise RuntimeError('Review regressions failed')
