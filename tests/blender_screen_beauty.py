"""Screen-only visual regression and engineering invariance checks (background safe)."""
import bpy,sys,json
from pathlib import Path
from mathutils import Matrix
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import projection_study as addon
from projection_study import screen_objects,screen_patterns,screen_display,typography

def run():
    addon.register()
    scene=bpy.context.scene
    obj=screen_objects.create(bpy.context,scene.beam_screen_draft)
    p=obj.beam_screen
    before=(p.uuid,p.identifier,p.built_signature,p.metrics,tuple(tuple(v.co) for v in obj.data.vertices),tuple(tuple(v.uv) for v in obj.data.uv_layers.active.data),obj.matrix_world.copy())
    image=screen_patterns.apply(obj)
    pixels=np.array(image.pixels[:]).reshape(image.size[1],image.size[0],4)
    assert np.isfinite(pixels).all() and np.all(pixels[:,:,3]==1)
    # Antialiased real-font edges, including digits and multiplication glyph.
    layer=screen_patterns.text_layer(400,100,[('SCR001 × 1080',20,20,36,(.9,.92,.94,1),'LEFT')])
    assert np.count_nonzero((layer[:,:,3]>0)&(layer[:,:,3]<1))>100
    # Exercise the Blender 4.5 file-backed buffer read as well as 5.2 memory view.
    screen_patterns.hasattr=lambda owner,name:False
    try:fallback=screen_patterns.text_layer(400,100,[('SCR001 × 1080',20,20,36,(.9,.92,.94,1),'LEFT')])
    finally:del screen_patterns.hasattr
    assert np.max(np.abs(layer-fallback))<.01
    second=screen_patterns.apply(obj);assert second==image
    after=(p.uuid,p.identifier,p.built_signature,p.metrics,tuple(tuple(v.co) for v in obj.data.vertices),tuple(tuple(v.uv) for v in obj.data.uv_layers.active.data),obj.matrix_world.copy())
    assert before==after,'Visual update changed engineering state'
    screen_objects.select(bpy.context,obj)
    labels=[];notes=[];old_label=typography.label;old_note=typography.annotation
    typography.label=lambda text,*args,**kwargs:labels.append(text)
    typography.annotation=lambda text,*args,**kwargs:notes.append(text)
    try:
        for detail,expected in [('OFF',0),('MINIMAL',2),('FULL',3)]:
            labels.clear();notes.clear();scene.ps_study.label_detail=detail
            screen_display.labels(Matrix.Identity(4),1200,800,{})
            assert len(notes)==expected,(detail,notes)
            assert labels and labels[0].startswith(p.identifier)
        p.show_label=False;scene.ps_study.label_detail='MINIMAL';labels.clear();notes.clear()
        screen_display.labels(Matrix.Identity(4),1200,800,{})
        assert not labels and len(notes)==2,'Dimension visibility must be independent of ID'
        scene.ps_study.display_units='mm';notes.clear();screen_display.labels(Matrix.Identity(4),1200,800,{})
        assert all('mm' in n for n in notes)
        scene.ps_study.display_units='m';notes.clear();screen_display.labels(Matrix.Identity(4),1200,800,{})
        assert all(n.endswith(' m') for n in notes)
    finally:typography.label=old_label;typography.annotation=old_note
    print('PASS: clean typography, 4.5 buffer fallback, packed image reuse, unchanged geometry/UV/identity, label detail, independent dimensions, m/mm',flush=True)

if __name__=='__main__':run()
