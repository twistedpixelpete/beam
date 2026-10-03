"""Stable, versioned file conventions independent of Blender."""
import re
import struct
import zlib
from pathlib import Path
from datetime import datetime, timezone

SCHEMA_VERSION='1.0'

def timestamp():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')

def image_filename(name, identity):
    slug=re.sub(r'[^a-z0-9]+','-',name.casefold()).strip('-')[:64] or 'study-view'
    return f'{slug}--{identity[:8]}.png'

def write_png(path, width, height, rgba_bottom_up):
    """Encode display-referred RGBA8 pixels without a second colour transform."""
    pixels=bytes(rgba_bottom_up)
    stride=width*4
    if len(pixels)!=stride*height: raise ValueError('Incorrect RGBA buffer size')
    def chunk(tag,data):
        return struct.pack('!I',len(data))+tag+data+struct.pack('!I',zlib.crc32(tag+data)&0xffffffff)
    rows=b''.join(b'\0'+pixels[y*stride:(y+1)*stride] for y in range(height-1,-1,-1))
    data=b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('!2I5B',width,height,8,6,0,0,0))
    data+=chunk(b'sRGB',b'\0')+chunk(b'IDAT',zlib.compress(rows,6))+chunk(b'IEND',b'')
    Path(path).write_bytes(data)


def beam_filename(project,revision,view):
    def clean(value):
        return re.sub(r'_+','_',re.sub(r'[^\w-]+','_',value.strip(),flags=re.UNICODE)).strip('_-.')[:80]
    pieces=[clean(project) or 'Beam',clean(revision),clean(view) or 'Current_View']
    return '_'.join(p for p in pieces if p)+'.png'
