"""Blender-owned UV test images, shared by raster size; creation outside drawing."""
import bpy


def ensure_uv_grid(rx,ry,kind='UV_GRID'):
    # Bound preview memory for unusually large custom rasters, preserving aspect.
    scale=min(1,4096/max(rx,ry))
    width=max(1,round(rx*scale)); height=max(1,round(ry*scale))
    name=f'.Beam {kind} {rx}x{ry}'
    image=bpy.data.images.get(name)
    if image is None or not image.get('ps_generated_uv'):
        image=bpy.data.images.new(name,width=width,height=height)
        image.generated_type=kind
        image['ps_generated_uv']=True
    return image
