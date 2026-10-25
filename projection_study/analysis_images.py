"""Saved-view analysis drawing and explicit, hash-linked PATCH assumptions."""
import hashlib,json
from pathlib import Path
from . import analysis_runtime

def current(context,mode):
    if mode=='NONE':return None
    result=analysis_runtime.CACHE.get(context.scene.as_pointer())
    if not result or result['stale']:raise ValueError('Surface Analysis is absent or stale. Analyse again before exporting.')
    if mode not in result.get('_batches',{}):raise ValueError('Analysis image export requires a GPU viewport analysis')
    return result

def metadata(result,mode):
    return dict(analysis_uuid=result['analysis_uuid'],mode=mode,generated_at=result['generated_at'],
        receiver_uuid=result['receiver_uuid'],receiver_name=result['receiver_name'],projector_uuids=result['projector_uuids'],
        statistics=result['statistics'],method=result['method'],visibility=result['visibility'],untested=result['untested'],
        metric_selection='Best visible projector by conservative worst-direction density at each sample',
        colour_scale='Sample minimum to maximum density' if mode=='DENSITY' else 'Anisotropy 1:1 to 3:1; colours saturate above 3:1')

def write_metadata(path,result,mode):
    path=Path(path);data=metadata(result,mode)
    data.update(image_filename=path.name,image_sha256=hashlib.sha256(path.read_bytes()).hexdigest())
    path.with_suffix('.analysis.json').write_text(json.dumps(data,indent=2,allow_nan=False)+'\n')
    return data

def legend(result,mode,width,height):
    import gpu,blf
    from . import typography
    stats=result['statistics'];density=mode=='DENSITY'
    keys=('density_min_px_m','density_average_px_m','density_max_px_m') if density else ('min_anisotropy','average_anisotropy','max_anisotropy')
    values=['—' if stats[k] is None else f'{stats[k]:.1f}' for k in keys]
    lines=[('Density · px/m · local auto scale' if density else 'Stretch · anisotropy :1'),
        'Min / avg / max   '+' / '.join(values),
        f"Coverage {stats['coverage_percent']:.1f}%   ·   Overlap {stats['overlap_percent']:.1f}%",
        f"{stats['sample_count']:,} samples · visible first-hit"]
    f=typography.font();size=max(9,min(16,width/75));blf.size(f,size)
    box=min(width-16,max(blf.dimensions(f,line)[0] for line in lines)+28)
    gpu.state.depth_test_set('NONE');gpu.state.blend_set('ALPHA')
    typography.rectangle(8,8,box,size*6.6,(.025,.035,.04,.92))
    for i,line in enumerate(lines):
        blf.color(f,.9,.94,.94,1);blf.position(f,20,8+size*(5.1-i*1.25),0);blf.draw(f,line)
    start=(.12,.24,.36) if density else (.22,.55,.52);end=(.55,.80,.72) if density else (.76,.42,.22)
    for i in range(48):
        t=i/47;typography.rectangle(20+i*(box-24)/48,14,(box-24)/48+1,4,tuple(a+(b-a)*t for a,b in zip(start,end))+(1,))
    gpu.state.blend_set('NONE')
