"""Explicit area-stratified CPU analysis against evaluated scene geometry."""
import math,time
import bpy
from mathutils import Vector
from . import runtime,scene_geometry,target_raycast,surface_analysis
CACHE={}

def invalidate():
    for result in CACHE.values():result['stale']=True

def analyse(context,receiver,projectors,budget=2048):
    if not isinstance(budget,int) or not 1<=budget<=100000:raise ValueError('Sample budget must be an integer from 1 to 100000')
    started=time.perf_counter();context.view_layer.update();runtime.refresh(True);target_raycast.prepare()
    surface=scene_geometry.SURFACES.get(receiver.as_pointer())
    if not surface:raise ValueError('Choose a visible receiver surface')
    if not projectors:raise ValueError('Choose at least one projector')
    if any(not runtime.rigid(o) for o in projectors):raise ValueError('Restore projector transforms before analysis')
    unit=context.scene.unit_settings.scale_length
    triangles=[]
    for ids in surface.triangles:
        a,b,c=(surface.vertices[i] for i in ids);cross=(b-a).cross(c-a);area=cross.length*.5*unit*unit
        if area>1e-14:triangles.append((a,b,c,cross.normalized(),area))
    total=sum(t[4] for t in triangles)
    if not total:raise ValueError('Receiver has no analysable area')
    # Equal-area systematic strata across the cumulative triangle-area distribution.
    samples=[];j=0;cumulative=triangles[0][4]
    for k in range(budget):
        position=(k+.5)*total/budget
        while position>cumulative and j<len(triangles)-1:j+=1;cumulative+=triangles[j][4]
        a,b,c,n,area=triangles[j]
        f=math.sqrt((k*.7548776662466927+.5)%1);g=(k*.5698402909980532+.5)%1
        point=(1-f)*a+f*(1-g)*b+f*g*c
        facing=1 if n.dot(runtime.CACHE[projectors[0].as_pointer()]['origin']-point)>=0 else -1
        sample=dict(area_m2=total/budget,point=list(point+n*(facing*.001/unit)),nominal=[],visible=[])
        for obj in projectors:
            r=runtime.CACHE[obj.as_pointer()];p=obj.ps;inv=r['rotation'].transposed()
            local=inv@(point-r['origin'])*unit;normal=inv@n
            metrics=surface_analysis.local_metrics(local,normal,p.throw_ratio,p.resolution_x,p.resolution_y,p.shift_h,p.shift_v,r['metrics'].pixels_per_metre if r['hit'] else None)
            if not metrics:continue
            metrics['projector_uuid']=p.uuid;sample['nominal'].append(metrics)
            delta=point-r['origin'];hit=target_raycast.cast(r['origin'],delta.normalized())
            if hit and (hit[0]-point).length*unit<=max(1e-5,delta.length*unit*1e-6):sample['visible'].append(metrics)
        samples.append(sample)
    result=dict(schema='beam-surface-analysis',version=1,receiver_uuid=receiver.beam_screen.uuid if receiver.beam_screen.is_screen else receiver.get('beam_receiver_uuid'),receiver_name=receiver.name,
        projector_uuids=[o.ps.uuid for o in projectors],projector_names=[o.ps.identifier for o in projectors],nominal_centre_density_px_m={o.ps.uuid:runtime.CACHE[o.as_pointer()]['metrics'].pixels_per_metre if runtime.CACHE[o.as_pointer()]['hit'] else None for o in projectors},
        statistics=surface_analysis.summarise(samples),samples=samples,stale=False,
        method='Equal-area systematic triangle strata, deterministic barycentric samples; area-weighted estimates',
        visibility='CPU evaluated-geometry first hit, opaque two-sided surfaces; not GPU depth; transparent materials treated opaque',
        untested='Between-sample regions and invisible/excluded scene geometry; thin features may be missed',elapsed_seconds=time.perf_counter()-started)
    if not bpy.app.background:
        import gpu
        from gpu_extras.batch import batch_for_shader
        interface=gpu.types.GPUStageInterfaceInfo('beam_analysis_colour');interface.smooth('VEC4','vColour')
        info=gpu.types.GPUShaderCreateInfo();info.push_constant('MAT4','viewProjection');info.vertex_in(0,'VEC3','pos');info.vertex_in(1,'VEC4','color');info.vertex_out(interface);info.fragment_out(0,'VEC4','fragColor')
        info.vertex_source('void main(){gl_Position=viewProjection*vec4(pos,1.0);gl_PointSize=7.0;vColour=color;}')
        info.fragment_source('void main(){fragColor=vColour;}')
        shader=gpu.shader.create_from_info(info);batches={}
        for mode in ('DENSITY','STRETCH'):
            points=[];colours=[]
            values=[max(s['visible'],key=lambda m:m['density_px_m'])['density_px_m'] for s in samples if s['visible']]
            low=min(values,default=0);high=max(values,default=1)
            for sample in samples:
                points.append(sample['point'])
                if not sample['visible']:colours.append((.20,.20,.23,1));continue
                m=max(sample['visible'],key=lambda m:m['density_px_m'])
                t=((m['density_px_m']-low)/(high-low) if high-low>max(1e-5,high*1e-6) else .5) if mode=='DENSITY' else min(1,(m['anisotropy']-1)/2)
                start=(.12,.24,.36) if mode=='DENSITY' else (.22,.55,.52)
                end=(.55,.80,.72) if mode=='DENSITY' else (.76,.42,.22)
                colours.append(tuple(a+(b-a)*t for a,b in zip(start,end))+(1,))
            batches[mode]=(shader,batch_for_shader(shader,'POINTS',{'pos':points,'color':colours}))
        result['_batches']=batches
    CACHE[context.scene.as_pointer()]=result
    return result
