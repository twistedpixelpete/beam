"""Versioned PATCH-neutral study package, with a small standalone HTML reader."""
import json,html,shutil,tempfile,os
from dataclasses import asdict
from uuid import UUID
from pathlib import Path
from . import export_json,analysis_runtime,optics_validation


def document(context):
    from .study_guidance import THRESHOLDS,BASIS
    source=export_json.document(context);warnings=[]
    for p in source['projectors']:
        if not p['calculated']:warnings.append(dict(code='NO_TARGET',uuid=p['uuid'],message='No centre target'))
        if not p['transform_valid']:warnings.append(dict(code='INVALID_TRANSFORM',uuid=p['uuid'],message='Scaled or sheared projector'))
    for group in source['blend_groups']:
        for pair in group['adjacent_pairs']:
            if pair.get('gap_m',0)>0:warnings.append(dict(code='BLEND_GAP',uuid=group['uuid'],message=f"Gap between {pair['a']} and {pair['b']} on the measurement plane"))
    optics=[]
    for obj in context.scene.objects:
        if not obj.ps.is_projector:continue
        p=obj.ps;issues=optics_validation.validate(p.optics_model,p.optics_lens,p.throw_ratio,p.shift_h,p.shift_v,(p.resolution_x,p.resolution_y))
        from .optics_library import PROJECTORS,LENSES
        model=PROJECTORS.get(p.optics_model);lens=LENSES.get(p.optics_lens)
        optics.append(dict(projector_uuid=p.uuid,model=p.optics_model,lens=p.optics_lens,projector_preset=asdict(model) if model else None,lens_preset=asdict(lens) if lens else None,warnings=issues))
        if lens and lens.restrictions:warnings.append(dict(code='OPTICS_ASSUMPTION',uuid=p.uuid,message=lens.restrictions))
        warnings.extend(dict(code='OPTICS',uuid=p.uuid,message=x) for x in issues)
    screens=[]
    for obj in context.scene.objects:
        if obj.beam_screen.is_screen:
            p=obj.beam_screen;screens.append(dict(uuid=p.uuid,name=p.identifier,width_m=p.width,height_m=p.height,aspect=p.width/p.height,notes=getattr(p,'notes','')))
    result=analysis_runtime.CACHE.get(context.scene.as_pointer())
    analysis=[]
    if result and not result['stale']:
        analysis=[{k:v for k,v in result.items() if k!='samples' and not k.startswith('_')}]
        stats=result['statistics']
        if stats['density_min_px_m'] is not None and stats['density_min_px_m']<THRESHOLDS['min_density_px_m']:warnings.append(dict(code='LOW_DENSITY',uuid=result['receiver_uuid'],message=f"Minimum sampled density below Beam guidance {THRESHOLDS['min_density_px_m']:g} px/m"))
        if stats['coverage_percent']<THRESHOLDS['min_coverage_percent']:warnings.append(dict(code='INCOMPLETE_COVERAGE',uuid=result['receiver_uuid'],message=f"Sampled receiver coverage below Beam guidance {THRESHOLDS['min_coverage_percent']:g}%"))
        if (stats['max_anisotropy'] or 0)>THRESHOLDS['max_anisotropy']:warnings.append(dict(code='EXCESSIVE_STRETCH',uuid=result['receiver_uuid'],message=f"Sampled pixel anisotropy exceeds Beam guidance {THRESHOLDS['max_anisotropy']:g}:1"))
    else:warnings.append(dict(code='NO_CURRENT_ANALYSIS',uuid=None,message='Surface analysis absent or stale; projector measurements are nominal only'))
    receivers=[dict(uuid=o.get('beam_receiver_uuid'),name=o.name) for o in context.scene.objects if o.get('beam_receiver_uuid') and not o.beam_screen.is_screen]
    return dict(schema='beam-study',schema_version='1.0.0',exported_at=source['exported_at'],project=source['project_metadata'],units=source['units'],
        study_guidance=dict(thresholds=THRESHOLDS,basis=BASIS),export_formats=source['export_formats'],
        projectors=source['projectors'],blend_groups=source['blend_groups'],screens=screens,receivers=receivers,views=source['study_views'],optics=optics,
        surface_analysis=analysis,warnings=warnings,assumptions=['Nominal projector measurements do not guarantee visible coverage.','Surface analysis is sampled, two-sided opaque evaluated geometry; thin occluders and between-sample regions remain untested.','Illuminance is nominal, not photometrically calibrated.'],
        transform_validation={k:source['disguise'][k] for k in ('convention_id','transform_convention','validated','mapping_matter_reference_validated')})

def validate(data):
    seen=set()
    for kind in ('projectors','blend_groups','screens','receivers','views'):
        for item in data[kind]:
            UUID(item['uuid'])
            if item['uuid'] in seen:raise ValueError('Duplicate study UUID')
            seen.add(item['uuid'])
    projectors={p['uuid'] for p in data['projectors']}
    for group in data['blend_groups']:
        members={m['projector_uuid'] for m in group['members']}
        if not members<=projectors:raise ValueError('Unresolved blend member')
        if group['anchor_projector_uuid'] not in members:raise ValueError('Unresolved blend anchor')
        if any(pair[k] not in members for pair in group['adjacent_pairs'] for k in ('a_uuid','b_uuid')):raise ValueError('Unresolved blend pair')
    for result in data['surface_analysis']:
        if result['receiver_uuid'] not in seen or not set(result['projector_uuids'])<=projectors:raise ValueError('Unresolved analysis reference')
    for optic in data['optics']:
        if optic['projector_uuid'] not in projectors:raise ValueError('Unresolved optics reference')
    for warning in data['warnings']:
        if warning.get('uuid') is not None and warning['uuid'] not in seen:raise ValueError('Unresolved warning reference')
    analyses={a.get('analysis_uuid'):a for a in data['surface_analysis'] if a.get('analysis_uuid')}
    for view in data['views']:
        image=view.get('analysis_image')
        if image:
            source=analyses.get(image['analysis_uuid'])
            if not source or image['receiver_uuid']!=source['receiver_uuid'] or image['projector_uuids']!=source['projector_uuids']:raise ValueError('Unresolved analysis image reference')
            if image['mode']!=view.get('analysis_overlay') or image['statistics']!=source['statistics']:raise ValueError('Analysis image metadata differs from its source')
        if view.get('package_image') not in (None,'views/view-'+view['uuid']+'.png'):raise ValueError('Unexpected study image path')
    json.dumps(data,allow_nan=False)


def html_sheet(data):
    esc=lambda x:html.escape(str(x))
    def number(value,digits=2):return '—' if value is None else f'{value:,.{digits}f}'
    def table(headers,rows):
        return '<table><thead><tr>'+''.join('<th>'+esc(x)+'</th>' for x in headers)+'</tr></thead><tbody>'+''.join('<tr>'+''.join('<td>'+esc(x)+'</td>' for x in row)+'</tr>' for row in rows)+'</tbody></table>'
    projector_rows=[]
    for p in data['projectors']:
        c=p['calculated'] or {};shift=p['lens_shift_percent']
        projector_rows.append((p['name'],f"{p['resolution']['x']} × {p['resolution']['y']}",number(p['throw_ratio']),number(c.get('throw_distance_m')),number(c.get('image_width_m'))+' × '+number(c.get('image_height_m')),number(c.get('pixel_density_px_per_m'),0),number(c.get('pixel_size_mm_per_px')),f"{shift['horizontal']:+.1f} / {shift['vertical']:+.1f}",number(p['total_lumens'],0),number(c.get('estimated_illuminance_lux'),0),p['notes']))
    groups=[]
    for g in data['blend_groups']:
        for pair in g['adjacent_pairs']:
            groups.append((g['name'],g['layout'],pair['a']+' / '+pair['b'],pair['axis'],number(pair['desired']['pixels'],0)+' px / '+number(pair['desired']['metres'])+' m',number(pair['actual']['pixels'],0)+' px / '+number(pair['actual']['metres'])+' m',number(pair.get('gap_m'))))
    screens=[(x['name'],number(x['width_m']),number(x['height_m']),number(x['aspect']),x['notes']) for x in data['screens']]
    analysis=[]
    for result in data['surface_analysis']:
        c=result['statistics'];analysis.append((result['receiver_name'],c['sample_count'],number(c['surface_area_m2']),number(c['coverage_percent'],1)+'%',number(c['overlap_percent'],1)+'%',number(c['density_min_px_m'],0)+' / '+number(c['density_average_px_m'],0)+' / '+number(c['density_max_px_m'],0),number(c['max_anisotropy'])+':1',number(c['occluded_sample_percent'],1)+'%'))
    images=''.join('<figure><img src="'+esc(v['package_image'])+'"><figcaption>'+esc(v['name'])+'</figcaption></figure>' for v in data['views'] if v.get('package_image'))
    warnings=''.join('<li>'+esc(w['code']+': '+w['message'])+'</li>' for w in data['warnings']) or '<li>No warnings in this export. Review the assumptions below.</li>'
    metadata=' · '.join(esc(k.replace('_',' ').title())+': '+esc(v) for k,v in data['project'].items() if v)
    return '<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Beam study</title><style>body{font:14px system-ui;margin:40px auto;padding:0 24px;max-width:1440px;color:#202830;background:#fafbf9}h1{font-size:32px}h2{margin-top:32px;color:#245e57}table{border-collapse:collapse;width:100%;font-size:12px}td,th{padding:10px 8px;border-bottom:1px solid #cdd5d0;text-align:left}th{background:#e6eee9}img{width:100%;max-height:600px;object-fit:contain}figure{margin:24px 0}figcaption{color:#52615c}li{margin:8px 0}@media print{body{margin:0}h2{break-after:avoid}tr,figure{break-inside:avoid}}</style><h1>'+esc(data['project']['project_name'] or 'Beam Study')+'</h1><p>Development beta · '+esc(data['exported_at'])+'</p><p>'+metadata+'</p>'+images+'<h2>Projector schedule</h2>'+table(['ID','Raster','Ratio','Throw m','Image W × H m','px/m','mm/px','H / V shift %','Lumens','Lux','Notes'],projector_rows)+'<p>Shift uses full-image dimensions. Measurements and illuminance are nominal centre values.</p><h2>Blend schedule</h2>'+table(['Group','Layout','Pair','Axis','Requested overlap','Actual overlap','Gap m'],groups)+'<p>Adjacent-pair overlap is measured on the group reference plane.</p><h2>Screen schedule</h2>'+table(['ID','Width m','Height m','Aspect','Notes'],screens)+'<h2>Surface analysis</h2>'+table(['Receiver','Samples','Area m²','Visible coverage','Overlap / surface','Min / avg / max px/m','Max anisotropy','Occluded samples'],analysis)+'<p>Density is conservative worst-direction density. Overlap is a percentage of total surface area.</p><h2>Warnings</h2><ul>'+warnings+'</ul><h2>Assumptions</h2><p>'+esc(' '.join(data['assumptions']))+'</p><p>Structured source: <a href="beam-study.json">beam-study.json</a>. UUIDs identify records; labels are presentation only.</p></html>'

def export(context,destination,include_views=True,area=None):
    """Write a fresh directory atomically. Refuse replacing an existing package."""
    destination=Path(destination)
    if destination.exists():raise ValueError('Choose a new package folder; existing packages are never replaced')
    destination.parent.mkdir(parents=True,exist_ok=True)
    temp=Path(tempfile.mkdtemp(prefix='.beam-study-',dir=destination.parent))
    view_state=[(v,v.image_filename,v.exported_at) for v in context.scene.ps_study.views]
    try:
        data=document(context);(temp/'views').mkdir()
        from .study_views import export_view
        for view,record in zip(context.scene.ps_study.views,data['views']):
            record['package_image']=None
            if include_views:
                name='view-'+view.uuid+'.png';record['analysis_image']=export_view(context,view,temp/'views'/name,area)
                record['package_image']='views/'+name
                record['exported_image_filename']=name;record['exported_at']=view.exported_at
            else:data['warnings'].append(dict(code='VIEW_NOT_RENDERED',uuid=view.uuid,message='View metadata only; image export disabled'))
        validate(data)
        (temp/'beam-study.json').write_text(json.dumps(data,indent=2,allow_nan=False)+'\n')
        (temp/'index.html').write_text(html_sheet(data));os.rename(temp,destination)
        return data
    except Exception:
        for view,name,date in view_state:view.image_filename=name;view.exported_at=date
        shutil.rmtree(temp);raise
