"""Live nominal screen-plane coverage for Auto Blend groups; no ray casting here."""
import math
from mathutils import Vector,Matrix
from . import runtime,screen_objects
from .projection_math import image_point
from .blend_math import intersection,adjacent,overlap_values

_cache={}


def report(group,context):
    screen=group.layout_screen
    if not screen or screen.name not in context.scene.objects:return None
    objects=[m.projector for m in group.members]
    unit=context.scene.unit_settings.scale_length
    key=(unit,screen.as_pointer(),tuple(v for row in screen.matrix_world for v in row),tuple(screen.dimensions),screen.beam_screen.built_signature,screen_objects.signature(screen.beam_screen),
         tuple((o.as_pointer(),tuple(v for row in o.matrix_world for v in row),o.ps.throw_ratio,o.ps.resolution_x,o.ps.resolution_y,o.ps.shift_h,o.ps.shift_v) if o else None for o in objects),group.overlap_h,group.overlap_v,group.input_mode,group.columns,group.layout)
    if _cache.get(group.uuid,(None,))[0]==key:return _cache[group.uuid][1]
    if len(_cache)>64:_cache.clear()
    from .auto_layout import screen_frame
    try:width,height,centre,screen_rotation=screen_frame(context,screen)
    except ValueError:return dict(pairs=[],coverage=0,status='Screen changed: update or restore a flat screen')
    rotation=screen_rotation@Matrix.Rotation(math.pi/2,3,'X');inverse=rotation.transposed()
    polygons=[]
    for obj in objects:
        polygon=[]
        if obj:
            origin,r=runtime.frame(obj);eye=inverse@(origin-centre);p=obj.ps
            for u,v in ((0,0),(1,0),(1,1),(0,1)):
                ray=inverse@r@Vector(image_point(u,v,1,p.throw_ratio,p.resolution_x,p.resolution_y,p.shift_h,p.shift_v))
                if abs(ray.z)<1e-8 or -eye.z/ray.z<=0:polygon=[];break
                point=eye+ray*(-eye.z/ray.z);polygon.append((point.x*unit,point.y*unit))
        polygons.append(polygon)
    index=next((i for i,o in enumerate(objects) if o and o.ps.uuid==group.anchor_uuid),0)
    anchor=objects[index] if objects else None;anchor_poly=polygons[index] if polygons else []
    result=[]
    if anchor and anchor_poly:
        for a,b,axis in adjacent(group.layout,len(objects),group.columns):
            if not objects[a] or not objects[b] or not polygons[a] or not polygons[b]:continue
            dim=0 if axis=='H' else 1;pixels=anchor.ps.resolution_x if dim==0 else anchor.ps.resolution_y
            full=max(v[dim] for v in anchor_poly)-min(v[dim] for v in anchor_poly)
            if full<=1e-8:continue
            poly=intersection(polygons[a],polygons[b])
            length=max((v[dim] for v in poly),default=0)-min((v[dim] for v in poly),default=0)
            gap=max(0,max(min(v[dim] for v in polygons[a]),min(v[dim] for v in polygons[b]))-min(max(v[dim] for v in polygons[a]),max(v[dim] for v in polygons[b])))
            desired=overlap_values(group.overlap_h if dim==0 else group.overlap_v,group.input_mode,pixels,full)
            result.append(dict(a=objects[a].ps.identifier,b=objects[b].ps.identifier,a_uuid=objects[a].ps.uuid,b_uuid=objects[b].ps.uuid,axis=axis,
                reference_status='target',actual_plane_distance_m=abs((inverse@(anchor.matrix_world.translation-centre)).z)*unit,
                desired=desired,actual=dict(metres=length,pixels=length/full*pixels,percent=length/full*100),gap_m=gap,
                polygon=[centre+rotation@Vector((x/unit,y/unit,0)) for x,y in poly]))
    rect=[(-width/2,-height/2),(width/2,-height/2),(width/2,height/2),(-width/2,height/2)]
    clipped=[intersection(p,rect) for p in polygons if p]
    from .coverage_math import union_area
    coverage=min(100,union_area(clipped)/(width*height)*100)
    result=dict(pairs=result,coverage=coverage,status='Valid nominal coverage' if coverage>=99.99 else 'Coverage incomplete',centre=centre,rotation=rotation,anchor_width=max((p[0] for p in anchor_poly),default=0)-min((p[0] for p in anchor_poly),default=0),anchor_height=max((p[1] for p in anchor_poly),default=0)-min((p[1] for p in anchor_poly),default=0),distance=abs((inverse@(anchor.matrix_world.translation-centre)).z)*unit if anchor else 0)
    _cache[group.uuid]=(key,result);return result
