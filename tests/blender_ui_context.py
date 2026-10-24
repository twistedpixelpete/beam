"""UI adapters preserve engineering values, context and native collections."""
import bpy,sys,unittest
from pathlib import Path
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root))
import projection_study as addon
from projection_study import ui_context,ui_workspace,ui_collections,study_data,screen_objects,projector_object,runtime
addon.register()
class UIContext(unittest.TestCase):
 def setUp(self):
  for o in list(bpy.data.objects):bpy.data.objects.remove(o,do_unlink=True)
  bpy.context.scene.ps_study.blend_groups.clear();bpy.context.scene.ps_study.pin_context=False
  ui_context.clear();runtime.reset();study_data._seen_selection.clear()
  p=bpy.context.scene.beam_screen_draft;p.width=20;p.height=10;p.aspect='FREE'
  self.screen=screen_objects.create(bpy.context,p);self.screen.location=(0,10,-5)
  self.pj=projector_object.create(bpy.context);bpy.context.view_layer.update();runtime.refresh(True)
 def select(self,obj):
  for old in bpy.context.selected_objects:old.select_set(False)
  obj.select_set(True);bpy.context.view_layer.objects.active=obj;study_data.sync_selection(bpy.context)
 def test_pin_and_receiver_are_independent(self):
  s=bpy.context.scene.ps_study;self.select(self.pj);s.pin_context=True;self.select(self.screen)
  self.assertEqual(study_data.active(bpy.context),self.pj);self.assertEqual(s.inspector,'PROJECTOR');self.assertEqual(ui_context.receiver(bpy.context),self.screen)
  s.pin_context=False;self.select(self.pj);self.select(self.screen);self.assertEqual(s.inspector,'SCREEN')
 def test_inline_target_cancel_and_failed_apply_are_non_destructive(self):
  before=self.pj.ps.throw_ratio;self.assertEqual(bpy.ops.beam.edit_target(field='HEIGHT'),{'FINISHED'})
  draft=bpy.context.window_manager.beam_target;draft.value=7;self.assertEqual(self.pj.ps.throw_ratio,before)
  bpy.ops.beam.apply_target(cancel=True);self.assertEqual(self.pj.ps.throw_ratio,before)
  bpy.ops.beam.edit_target(field='HEIGHT');draft.value=1e-6
  self.assertEqual(bpy.ops.beam.apply_target(),{'CANCELLED'});self.assertEqual(self.pj.ps.throw_ratio,before)
 def test_draft_cannot_apply_to_new_context(self):
  bpy.ops.beam.edit_target(field='WIDTH');bpy.context.window_manager.beam_target.value=3
  other=projector_object.create(bpy.context);bpy.context.view_layer.update();runtime.refresh(True)
  self.assertEqual(bpy.ops.beam.apply_target(),{'CANCELLED'});self.assertEqual(other.ps.throw_ratio,1);self.assertEqual(self.pj.ps.throw_ratio,1)
 def test_pixel_size_uses_mm_and_preserves_resolution(self):
  bpy.context.scene.ps_study.display_units='m';bpy.ops.beam.edit_target(field='PIXEL_SIZE')
  d=bpy.context.window_manager.beam_target;self.assertEqual(d.factor,1000);self.assertEqual(d.units,'mm');d.value=4
  self.assertEqual(bpy.ops.beam.apply_target(),{'FINISHED'});self.assertAlmostEqual(runtime.CACHE[self.pj.as_pointer()]['metrics'].pixel_size_m,.004,places=6)
  self.assertEqual((self.pj.ps.resolution_x,self.pj.ps.resolution_y),(1920,1080))
 def test_collection_identity_survives_rename(self):
  c=ui_collections.collection(bpy.context.scene,'PROJECTORS');uid=c['beam_collection_uuid'];c.name='User renamed collection'
  self.assertIs(ui_collections.collection(bpy.context.scene,'PROJECTORS'),c);self.assertEqual(c['beam_collection_uuid'],uid)
  self.assertIn(self.pj.name,c.objects)
 def test_organize_preserves_unrelated_geometry_and_user_links(self):
  scene=bpy.context.scene;bpy.ops.mesh.primitive_cube_add();venue=bpy.context.object;before=tuple(venue.users_collection)
  user=bpy.data.collections.new('Custom user rig');scene.collection.children.link(user);user.objects.link(self.pj)
  ui_collections.organize(scene)
  self.assertEqual(tuple(venue.users_collection),before);self.assertIn(self.pj.name,user.objects)
 def test_creation_preset_does_not_edit_active_screen(self):
  self.select(self.screen);p=bpy.context.scene.beam_screen_draft;p.preset='GENERIC1000';original=self.screen.beam_screen.cabinet_height
  bpy.ops.beam.draft_preset();self.assertEqual(p.cabinet_height,1);self.assertEqual(self.screen.beam_screen.cabinet_height,original)

result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(UIContext));addon.unregister()
assert not bpy.app.timers.is_registered(ui_workspace.tick)
if not result.wasSuccessful():raise RuntimeError('UI context regressions failed')
