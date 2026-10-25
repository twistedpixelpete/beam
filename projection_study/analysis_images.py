"""Saved-view analysis drawing and explicit, hash-linked PATCH assumptions."""
import hashlib,json
from pathlib import Path
from . import analysis_runtime

def current(context,mode):
    if mode=='NONE':return None
    result=analysis_runtime.CACHE.get(context.scene.as_pointer())
    if not result or analysis_runtime.stale(result,mode):raise ValueError('Surface Analysis is absent or stale. Analyse again before exporting.')
    if mode not in result.get('_batches',{}):raise ValueError('Analysis image export requires a GPU viewport analysis')
    return result

def metadata(result,mode):
    from .analysis_display import scale
    statistics=dict(result['statistics'])
    for stale_mode in result.get('_stale_modes',set()):
        prefixes={'ILLUMINANCE':('illuminance_',),'ACUITY':('acuity_',)}.get(stale_mode,())
        statistics={k:v for k,v in statistics.items() if not k.startswith(prefixes)}
    rule={'DENSITY':'Best visible projector by conservative worst-direction density at each sample',
        'STRETCH':'Best visible projector by conservative worst-direction density at each sample',
        'ILLUMINANCE':'Sum of visible source illuminance; unlit samples included as zero',
        'DISTANCE':result.get('distance_rule','Nearest visible projector'),
        'ACUITY':(result.get('observer') or {}).get('source_rule','Observer required')}[mode]
    return dict(analysis_uuid=result['analysis_uuid'],mode=mode,analysis_type=mode.lower(),generated_at=result['generated_at'],
        receiver_uuid=result['receiver_uuid'],receiver_name=result['receiver_name'],projector_uuids=result['projector_uuids'],
        statistics=statistics,method=result['method'],visibility=result['visibility'],untested=result['untested'],
        metric_selection=rule,colour_scale=('Sample minimum to maximum density' if mode=='DENSITY' else 'Anisotropy 1:1 to 3:1; colours saturate above 3:1' if mode=='STRETCH' else 'See scale_range and display'),
        scale_range=scale(result,mode),display=result.get('display',{}),
        assumptions=result.get('assumptions',[]),observer=result.get('observer') if mode=='ACUITY' else None)

def write_metadata(path,result,mode):
    path=Path(path);data=metadata(result,mode)
    data.update(image_filename=path.name,image_sha256=hashlib.sha256(path.read_bytes()).hexdigest())
    path.with_suffix('.analysis.json').write_text(json.dumps(data,indent=2,allow_nan=False)+'\n')
    return data

def legend(result,mode,width,height):
    import gpu,blf
    from . import typography
    from .analysis_display import lines as readouts,PALETTES
    lines=readouts(result,mode,result.get('display',{}).get('display_units','m'))
    f=typography.font();size=max(9,min(16,width/75));blf.size(f,size)
    box=min(width-16,max(blf.dimensions(f,line)[0] for line in lines)+28)
    gpu.state.depth_test_set('NONE');gpu.state.blend_set('ALPHA')
    typography.rectangle(8,8,box,size*(len(lines)*1.25+1.6),(.025,.035,.04,.92))
    for i,line in enumerate(lines):
        blf.color(f,.9,.94,.94,1);blf.position(f,20,8+size*((len(lines)-i)*1.25+.1),0);blf.draw(f,line)
    start,end=PALETTES[mode]
    for i in range(48):
        t=i/47;typography.rectangle(20+i*(box-24)/48,14,(box-24)/48+1,4,tuple(a+(b-a)*t for a,b in zip(start,end))+(1,))
    gpu.state.blend_set('NONE')
