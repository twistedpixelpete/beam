"""Loop UV mapping and bounded, explicit diagnostics for display meshes."""
from collections import defaultdict,deque
from math import isfinite,sqrt
from .blend_math import intersection


def projected(mesh,plane):
    axes={'XZ':(0,2),'XY':(0,1),'YZ':(1,2)}[plane]
    low=[min(v.co[i] for v in mesh.vertices) for i in axes]
    span=[max(v.co[i] for v in mesh.vertices)-lo for i,lo in zip(axes,low)]
    if min(span)<1e-9: raise ValueError('Selected UV plane has zero extent; choose a different plane')
    return [[tuple((mesh.vertices[mesh.loops[k].vertex_index].co[a]-l)/s for a,l,s in zip(axes,low,span)) for k in f.loop_indices] for f in mesh.polygons]


def distance_grid(mesh):
    """Infer a rectangular quad lattice, then integrate physical edge lengths.

    This is row/column distance mapping, not a general isometric flattening.
    Reject holes, branching, closed seams and non-quads rather than invent UVs.
    """
    if not mesh.polygons or any(len(f.vertices)!=4 for f in mesh.polygons):
        raise ValueError('Surface Distance requires a connected rectangular quad grid; use Existing or Projected UV for this topology')
    edges=defaultdict(list)
    faces=[tuple(f.vertices) for f in mesh.polygons]
    for i,face in enumerate(faces):
        for a,b in zip(face,face[1:]+face[:1]):edges[tuple(sorted((a,b)))].append(i)
    if any(len(v)>2 for v in edges.values()):raise ValueError('Surface grid is non-manifold')
    coords=dict(zip(faces[0],[(0,0),(1,0),(1,1),(0,1)])); visited={0};queue=deque([0])
    while queue:
        i=queue.popleft();f=faces[i]
        for a,b in zip(f,f[1:]+f[:1]):
            for j in edges[tuple(sorted((a,b)))]:
                if j==i:continue
                # Adjacent CCW quad traverses shared edge in the opposite direction.
                g=faces[j];k=next((k for k in range(4) if g[k]==b and g[(k+1)%4]==a),None)
                if k is None:raise ValueError('Surface grid has inconsistent normals; repair winding first')
                ax,ay=coords[a];bx,by=coords[b];dx,dy=bx-ax,by-ay
                proposed={b:(bx,by),a:(ax,ay),g[(k+2)%4]:(ax+dy,ay-dx),g[(k+3)%4]:(bx+dy,by-dx)}
                if any(v in coords and coords[v]!=c for v,c in proposed.items()):raise ValueError('Closed or ambiguous surface grid; use Existing UV with an explicit seam')
                coords.update(proposed)
                if j not in visited:visited.add(j);queue.append(j)
    if len(visited)!=len(faces) or len(coords)!=len(mesh.vertices):raise ValueError('Surface grid must be a single connected patch without loose vertices')
    xmin=min(x for x,y in coords.values());ymin=min(y for x,y in coords.values())
    grid={(x-xmin,y-ymin):v for v,(x,y) in coords.items()};nx=max(x for x,y in grid);ny=max(y for x,y in grid)
    if len(grid)!=(nx+1)*(ny+1) or len(faces)!=nx*ny:raise ValueError('Surface grid has holes or folded topology')
    values={v:[0.,0.] for v in coords}
    for axis,count,other in [(0,nx,ny),(1,ny,nx)]:
        for j in range(other+1):
            row=[grid[(i,j) if axis==0 else (j,i)] for i in range(count+1)];distance=[0.]
            for a,b in zip(row,row[1:]):distance.append(distance[-1]+(mesh.vertices[a].co-mesh.vertices[b].co).length)
            if distance[-1]<1e-9:raise ValueError('Surface grid contains a zero-length row')
            for v,d in zip(row,distance):values[v][axis]=d/distance[-1]
    return [[tuple(values[v]) for v in f] for f in faces]


def assign(mesh,values):
    layer=mesh.uv_layers.active or mesh.uv_layers.new(name='Beam UV')
    for face,uvs in zip(mesh.polygons,values):
        for k,uv in zip(face.loop_indices,uvs):layer.data[k].uv=uv


def diagnose(mesh,unit=1.,rx=1920,ry=1080,reverse=False):
    errors=[];warnings=[]
    if not mesh.vertices or not mesh.polygons:return dict(errors=['No display faces'],warnings=[],summary='No display faces')
    if any(not isfinite(c) for v in mesh.vertices for c in v.co):errors.append('Non-finite geometry')
    edges=defaultdict(int);seen=set();duplicates=0
    for f in mesh.polygons:
        key=tuple(sorted(tuple(round(c,7) for c in mesh.vertices[v].co) for v in f.vertices))
        if key in seen:duplicates+=1
        seen.add(key)
        for k in f.edge_keys:edges[k]+=1
    if duplicates:errors.append(f'{duplicates} duplicate faces')
    if any(n>2 for n in edges.values()):errors.append('Non-manifold edges with more than two faces')
    if any(f.area<1e-12 for f in mesh.polygons):errors.append('Zero-area geometric faces')
    layer=mesh.uv_layers.active
    if not layer:return dict(errors=errors+['Missing UV map'],warnings=warnings,summary='Missing UV map')
    coords=[tuple(d.uv) for d in layer.data]
    if any(not isfinite(v) for p in coords for v in p):errors.append('Non-finite UV coordinates')
    if any(v < -1e-5 or v > 1+1e-5 for p in coords for v in p):errors.append('UV coordinates outside 0–1')
    mesh.calc_loop_triangles();triangles=[];zero=flipped=0;densities=[]
    for tri in mesh.loop_triangles:
        uv=[coords[k] for k in tri.loops];a,b,c=uv
        area=((b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0]))/2
        if abs(area)<1e-12:zero+=1
        elif (area<0)!=reverse:flipped+=1
        if tri.area>1e-12:densities.append(sqrt(abs(area)*rx*ry/(tri.area*unit*unit)))
        triangles.append((min(p[0] for p in uv),max(p[0] for p in uv),min(p[1] for p in uv),max(p[1] for p in uv),uv))
    if zero:errors.append(f'{zero} zero-area UV triangles')
    if flipped:errors.append(f'{flipped} reversed UV triangles / inconsistent front direction')
    # Sweep broad phase; exact convex intersection excludes touching boundaries.
    active=[];overlaps=checks=0;limited=False
    for t in sorted(triangles,key=lambda t:t[0]):
        active=[a for a in active if a[1]>t[0]+1e-9]
        for a in active:
            if a[3]<=t[2]+1e-9 or t[3]<=a[2]+1e-9:continue
            checks+=1
            if checks>2000000:limited=True;break
            poly=intersection(a[4],t[4]);area=abs(sum(x[0]*y[1]-y[0]*x[1] for x,y in zip(poly,poly[1:]+poly[:1])))/2 if poly else 0
            if area>1e-9:overlaps+=1
        if limited:break
        active.append(t)
    if overlaps:errors.append(f'{overlaps} overlapping UV triangle pairs')
    if limited:errors.append('Overlap validation budget exceeded; simplify or split the display mesh')
    ratio=max(densities)/min(densities) if densities and min(densities)>0 else 0
    if ratio>1.2:warnings.append(f'Texel density varies by {ratio:.2f}× across the surface')
    return dict(errors=errors,warnings=warnings,texel_density_min=min(densities,default=0),texel_density_max=max(densities,default=0),
                summary='; '.join(errors+warnings) or 'UVs valid · consistent winding · no overlaps')
