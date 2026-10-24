"""Pure limits validation; manual values are never silently clamped."""
from .optics_library import PROJECTORS,LENSES

def validate(model_id,lens_id,ratio,h,v,resolution):
    if model_id=='MANUAL' and lens_id=='MANUAL':return []
    model=PROJECTORS.get(model_id)
    if not model:return ['Unknown projector preset']
    errors=[]
    if tuple(resolution)!=model.resolution:errors.append('Resolution differs from native preset')
    if lens_id=='MANUAL':return errors
    if lens_id not in model.lenses:return errors+['Lens is incompatible with projector']
    lens=LENSES[lens_id]
    if not lens.throw_min-1e-6<=ratio<=lens.throw_max+1e-6:errors.append(f'Outside lens range: throw {ratio:.2f}; lens {lens.throw_min:.2f}–{lens.throw_max:.2f}')
    for label,value,limits in [('H',h,lens.h_limits),('V',v,lens.v_limits)]:
        if limits is None:
            if abs(value)>1e-6:errors.append(label+' Shift convention unverified for this lens')
        elif not limits[0]<=value<=limits[1]:errors.append(label+' Shift exceeds lens limit')
    return errors

def require(p,ratio=None):
    problems=validate(p.optics_model,p.optics_lens,p.throw_ratio if ratio is None else ratio,p.shift_h,p.shift_v,(p.resolution_x,p.resolution_y))
    if problems:raise ValueError('Requested image cannot be achieved: '+'; '.join(problems))
