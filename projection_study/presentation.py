"""Reversible per-viewport preset. Never edits venue materials."""
import bpy
_states={}

def active(area): return bool(area and area.as_pointer() in _states)

def restore(key):
    state=_states.pop(key,None)
    if not state: return
    try:
        space,values=state
        for owner,props in values:
            for key,value in props.items(): setattr(owner,key,value)
    except (ReferenceError,TypeError): pass

@bpy.app.handlers.persistent
def cleanup(*args):
    _save_states.clear()
    for key in list(_states): restore(key)

class BEAM_OT_presentation(bpy.types.Operator):
    bl_idname='beam.presentation'; bl_label='Presentation / Technical View'
    bl_description='Neutral viewport and Minimal labels; return to restore your technical display settings'
    def execute(self,context):
        area=context.area
        if not area or area.type!='VIEW_3D': return {'CANCELLED'}
        key=area.as_pointer()
        if key in _states: restore(key)
        else:
            space=area.spaces.active
            changes=[(context.scene.ps_study,dict(label_detail='MINIMAL')),(space,dict(show_gizmo=False)),(space.shading,dict(type='SOLID',light='STUDIO',color_type='SINGLE',single_color=(.55,.57,.6),background_type='VIEWPORT',background_color=(.09,.10,.12),show_shadows=True,show_cavity=False)),
                     (space.overlay,dict(show_overlays=False,show_floor=False,show_axis_x=False,show_axis_y=False,show_axis_z=False,show_cursor=False,show_extras=False,show_relationship_lines=False,show_outline_selected=False,show_text=False,show_stats=False,show_object_origins=False,show_object_origins_all=False))]
            values=[]
            for owner,props in changes:
                props={k:v for k,v in props.items() if hasattr(owner,k)}
                before={k:(tuple(getattr(owner,k)) if hasattr(getattr(owner,k),'__len__') and not isinstance(getattr(owner,k),str) else getattr(owner,k)) for k in props}
                if owner==space.shading: before['studio_light']=owner.studio_light
                values.append((owner,before))
            _states[key]=(space,values)
            for owner,props in changes:
                for k,v in props.items():
                    if hasattr(owner,k): setattr(owner,k,v)
        area.tag_redraw(); return {'FINISHED'}

CLASSES=(BEAM_OT_presentation,)

_save_states=[]

@bpy.app.handlers.persistent
def before_save(*args):
    # Save the original technical viewport, then restore the live preset after
    # serialization so a .blend never loses the pre-presentation settings.
    _save_states.clear()
    for key,(space,values) in list(_states.items()):
        current=[]
        for owner,props in values:
            state={}
            for name in props:
                value=getattr(owner,name)
                state[name]=tuple(value) if hasattr(value,'__len__') and not isinstance(value,str) else value
            current.append((owner,state))
        _save_states.append((key,space,values,current)); restore(key)

@bpy.app.handlers.persistent
def after_save(*args):
    for key,space,original,current in _save_states:
        try:
            for owner,props in current:
                for name,value in props.items(): setattr(owner,name,value)
            _states[key]=(space,original)
        except ReferenceError: pass
    _save_states.clear()
