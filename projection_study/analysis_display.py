"""Shared numeric ranges, restrained palettes and mode-specific readouts."""
MODES=[('DENSITY','Density','Conservative worst-direction pixels per metre'),('STRETCH','Stretch','Principal pixel anisotropy'),('ILLUMINANCE','Illuminance','Estimated incident lux; visible sources add'),('DISTANCE','Distance','Nearest visible lens-to-surface distance'),('ACUITY','Acuity','Angular pixel size from the active Observer')]
PALETTES={'DENSITY':((.12,.24,.36),(.55,.80,.72)),'STRETCH':((.22,.55,.52),(.76,.42,.22)),
 'ILLUMINANCE':((.12,.16,.25),(.92,.76,.38)),'DISTANCE':((.14,.26,.40),(.69,.81,.88)),
 'ACUITY':((.18,.40,.44),(.84,.62,.37))}
KEYS={'DENSITY':('density_min_px_m','density_average_px_m','density_max_px_m'),
 'STRETCH':('min_anisotropy','average_anisotropy','max_anisotropy'),
 'ILLUMINANCE':('illuminance_min_lux','illuminance_average_lux','illuminance_max_lux'),
 'DISTANCE':('distance_min_m','distance_average_m','distance_max_m'),
 'ACUITY':('acuity_min_arcmin','acuity_average_arcmin','acuity_max_arcmin')}


def value(sample,mode):
    if mode=='ILLUMINANCE':return sample['illuminance_lux']
    if mode=='DISTANCE':return sample['distance_m']
    if mode=='ACUITY':return sample.get('angular_pixel_arcmin')
    best=max(sample['visible'],key=lambda v:v['density_px_m'],default=None)
    return best['density_px_m' if mode=='DENSITY' else 'anisotropy'] if best else None


def scale(result,mode):
    if mode=='STRETCH':return (1,3)
    if mode=='ACUITY':
        t=result['observer']['threshold_arcmin'];return (.5*t,1.5*t)
    display=result.get('display',{})
    if mode=='ILLUMINANCE' and display.get('illuminance_scale')=='FIXED':return (0,display['illuminance_max_lux'])
    stats=result['statistics'];keys=KEYS[mode]
    return (stats.get(keys[0]) or 0,stats.get(keys[2]) or 0)


def colour(result,mode,sample):
    v=value(sample,mode)
    if v is None:return (.20,.20,.23,1)
    if mode=='ILLUMINANCE' and v==0:return PALETTES[mode][0]+(1,)
    low,high=scale(result,mode)
    t=min(1,max(0,(v-low)/(high-low))) if high-low>max(1e-5,high*1e-6) else .5
    start,end=PALETTES[mode]
    return tuple(a+(b-a)*t for a,b in zip(start,end))+(1,)


def lines(result,mode,units='m'):
    s=result['statistics'];factor=1000 if mode=='DISTANCE' and units=='mm' else 1
    title={'DENSITY':'Density · px/m · local auto scale','STRETCH':'Stretch · anisotropy :1','ILLUMINANCE':'Estimated Illuminance · lux','DISTANCE':'Projection Distance · '+units,'ACUITY':'Angular Pixel Size · arcmin'}[mode]
    values=['—' if s.get(k) is None else f'{s[k]*factor:.2f}' for k in KEYS[mode]]
    output=[title,'Min / avg / max   '+' / '.join(values)]
    if mode=='ILLUMINANCE':
        u=s['illuminance_uniformity_min_average'];output.append('Uniformity min / average: '+('—' if u is None else f'{u:.3f}'))
        lo,hi=scale(result,mode);output.append(f"Scale {lo:.1f}–{hi:.1f} lux · "+result.get('display',{}).get('illuminance_scale','AUTO').lower())
        target=result.get('display',{}).get('target_illuminance_lux')
        if target:output.append(f'Target reference: {target:g} lux (display only)')
        output.append('Uniform raster flux · visible sources add')
    elif mode=='DISTANCE':
        d=s['distance_variation_m'];output.append('Variation: '+('—' if d is None else f'{d*factor:.2f} {units}'))
        output.append('Nearest visible projector · not focus compliance')
    elif mode=='ACUITY':
        t=result['observer']['threshold_arcmin'];below=s['acuity_below_threshold_percent'];above=s['acuity_at_or_above_threshold_percent']
        output.append(f'Threshold {t:g} arcmin · '+result['observer']['name'])
        output.append('Below / at-or-above: '+('—' if below is None else f'{below:.1f}% / {above:.1f}%'))
        output.append('Coarsest apparent pixel · viewer visibility tested')
    else:output.append(f"Coverage {s['coverage_percent']:.1f}% · overlap {s['overlap_percent']:.1f}%")
    output.append(f"{s['sample_count']:,} samples · opaque first-hit")
    return output
