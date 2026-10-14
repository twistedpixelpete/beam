"""Native collection routing; roles/UUIDs, never names, identify Beam containers."""
import bpy
from .utils import new_uuid
NAMES={'ROOT':'BEAM','PROJECTORS':'Projectors','SCREENS':'Screens','GROUPS':'Blend Groups','VIEWS':'Study Views'}

def collection(scene,role):
    candidates=[scene.collection,*scene.collection.children_recursive]
    existing=next((c for c in candidates if c.get('beam_collection_role')==role and not c.library),None)
    if existing:return existing
    parent=scene.collection if role=='ROOT' else collection(scene,'ROOT')
    result=bpy.data.collections.new(NAMES[role]);result['beam_collection_role']=role;result['beam_collection_uuid']=new_uuid();parent.children.link(result)
    if role=='SCREENS':result['beam_screens']=True
    return result


def organize(scene):
    views={v.camera for v in scene.ps_study.views if v.camera}
    for obj in list(scene.objects):
        role='PROJECTORS' if obj.ps.is_projector or obj.get('ps_helper') else 'SCREENS' if obj.beam_screen.is_screen or obj.get('beam_screen_detail') else 'GROUPS' if obj.get('beam_group_uuid') or obj.get('beam_layout_slot') else 'VIEWS' if obj in views else None
        if not role:continue
        target=collection(scene,role)
        if obj.name not in target.objects:target.objects.link(obj)
        # Preserve arbitrary user collections and links to other scenes.
        for old in list(obj.users_collection):
            if old!=target and (old==scene.collection or old.get('beam_collection_role') or old.get('beam_screens')):old.objects.unlink(obj)
