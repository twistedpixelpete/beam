from . import blend_groups
from .display_units import dimension


def overlap(value,mode):
    return f"{value['pixels']:,.0f} px" if mode=='PIXELS' else f"{value['percent']:.1f}%" if mode=='PERCENT' else f"{value['metres']:.2f} m"


def draw_groups(layout,context):
    from .ui import section
    settings=context.scene.ps_study
    row=layout.row(align=True);row.operator('beam.create_group',text='Create Blend',icon='ADD');row.operator('beam.create_group',text='From Selection').from_selection=True
    if not settings.blend_groups:return
    layout.template_list('UI_UL_list','beam_groups',settings,'blend_groups',settings,'blend_group_index',rows=2)
    group=blend_groups.active_group(context)
    if not group:return
    layout.prop(group,'name',text='Group')
    layout.label(text=f'{group.layout.title()} · {len(group.members)} members')
    if group.layout_screen:
        from .layout_coverage import report
        coverage=report(group,context)
        layout.label(text='Screen: '+group.layout_screen.name)
        if coverage:layout.label(text=f"{coverage['coverage']:.1f}% · {coverage['status']}",icon='CHECKMARK' if coverage['coverage']>=99.99 else 'ERROR')
        layout.operator('beam.auto_blend',text='Auto Blend New Layout')
    layout.prop(group,'input_mode',text='Overlap Units')
    if group.layout!='VERTICAL':layout.prop(group,'overlap_h',text='Horizontal')
    if group.layout!='HORIZONTAL':layout.prop(group,'overlap_v',text='Vertical')
    pairs=blend_groups.pair_data(group,context)
    if any(pair['reference_status']=='preview' for pair in pairs):layout.label(text='Preview plane · no centre hit',icon='INFO')
    if pairs:layout.label(text='Nominal overlap · anchor pixel scale',icon='INFO')
    for pair in pairs:
        box=layout.box();box.label(text=f"{pair['a']} ↔ {pair['b']} · {'Horizontal' if pair['axis']=='H' else 'Vertical'}")
        units=settings.display_units
        for title,key in [('Requested','desired'),('Actual','actual')]:
            v=pair[key];box.label(text=f"{title}: {v['pixels']:.1f} px · {dimension(v['metres'],units)} · {v['percent']:.1f}%")
        if pair.get('gap_m',0)>1e-5:box.label(text='Gap: '+dimension(pair['gap_m'],units),icon='ERROR')
    row=layout.row(align=True);row.operator('beam.group_action',text='Reflow').action='APPLY';row.operator('beam.group_action',text='Solo Group',icon='HIDE_OFF').action='SOLO'
    box=section(layout,'blend_members','Members / Editing',True)
    if box:
        positions=blend_groups.cells(group.layout,len(group.members),group.columns)
        for i,(member,(column,row)) in enumerate(zip(group.members,positions)):
            if not member.projector:continue
            label=f'{i+1}. {member.projector.ps.identifier}'
            if group.layout=='ARRAY':label+=f' · R{row+1} C{column+1}'
            if member.projector.ps.uuid==group.anchor_uuid:label+=' · Anchor'
            box.operator('beam.select_member',text=label,icon='OUTLINER_OB_CAMERA').index=i
        row=box.row(align=True);row.operator('beam.group_action',text='Add Selected',icon='ADD').action='ADD_SELECTED';row.operator('beam.group_action',text='Remove',icon='REMOVE').action='REMOVE'
        row=box.row(align=True);row.operator('beam.group_action',text='New Projector').action='ADD_NEW';row.operator('beam.group_action',text='Duplicate').action='DUPLICATE'
        row=box.row(align=True);row.operator('beam.group_action',text='Select Controller').action='SELECT';row.operator('beam.group_action',text='Reset Member').action='RESET'
    box=section(layout,'blend_advanced','Preview / Notes',True)
    if box:
        row=box.row(align=True);row.prop(group,'show_overlap',text='Overlap');row.prop(group,'preview_edge_blend',text='Feather')
        box.prop(group,'combined',text='Combined Preview');box.prop(group,'notes')
        box.operator('beam.group_action',text='Ungroup').action='UNGROUP'
