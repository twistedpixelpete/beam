"""Compact, collapsible study controls; presentation formatting only."""
import bpy
from .projector_object import selected
from . import runtime
from .display_units import dimension,coordinates
from .study_views import selected_view


def section(layout,key,title,closed=False):
    header,body=layout.panel('beam_'+key,default_closed=closed)
    header.label(text=title)
    if body:
        body.use_property_decorate=False
    return body


def readout(layout,label,value):
    row=layout.row();row.label(text=label);value_row=row.row();value_row.alignment='RIGHT';value_row.label(text=value)


def length(value,units):return f'{value:,.2f} m' if units=='m' else f'{value*1000:,.0f} mm'


class PS_PT_main(bpy.types.Panel):
    bl_label='Beam'
    bl_idname='PS_PT_main'
    bl_space_type='VIEW_3D';bl_region_type='UI';bl_category='Beam'
    def draw(self,context):
        from . import presentation
        layout=self.layout;settings=context.scene.ps_study;obj=selected(context);p=obj.ps if obj else None
        units=settings.display_units;record=runtime.CACHE.get(obj.as_pointer()) if obj else None
        box=section(layout,'projector','Projector')
        if box:
            row=box.row(align=True);row.operator('ps.add',text='Add Projector',icon='ADD');row.operator('ps.duplicate',text='Duplicate',icon='DUPLICATE')
            row=box.row(align=True);row.prop(settings,'active_projector',text='Active');row.operator('ps.active_projector',text='',icon='EYEDROPPER')
            if p:
                row=box.row(align=True)
                locked=any(obj.lock_location) or any(obj.lock_rotation)
                row.operator('ps.lock',text='Unlock' if locked else 'Lock',icon='LOCKED' if locked else 'UNLOCKED').action='UNLOCK' if locked else 'LOCK'
                row.operator('ps.isolate',text='Solo',icon='HIDE_OFF');row.operator('beam.frame_projector',text='Frame',icon='VIEWZOOM')
                box.label(text=p.identifier+' · '+context.scene.transform_orientation_slots[0].type.title()+' axes',icon='OUTLINER_OB_CAMERA')
                if not runtime.rigid(obj):box.label(text='Restore projector / parent scale to 1',icon='ERROR')
            row=box.row(align=True);row.operator('beam.create_group',text='Create Blend',icon='GROUP');row.operator('beam.create_group',text='From Selected').from_selection=True
        box=section(layout,'projection','Projection')
        if box:
            if not p:box.label(text='Choose a Beam projector',icon='INFO')
            else:
                box.use_property_split=True
                box.prop(p,'output_mode',text='Output');box.prop(p,'throw_ratio',text='Throw Ratio');box.prop(p,'colour',text='Study Colour')
                row=box.row(align=True);row.use_property_split=False;row.prop(p,'resolution_x',text='X');row.prop(p,'resolution_y',text='Y')
                row=box.row(align=True);row.use_property_split=False;row.prop(p,'shift_h',text='H Shift %');row.prop(p,'shift_v',text='V Shift %')
                box.prop(p,'stack',text='Stack');box.prop(p,'brightness',text='Brightness %');box.prop(p,'lumens',text='Lumens')
                if p.output_mode=='IMAGE':box.template_ID(p,'image',open='ps.load_image')
        box=section(layout,'calculated','Calculated')
        if box:
            if not record or not record['hit']:
                box.label(text='No centre hit',icon='INFO')
                if p:box.prop(settings,'preview_distance_display',text='Preview ('+units+')')
            else:
                m=record['metrics']
                for label,value in [('Throw',length(m.distance,units)),('Image',f'{m.width:,.2f} × {m.height:,.2f} m' if units=='m' else f'{m.width*1000:,.0f} × {m.height*1000:,.0f} mm'),('Density',f'{m.pixels_per_metre:,.0f} px/m'),('Pixel Size',f'{m.pixel_size_m*1000:.2f} mm/px'),('DPI',f'{m.dpi:.1f}'),('Illuminance',f'{m.lux:,.0f} lux')]:readout(box,label,value)
                box.label(text='Nominal image · estimated lux',icon='INFO')
            box.prop(settings,'display_units',text='Units',expand=True)
        if settings.blend_groups:
            box=section(layout,'blend','Blend Group',True)
            if box:
                from .blend_ui import draw_groups
                draw_groups(box,context)
        box=section(layout,'views','Study Views',True)
        if box:
            row=box.row(align=True);row.operator('ps.create_view',text='Add View',icon='CAMERA_DATA');row.operator('ps.capture_current',text='Capture',icon='IMAGE_DATA')
            if settings.views:
                box.template_list('PS_UL_study_views','ps_views',settings,'views',settings,'view_index',rows=2)
                view=selected_view(context)
                if view:
                    row=box.row(align=True);row.operator('ps.view_study',text='View');row.operator('ps.view_study',text='Exit').action='EXIT'
                    row=box.row(align=True);row.operator('ps.view_study',text='Previous',icon='TRIA_LEFT').action='PREVIOUS';row.operator('ps.view_study',text='Next',icon='TRIA_RIGHT').action='NEXT'
                    box.prop(view,'name');row=box.row(align=True);row.operator('ps.export_views',text='Export View',icon='EXPORT');row.operator('ps.export_views',text='Export All').all_views=True
                    advanced=section(box,'view_options','View Options',True)
                    if advanced:
                        advanced.prop(view,'camera');row=advanced.row(align=True);row.prop(view,'resolution_x',text='Width');row.prop(view,'resolution_y',text='Height')
                        for key in ('include_overlays','include_labels','include_frustums','include_projected_identifiers','include_grids'):advanced.prop(view,key)
                        advanced.operator('ps.remove_view',text='Remove View',icon='REMOVE')
        box=section(layout,'display','Display',True)
        if box:
            box.operator('beam.presentation',text='Technical View' if presentation.active(context.area) else 'Presentation View',icon='SHADING_SOLID')
            box.prop(settings,'label_detail',text='Label Detail',expand=True)
            for a,b in [('show_frustums','show_centre_rays'),('show_labels','show_outputs')]:
                row=box.row(align=True);row.prop(settings,a);row.prop(settings,b)
            box.prop(settings,'show_projected_identifiers',text='Projected IDs');box.prop(settings,'show_study_cameras',text='Study Cameras')
            if p:
                box.prop(p,'show_target_marker',text='Active Target Marker')
                sub=section(box,'per_projector_display','Active Projector Display',True)
                if sub:
                    for key,text in [('show_frustum','Frustum'),('show_centre_ray','Centre Ray'),('show_identifier','ID / Labels'),('show_projected_identifier','Projected ID'),('show_grid','Grid'),('show_output','Projection Output')]:sub.prop(p,key,text=text)
            box.prop(settings,'shadow_resolution',text='Preview Quality')
        box=section(layout,'export','Export',True)
        if box:
            row=box.row(align=True);row.operator('ps.export',text='Export CSV',icon='EXPORT');row.operator('ps.export_json',text='Export JSON',icon='FILE_TEXT')
            if p:box.prop(p,'active',text='Include Active Projector in CSV')
            if settings.views:
                row=box.row(align=True);row.operator('ps.export_views',text='Export View');row.operator('ps.export_views',text='Export All').all_views=True
            box.label(text='Designer transforms unvalidated',icon='INFO')
        box=section(layout,'position','Aim / Position',True)
        if box and p:
            row=box.row();row.enabled=False;row.prop(p,'target',text='Centre Target')
            if record:
                unit=context.scene.unit_settings.scale_length
                box.label(text='Lens: '+coordinates([v*unit for v in record['origin']],units))
                if record['hit']:box.label(text='Target: '+coordinates([v*unit for v in record['hit'][0]],units))
                readout(box,'Centre Ray',length(record['slant'],units) if record['hit'] else 'No hit')
            row=box.row(align=True);row.operator('ps.aim',text='Object Centre').mode='OBJECT';row.operator('ps.aim',text='3D Cursor').mode='CURSOR'
            row=box.row(align=True);row.operator('ps.aim',text='Click Surface').mode='CLICK';row.operator('ps.look',text='Look Through')
            row=box.row(align=True);row.operator('ps.move',text='Axis −1 m').distance=-1;row.operator('ps.move',text='Axis +1 m').distance=1
            row=box.row(align=True)
            for label,distance in [('Further',-1),('Closer',1)]:
                op=row.operator('ps.move',text=label+' 1 m');op.distance=distance;op.maintain_aim=True
            box.prop(p,'notes')
        box=section(layout,'metadata','Project Details',True)
        if box:
            for key in ('project_name','venue','revision','client','author'):box.prop(settings,key)
            box.label(text='Beam 0.7 · Twisted Pixel',icon='INFO')
