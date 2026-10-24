"""Compact cached summaries; pair-level measurements are progressively disclosed."""
from . import blend_groups,ui_context
from .display_units import dimension

def overlap(value,mode):return f"{value['pixels']:,.0f} px" if mode=='PIXELS' else f"{value['percent']:.1f}%" if mode=='PERCENT' else f"{value['metres']:.2f} m"

def values(v,units):return f"{v['pixels']:.0f} px · {dimension(v['metres'],units)} · {v['percent']:.1f}%"

def draw_groups(layout,context):
    from .ui import section,status,actions
    s=context.scene.ps_study;units=s.display_units
    row=layout.row(align=True);row.operator('beam.create_group',text='New Blend',icon='ADD');row.operator('beam.create_group',text='From Selection').from_selection=True
    if not s.blend_groups:status(layout,'No Blend Group');return
    if len(s.blend_groups)>1:layout.template_list('UI_UL_list','beam_groups',s,'blend_groups',s,'blend_group_index',rows=2)
    g=blend_groups.active_group(context)
    if not g:return
    layout.prop(g,'name',text='Group');actions(layout,context)
    anchor=next((m.projector.ps.identifier for m in g.members if m.projector and m.projector.ps.uuid==g.anchor_uuid),'Missing')
    layout.label(text=f'{len(g.members)} members · {g.layout.title()} · Anchor {anchor}')
    if g.layout=='ARRAY':layout.label(text=f'{g.columns} columns × {g.rows} rows')
    data=ui_context.summary(context,g);coverage=data.get('coverage');pairs=data.get('pairs',[])
    if coverage:status(layout,f"{coverage['coverage']:.0f}% · "+('Valid' if coverage['status'].startswith('Valid') else coverage['status']),coverage['coverage']>=99.99 and coverage['status'].startswith('Valid'))
    elif not data:status(layout,'Updating measurements')
    box=section(layout,'blend_overlap','Overlap')
    if box:
        box.prop(g,'input_mode',text='Units')
        if g.layout!='VERTICAL':box.prop(g,'overlap_h',text='Horizontal')
        if g.layout!='HORIZONTAL':box.prop(g,'overlap_v',text='Vertical')
        for axis,title in [('H','Horizontal'),('V','Vertical')]:
            axis_pairs=[p for p in pairs if p['axis']==axis]
            if not axis_pairs:continue
            first=axis_pairs[0];box.label(text=title)
            box.label(text='Requested '+values(first['desired'],units))
            lows={k:min(p['actual'][k] for p in axis_pairs) for k in ('pixels','metres','percent')};highs={k:max(p['actual'][k] for p in axis_pairs) for k in lows}
            if highs['metres']-lows['metres']<1e-5:box.label(text='Actual '+values(first['actual'],units))
            else:
                box.label(text=values(lows,units)+' min');box.label(text=values(highs,units)+' max')
            if any(p.get('gap_m',0)>1e-5 for p in axis_pairs):status(box,'GAP · '+dimension(max(p.get('gap_m',0) for p in axis_pairs),units))
        detail=section(box,'blend_pairs','Pair Details',True)
        if detail:
            for pair in pairs:
                detail.label(text=f"{pair['a']} ↔ {pair['b']} · {pair['axis']}")
                detail.label(text='Request '+values(pair['desired'],units));detail.label(text='Actual '+values(pair['actual'],units))
    row=layout.row(align=True);row.operator('beam.reflow',text='Reflow Group',icon='FILE_REFRESH')
    if g.layout_screen:
        row.operator('beam.ui_new_auto',text='New Auto Blend',icon='ADD')
    box=section(layout,'blend_members','Members')
    if box:
        box.template_list('BEAM_UL_members','beam_members',g,'members',s,'ui_member_index',rows=3,maxrows=4)
        row=box.row(align=True);row.operator('beam.group_action',text='Add Selected',icon='ADD').action='ADD_SELECTED';row.operator('beam.group_action',text='Remove Selected',icon='REMOVE').action='REMOVE'
        row=box.row(align=True);row.operator('beam.group_action',text='New Projector').action='ADD_NEW';row.operator('beam.group_action',text='Reset Member').action='RESET'
    box=section(layout,'blend_advanced','Preview / Editing',True)
    if box:
        row=box.row(align=True);row.prop(g,'show_overlap',text='Overlap');row.prop(g,'preview_edge_blend',text='Feather')
        box.prop(g,'combined',text='Combined Preview');box.prop(g,'notes')
        row=box.row(align=True);row.operator('beam.group_action',text='Duplicate').action='DUPLICATE';row.operator('beam.group_action',text='Ungroup').action='UNGROUP'
