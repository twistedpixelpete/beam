from . import blend_groups
from .display_units import dimension


def overlap(value,mode):
    return f"{value['pixels']:,.0f} px" if mode=='PIXELS' else f"{value['percent']:.1f}%" if mode=='PERCENT' else f"{value['metres']:.2f} m"


def draw_groups(layout,context):
    box=layout
    row=box.row(align=True);row.operator('beam.create_group',text='Create Blend',icon='ADD');row.operator('beam.create_group',text='From Selection').from_selection=True
    settings=context.scene.ps_study
    if not settings.blend_groups:return
    box.template_list('UI_UL_list','beam_groups',settings,'blend_groups',settings,'blend_group_index',rows=2)
    group=blend_groups.active_group(context)
    if not group:return
    box.prop(group,'name',text='Group')
    box.label(text=f'{group.layout.title()} · {len(group.members)} members')
    positions=blend_groups.cells(group.layout,len(group.members),group.columns)
    members=box.column(align=True)
    for i,(member,(column,row)) in enumerate(zip(group.members,positions)):
        if not member.projector:continue
        label=f'{i+1}. {member.projector.ps.identifier}'
        if group.layout=='ARRAY':label+=f' · R{row+1} C{column+1}'
        if member.projector.ps.uuid==group.anchor_uuid:label+=' · Anchor'
        members.operator('beam.select_member',text=label,icon='OUTLINER_OB_CAMERA').index=i
    row=box.row(align=True);row.operator('beam.group_action',text='Add Member',icon='ADD').action='ADD_SELECTED';row.operator('beam.group_action',text='Remove',icon='REMOVE').action='REMOVE'
    row=box.row(align=True);row.operator('beam.group_action',text='New Projector').action='ADD_NEW';row.operator('beam.group_action',text='Duplicate').action='DUPLICATE'
    box.separator(factor=.5)
    box.prop(group,'input_mode',text='Overlap Units')
    if group.layout!='VERTICAL':box.prop(group,'overlap_h',text='Horizontal')
    if group.layout!='HORIZONTAL':box.prop(group,'overlap_v',text='Vertical')
    pairs=blend_groups.pair_data(group,context)
    if any(pair['reference_status']=='preview' for pair in pairs):box.label(text='Preview plane · no centre hit',icon='INFO')
    for pair in pairs:
        box.label(text=f"{pair['a']} ↔ {pair['b']}")
        row=box.row();row.label(text='Desired '+overlap(pair['desired'],group.input_mode));row.label(text='Actual '+overlap(pair['actual'],group.input_mode))
    row=box.row(align=True);row.operator('beam.group_action',text='Reflow').action='APPLY';row.operator('beam.group_action',text='Solo Group',icon='HIDE_OFF').action='SOLO'
    row=box.row(align=True);row.operator('beam.group_action',text='Select Controller').action='SELECT';row.operator('beam.group_action',text='Reset Member').action='RESET'
    box.separator(factor=.5)
    row=box.row(align=True);row.prop(group,'show_overlap',text='Overlap');row.prop(group,'preview_edge_blend',text='Feather')
    box.prop(group,'combined',text='Combined Preview');box.prop(group,'notes')
    box.operator('beam.group_action',text='Ungroup').action='UNGROUP'
