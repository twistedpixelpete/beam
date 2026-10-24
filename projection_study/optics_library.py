"""Small, versioned guidance library, independent of runtime projector state."""
from dataclasses import dataclass

@dataclass(frozen=True)
class Lens:
    id: str
    model: str
    throw_min: float
    throw_max: float
    h_limits: tuple | None
    v_limits: tuple | None
    restrictions: str=''
    source: str=''

@dataclass(frozen=True)
class Projector:
    id: str
    manufacturer: str
    model: str
    resolution: tuple
    lumens: float
    lenses: tuple
    source: str

SOURCE='https://www.christiedigital.com/globalassets/resources/public/4k7-4k10-hs-datasheet.pdf'
LENSES={
 'christie_085':Lens('christie_085','0.85–1.02:1 zoom',.85,1.02,None,None,
     'Nominal throw guidance only. Published offsets ±59% H / ±140% V have not been normalised to Beam full-image units; shifted solves are blocked. Coupled shift envelope and distance corrections unverified.',SOURCE),
 'synthetic_120':Lens('synthetic_120','TEST ONLY · 1.20–1.60',1.2,1.6,(-25,25),(-55,55),'Synthetic rectangular independent shift envelope; not a real lens','Beam synthetic test fixture')}
PROJECTORS={
 'christie_4k10':Projector('christie_4k10','Christie','4K10-HS (native raster)',(2716,1528),10000,('christie_085',),SOURCE),
 'synthetic':Projector('synthetic','Test fixture','Synthetic 1080p',(1920,1080),10000,('synthetic_120',),'Beam synthetic test fixture')}

def projector_items():return [('MANUAL','Generic / Manual','No manufacturer constraints')]+[(k,p.manufacturer+' · '+p.model,p.source) for k,p in PROJECTORS.items()]
def lens_items(self,context):
    model=PROJECTORS.get(self.optics_model)
    return [('MANUAL','Generic / Manual','No lens constraints')]+[(k,LENSES[k].model,LENSES[k].restrictions) for k in model.lenses] if model else [('MANUAL','Generic / Manual','No lens constraints')]
