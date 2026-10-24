"""Opt-in native theme application with a durable, one-level theme-only backup."""
import json
from pathlib import Path
import bpy
_ready=False

def folder(create=False):
    value=bpy.utils.user_resource('CONFIG',path='beam_theme',create=create)
    if not value:raise OSError('Theme backup directory is unavailable')
    return Path(value)

def metadata():
    try:
        data=json.loads((folder()/'previous.json').read_text())
        return data if isinstance(data,dict) else {}
    except (OSError,ValueError):return {}

def write_metadata(data):
    path=folder(True)/'previous.json';temp=path.with_suffix('.tmp')
    temp.write_text(json.dumps(data));temp.replace(path)

def refresh():
    global _ready
    _ready=bool(metadata().get('active') and (folder()/'previous.xml').is_file())

def load(context,path):
    result=bpy.ops.script.execute_preset(filepath=str(path),menu_idname='USERPREF_MT_interface_theme_presets')
    if result!={'FINISHED'}:raise RuntimeError('Theme could not be loaded')
    for window in context.window_manager.windows:
        for area in window.screen.areas:area.tag_redraw()

class BEAM_OT_apply_theme(bpy.types.Operator):
    bl_idname='beam.apply_theme';bl_label='Apply Beam Theme'
    bl_description='Apply the application-wide Beam palette; keep a theme-only backup for Restore Previous Theme'
    def invoke(self,context,event):return context.window_manager.invoke_props_dialog(self,width=340,confirm_text='Apply Theme')
    def draw(self,context):
        self.layout.label(text='Applies to all Blender workspaces.')
        self.layout.label(text='Your current theme can be restored.')
    def execute(self,context):
        import _rna_xml
        try:
            refresh()
            if not _ready:
                path=folder(True)/'previous.xml';temp=path.with_suffix('.tmp')
                _rna_xml.xml_file_write(context,str(temp),bpy.types.USERPREF_MT_interface_theme_presets.preset_xml_map)
                temp.replace(path)
                write_metadata(dict(active=True,filepath=context.preferences.themes[0].filepath,label=bpy.types.USERPREF_MT_interface_theme_presets.bl_label))
            load(context,Path(__file__).parent/'themes/Beam.xml');refresh()
        except (OSError,ValueError,RuntimeError) as exc:
            self.report({'ERROR'},str(exc));return {'CANCELLED'}
        return {'FINISHED'}

class BEAM_OT_restore_theme(bpy.types.Operator):
    bl_idname='beam.restore_theme';bl_label='Restore Previous Theme'
    bl_description='Restore the theme captured before Apply Beam Theme, including after a Blender restart'
    @classmethod
    def poll(cls,context):return _ready
    def execute(self,context):
        try:
            data=metadata()
            if not data.get('active'):raise ValueError('No previous Beam theme backup')
            load(context,folder()/'previous.xml')
            context.preferences.themes[0].filepath=data.get('filepath','')
            bpy.types.USERPREF_MT_interface_theme_presets.bl_label=data.get('label','Presets')
            data['active']=False;write_metadata(data);refresh()
        except (OSError,ValueError,RuntimeError) as exc:
            self.report({'ERROR'},str(exc));return {'CANCELLED'}
        return {'FINISHED'}

CLASSES=(BEAM_OT_apply_theme,BEAM_OT_restore_theme)
