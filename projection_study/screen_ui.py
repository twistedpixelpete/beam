"""Context-sensitive creation/edit panels using Beam's native layout language."""
import json,textwrap
import bpy
from . import screen_data,screen_math,screen_objects
from .ui import section,readout


def action(layout,text,kind,icon='NONE'):
    op=layout.operator('beam.screen_action',text=text,icon=icon);op.action=kind


def parameters(layout,p,editing=False):
    layout.use_property_split=True;layout.use_property_decorate=False
    if not editing:layout.prop(p,'screen_type');layout.prop(p,'category')
    if p.category=='LED':
        layout.prop(p,'preset');action(layout,'Apply Cabinet Preset','PRESET')
        for a,b,ta,tb in [('cabinet_width','cabinet_height','W m','H m'),('cabinet_px','cabinet_py','X px','Y px'),('columns','rows','Columns','Rows')]:
            row=layout.row(align=True);row.use_property_split=False;row.prop(p,a,text=ta);row.prop(p,b,text=tb)
        layout.prop(p,'cabinet_depth')
        if p.screen_type in {'ARC','CLOSED'}:
            if p.screen_type=='ARC':layout.prop(p,'led_geometry')
            if p.screen_type=='ARC' and p.led_geometry=='FACETED':layout.prop(p,'joint_angle')
            else:
                layout.prop(p,'radius');layout.label(text='Arc length = columns × cabinet width')
            layout.prop(p,'curvature')
    else:
        if p.screen_type=='FLAT':layout.prop(p,'width')
        if p.screen_type=='FLAT' and p.aspect!='FREE':
            ratio=p.aspect_ratio if p.aspect=='CUSTOM' else float(p.aspect.split(':')[0])/float(p.aspect.split(':')[1])
            readout(layout,'Height',f'{p.width/ratio:.3f} m')
        elif p.screen_type!='SURFACE':layout.prop(p,'height')
        if p.screen_type=='FLAT':
            layout.prop(p,'aspect')
            if p.aspect=='CUSTOM':layout.prop(p,'aspect_ratio')
        elif p.screen_type in {'ARC','CLOSED'}:
            if p.screen_type=='ARC':layout.prop(p,'arc_input')
            mode=p.arc_input if p.screen_type=='ARC' else 'RADIUS_ANGLE'
            for k in {'LENGTH_RADIUS':['arc_length','radius'],'LENGTH_ANGLE':['arc_length','angle'],'RADIUS_ANGLE':['radius','angle'],'CHORD_RADIUS':['chord','radius'],'CHORD_ANGLE':['chord','angle']}[mode]:layout.prop(p,k)
            layout.prop(p,'curvature')
        if p.screen_type in {'CURVE','SURFACE'}:
            layout.prop(p,'source')
            if p.screen_type=='SURFACE':
                layout.prop(p,'selected_faces');layout.prop(p,'uv_method')
                if p.uv_method=='PROJECTED':layout.prop(p,'uv_plane')
    if p.screen_type=='CLOSED':layout.prop(p,'seam_angle')
    if p.screen_type!='SURFACE':layout.prop(p,'origin')
    geo=section(layout,'screen_geometry'+str(editing),'Geometry / Resolution',True)
    if geo:
        if p.screen_type in {'FLAT','ARC','CLOSED'} and (p.category!='LED' or (p.screen_type!='FLAT' and p.led_geometry=='SMOOTH') or p.screen_type=='CLOSED'):
            if p.screen_type!='FLAT':geo.prop(p,'quality')
            geo.prop(p,'segments' if p.quality=='SEGMENTS' or p.screen_type=='FLAT' else 'segment_length')
        if p.screen_type=='CURVE':geo.label(text='Path density follows source curve resolution')
        if p.category!='LED':
            geo.prop(p,'vertical_segments');row=geo.row(align=True);row.prop(p,'resolution_x',text='X px');row.prop(p,'resolution_y',text='Y px')
        geo.prop(p,'projection_side')
    if p.screen_type in {'FLAT','ARC','CLOSED'}:
        try:
            # Cheap scalar calculation, never create geometry while drawing.
            if p.category=='LED':
                v=screen_math.led_values(p.cabinet_width,p.cabinet_height,p.cabinet_px,p.cabinet_py,p.columns,p.rows,p.joint_angle if p.screen_type=='ARC' and p.led_geometry=='FACETED' else 0)
                readout(layout,'Canvas',f"{v['width']:.3f} × {v['height']:.3f} m")
                readout(layout,'Native',f"{v['rx']} × {v['ry']} px")
                readout(layout,'Pitch X / Y',f"{v['pitch_x']:.3f} / {v['pitch_y']:.3f} mm")
                readout(layout,'Cabinets',str(v['count']))
                if p.screen_type=='ARC' and p.led_geometry=='FACETED':
                    readout(layout,'Turn (N−1 joins)',f"{v['angle']:.3f}°");readout(layout,'Endpoint chord',f"{v['chord']:.3f} m")
                    readout(layout,'Equivalent radius',f"{v['radius']:.3f} m" if v['radius'] else 'Flat')
                    layout.label(text='Faceted length ≠ smooth arc',icon='INFO')
                    return
            if p.screen_type in {'ARC','CLOSED'}:
                a=screen_math.arc_values('LENGTH_RADIUS' if p.category=='LED' else 'RADIUS_ANGLE' if p.screen_type=='CLOSED' else p.arc_input,p.radius,p.angle,p.columns*p.cabinet_width if p.category=='LED' else p.arc_length,p.chord)
                for title,k,unit in [('Arc Length','length','m'),('Chord','chord','m'),('Radius','radius','m'),('Angle','angle','°')]:readout(layout,title,f'{a[k]:.3f} {unit}')
        except ValueError as exc:layout.label(text=str(exc),icon='ERROR')


class BEAM_PT_screens(bpy.types.Panel):
    bl_label='Screen Builder';bl_idname='BEAM_PT_screens';bl_space_type='VIEW_3D';bl_region_type='UI';bl_category='Beam';bl_order=-1
    def draw(self,context):
        layout=self.layout;obj=screen_data.active(context)
        create=section(layout,'screen_create','Create Screen',True)
        if create:
            p=context.scene.beam_screen_draft;parameters(create,p)
            action(create,'Use Selected Source','SOURCE','EYEDROPPER');create.operator('beam.screen_create',icon='ADD')
        if not obj:return
        p=obj.beam_screen
        edit=section(layout,'screen_edit','Screen · '+p.identifier)
        if edit:
            edit.prop(p,'name');parameters(edit,p,True)
            action(edit,'Update Screen','UPDATE','FILE_REFRESH')
            if abs(p.unit_scale-context.scene.unit_settings.scale_length)>1e-8:edit.label(text='Scene units changed · update required',icon='ERROR')
            if p.built_signature!=screen_objects.signature(p):edit.label(text='Parameters changed · update required',icon='INFO')
            if any(abs(s-1)>1e-5 for s in obj.matrix_world.to_scale()):edit.label(text='Scaled object: parameter sizes are local',icon='ERROR')
        appearance=section(layout,'screen_display','Appearance')
        if appearance:
            row=appearance.row(align=True)
            action(row,'Clean Pattern','PATTERN');action(row,'Neutral Surface','NEUTRAL')
            appearance.prop(p,'show_outline',text='Border')
            if p.category=='LED':appearance.prop(p,'show_detail')
        labels=section(layout,'screen_labels','Labels')
        if labels:
            row=labels.row(align=True);row.prop(p,'show_label',text='Screen ID');row.prop(p,'show_dimensions',text='Dimensions')
            labels.prop(context.scene.ps_study,'label_detail',text='Detail')
            row=labels.row(align=True);row.prop(context.scene.ps_study,'display_units',text='Units',expand=True)
        actions=section(layout,'screen_actions','Actions',True)
        if actions:
            row=actions.row(align=True);action(row,'Duplicate','DUPLICATE','DUPLICATE');action(row,'Flip Front','FLIP')
        technical=section(layout,'screen_technical','Technical Overlays',True)
        if technical:
            technical.prop(p,'show_wire')
            markers=technical.column();markers.enabled=context.scene.ps_study.label_detail=='FULL'
            markers.label(text='Markers · Full detail')
            for key in ('show_normal','show_centre'):markers.prop(p,key)
            if p.category=='LED':
                for key in ('show_cabinet_lines','show_cabinet_ids'):markers.prop(p,key)
        mapping=section(layout,'screen_mapping','Mapping / Surface',True)
        if mapping:
            mapping.prop(p,'uv_method')
            if p.uv_method=='PROJECTED':mapping.prop(p,'uv_plane')
            if p.uv_method=='DISTANCE':mapping.label(text='Rectangular quad grid only',icon='INFO')
            action(mapping,'Apply UV Mapping','REMAP')
            mapping.prop(p,'conform_target');mapping.prop(p,'conform_offset');action(mapping,'Conform to Surface','CONFORM')
            mapping.label(text='Nearest surface · source preserved')
            row=mapping.row();action(row,'Make Surface','SURFACE');action(row,'Bake Mesh','BAKE')
        diagnostics=section(layout,'screen_diagnostics','Diagnostics',True)
        if diagnostics:
            action(diagnostics,'Validate Geometry / UV','VALIDATE','CHECKMARK')
            for line in textwrap.wrap(p.diagnostic,40):diagnostics.label(text=line)
            diagnostics.label(text='Front: '+('reversed' if p.direction=='REVERSED' else 'local −Y (generated walls)'))
        export=section(layout,'screen_export','Export Geometry',True)
        if export:
            export.prop(p,'export_mode');export.prop(p,'export_space')
            export.label(text='Metres · +Z up · no annotations')
            row=export.row(align=True)
            for fmt in ('OBJ','FBX'):row.operator('beam.screen_export',text='Export '+fmt,icon='EXPORT').format=fmt

CLASSES=(BEAM_PT_screens,)
