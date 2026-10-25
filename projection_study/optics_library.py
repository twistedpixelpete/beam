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
    source_revision: str=''
    checked_on: str='2026-10-24'
    shift_source_convention: str='Unknown; not converted'
    shift_source: str=''

@dataclass(frozen=True)
class Projector:
    id: str
    manufacturer: str
    model: str
    resolution: tuple
    lumens: float
    lenses: tuple
    source: str
    source_revision: str=''
    checked_on: str='2026-10-24'
    light_output_basis: str='Nominal; see source'

SOURCE='https://www.christiedigital.com/globalassets/resources/public/4k7-4k10-hs-datasheet.pdf'
LENSES={
 'christie_085':Lens('christie_085','0.85–1.02:1 zoom',.85,1.02,None,None,
     'Nominal throw guidance only. Published offsets ±59% H / ±140% V have not been normalised to Beam full-image units; shifted solves are blocked. Coupled shift envelope and distance corrections unverified.',SOURCE,'July 2023, p2',shift_source_convention='Published ±59% H / ±140% V; optical centre and coupled envelope unverified'),
 'synthetic_120':Lens('synthetic_120','TEST ONLY · 1.20–1.60',1.2,1.6,(-25,25),(-55,55),'Synthetic rectangular independent shift envelope; not a real lens','Beam synthetic test fixture')}
PROJECTORS={
 'christie_4k10':Projector('christie_4k10','Christie','4K10-HS (native raster)',(2716,1528),10000,('christie_085',),SOURCE,'July 2023, p2',light_output_basis='ANSI lumens'),
 'synthetic':Projector('synthetic','Test fixture','Synthetic 1080p',(1920,1080),10000,('synthetic_120',),'Beam synthetic test fixture')}


PANASONIC='https://docs.connect.panasonic.com/projector/download/catalog/pdf/PT_RZ990_S_2P_ctlg_Eng_PC.pdf'
EPSON='https://files.support.epson.com/pdf/specs/specifications_ebpu2010series_en_r102.pdf'
BARCO='https://assets.barco.com/m/65f051bcac7e2970/original/G100-W22-en-Spec-sheet.pdf'
UNKNOWN='Nominal throw guidance only; shift origin/envelope not verified. Nonzero shifted solves blocked.'
LENSES.update({
 'panasonic_dle150':Lens('panasonic_dle150','ET-DLE150',1.30,1.89,None,None,UNKNOWN,PANASONIC,'RZ990series_G2, p2',shift_source_convention='Offsets from lens-mounter origin; Beam optical-centre conversion unverified'),
 'panasonic_dle170':Lens('panasonic_dle170','ET-DLE170',1.71,2.41,None,None,UNKNOWN,PANASONIC,'RZ990series_G2, p2',shift_source_convention='Offsets from lens-mounter origin; Beam optical-centre conversion unverified'),
 'epson_m15':Lens('epson_m15','ELPLM15',1.57,2.56,None,None,UNKNOWN+' Published distance formula includes lens-specific intercepts.',EPSON,'r1.02, pp10,26',shift_source_convention='Lens-specific home position and lens-to-screen-base distances; conversion unverified'),
 'epson_w08':Lens('epson_w08','ELPLW08',.86,1.21,None,None,UNKNOWN+' Published distance formula includes lens-specific intercepts.',EPSON,'r1.02, pp10,26',shift_source_convention='Lens-specific home position and lens-to-screen-base distances; conversion unverified'),
 'barco_gc120':Lens('barco_gc120','GC 1.2–1.5',1.2,1.5,None,None,UNKNOWN,BARCO,'G100-W22 specification sheet',shift_source_convention='Up to 120% vertical / 50% horizontal depending on lens; lens-specific envelope unverified'),
 'barco_gc150':Lens('barco_gc150','GC 1.5–2.0',1.5,2,None,None,UNKNOWN,BARCO,'G100-W22 specification sheet',shift_source_convention='Up to 120% vertical / 50% horizontal depending on lens; lens-specific envelope unverified')})
PROJECTORS.update({
 'panasonic_rz990':Projector('panasonic_rz990','Panasonic','PT-RZ990',(1920,1200),9400,('panasonic_dle150','panasonic_dle170'),PANASONIC,'RZ990series_G2, pp1–2',light_output_basis='Normal mode, ISO/IEC 21118:2020; not centre lumens'),
 'epson_pu2010':Projector('epson_pu2010','Epson','EB-PU2010B',(1920,1200),10000,('epson_m15','epson_w08'),EPSON,'r1.02, pp5,10,26',light_output_basis='Normal mode; manufacturer specification'),
 'barco_g100w22':Projector('barco_g100w22','Barco','G100-W22',(1920,1200),18500,('barco_gc120','barco_gc150'),BARCO,'G100-W22 specification sheet',light_output_basis='ANSI lumens; not 22000 ISO lumen rating')})

# Additional conventional lenses, verified against the same official tables.
LENSES.update({
 'panasonic_dle105':Lens('panasonic_dle105','ET-DLE105',.978,1.32,None,None,UNKNOWN,PANASONIC,'RZ990series_G2 April 2022, p2',shift_source_convention='Manual pp77–78: full-image dimensions relative to lens-mounter/home origin, coupled polygon; not an independent rectangle'),
 'panasonic_dle250':Lens('panasonic_dle250','ET-DLE250',2.27,3.62,None,None,UNKNOWN,PANASONIC,'RZ990series_G2 April 2022, p2',shift_source_convention='Manual pp77–78: full-image dimensions relative to lens-mounter/home origin, coupled polygon; not an independent rectangle'),
 'barco_gc200':Lens('barco_gc200','GC 2.0–4.0',2,4,None,None,UNKNOWN,BARCO,'18 September 2026, p2',shift_source_convention='Lens-dependent maxima; coupled envelope and centre convention unverified')})
from dataclasses import replace
PROJECTORS['panasonic_rz990']=replace(PROJECTORS['panasonic_rz990'],lenses=PROJECTORS['panasonic_rz990'].lenses+('panasonic_dle105','panasonic_dle250'))
PROJECTORS['panasonic_rz890']=Projector('panasonic_rz890','Panasonic','PT-RZ890',(1920,1200),8500,PROJECTORS['panasonic_rz990'].lenses,PANASONIC,'RZ990series_G2 April 2022, pp1–2',light_output_basis='Normal mode, ISO/IEC 21118:2020; not centre lumens')
PROJECTORS['barco_g100w22']=replace(PROJECTORS['barco_g100w22'],lenses=PROJECTORS['barco_g100w22'].lenses+('barco_gc200',),source_revision='18 September 2026, p2')
for key in ('panasonic_dle105','panasonic_dle150','panasonic_dle170','panasonic_dle250'):
    LENSES[key]=replace(LENSES[key],shift_source='https://eu.connect.panasonic.com/sites/default/files/media/document/2025-01/rz990_manual_en.pdf',shift_source_convention='Manual p77: full-image H/V dimensions, lens-mounter/home origin and coupled polygon; not converted to independent limits')
UNSUPPORTED_OPTICS={
 'panasonic_dle020':dict(model='ET-DLE020',source=PANASONIC,reason='UST optical geometry/offset is not validated in Beam’s central pinhole model'),
 'panasonic_dle035':dict(model='ET-DLE035',source=PANASONIC,reason='UST offset and lens-mounter origin are not represented by the current model'),
 'barco_fldx038':dict(model='FLDX 0.38 UST 90°',source=BARCO,reason='Folded 90-degree UST optics are not represented by the current model')}

def projector_items():return [('MANUAL','Generic / Manual','No manufacturer constraints')]+[(k,p.manufacturer+' · '+p.model,p.source) for k,p in PROJECTORS.items()]
def lens_items(self,context):
    model=PROJECTORS.get(self.optics_model)
    return [('MANUAL','Generic / Manual','No lens constraints')]+[(k,LENSES[k].model,LENSES[k].restrictions) for k in model.lenses] if model else [('MANUAL','Generic / Manual','No lens constraints')]
