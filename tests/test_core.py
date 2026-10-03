import unittest
import importlib.util
import sys
from pathlib import Path
import io
import csv
import uuid
import math

ROOT=Path(__file__).resolve().parents[1]/'projection_study'
def load(name):
    spec=importlib.util.spec_from_file_location(name,ROOT/(name+'.py'))
    module=importlib.util.module_from_spec(spec); sys.modules[name]=module
    spec.loader.exec_module(module)
    return module

projection=load('projection_math'); utils=load('utils'); table=load('export_table')
patterns=load('output_patterns'); conversion=load('transform_conversion')
display=load('display_units'); interchange=load('interchange')

class ProjectionTests(unittest.TestCase):
    def test_16_9(self):
        m=projection.calculate(10,1,1920,1080)
        self.assertEqual(m.width,10); self.assertEqual(m.height,5.625)
    def test_16_10(self): self.assertEqual(projection.calculate(10,1,1920,1200).height,6.25)
    def test_ratio(self): self.assertEqual(projection.calculate(10,2,1920,1080).width,5)
    def test_density_dpi(self):
        m=projection.calculate(10,1,1920,1080)
        self.assertEqual(m.pixels_per_metre,192)
        self.assertAlmostEqual(m.dpi,1920/(10000/25.4))
    def test_stack_brightness_lux(self):
        m=projection.calculate(10,1,1920,1080,20000,50,3)
        self.assertEqual(m.total_lumens,30000)
        self.assertAlmostEqual(m.lux,30000/56.25)
    def test_zero_brightness(self): self.assertEqual(projection.calculate(10,1,1920,1080,20000,0,3).lux,0)
    def test_invalid(self):
        for args in [(0,1,1920,1080),(10,0,1920,1080),(10,1,0,1080),(math.nan,1,1920,1080),(10,1,1920,1080,-1),(10,1,1920,1080,1,101)]:
            with self.assertRaises(ValueError): projection.calculate(*args)
    def test_shift(self):
        self.assertEqual(projection.image_point(.5,.5,10,1,1920,1080,20,40),(2,2.25,-10))
        c=projection.camera_parameters(1,1920,1080,20,40)
        self.assertEqual(c['lens'],36); self.assertEqual(c['shift_x'],.2)
        self.assertEqual(c['shift_y'],.225)
    def test_uuid(self):
        values={utils.new_uuid() for _ in range(1000)}
        self.assertEqual(len(values),1000)
        self.assertTrue(all(uuid.UUID(v).version==4 for v in values))
    def test_identifiers(self):
        self.assertEqual(utils.next_identifier([]),'PJ01')
        self.assertEqual(utils.next_identifier(['PJ01','PJ02','PJ04','Other','PJ02.001']),'PJ05')
        self.assertEqual(utils.next_identifier(['PJ99']),'PJ100')
    def test_palette(self):
        self.assertEqual(len(set(utils.PALETTE)),8)
        self.assertTrue(all(0<c<1 for colour in utils.PALETTE for c in colour))
    def test_units(self): self.assertEqual(conversion.position_mm((1,2,3),.001),(1,2,3))
    def test_export_format(self):
        stream=io.StringIO(); row=['PJ01']+[1]*23+['mm','lux',utils.new_uuid()]
        table.write_table(stream,[row]); rows=list(csv.reader(io.StringIO(stream.getvalue())))
        self.assertEqual(len(rows[0]),27)
        self.assertEqual(rows[0][7],'Projector_Trow-Ratio')
        self.assertEqual(rows[1][-3:-1],['mm','lux'])
    def test_export_validation(self):
        with self.assertRaises(ValueError): table.write_table(io.StringIO(),[[1]])
        with self.assertRaises(ValueError): table.write_table(io.StringIO(),[[math.inf]*27])
    def test_pattern_bounds(self):
        for rx,ry in [(1920,1080),(1920,1200),(1080,1920)]:
            lines,quads=patterns.pattern('GRID','PJ100',rx,ry)
            self.assertTrue(lines and quads)
            self.assertTrue(all(0<=x<=1 and 0<=y<=1 for shape in lines+quads for x,y in shape))
    def test_toggles(self):
        lines,quads=patterns.pattern('GRID','PJ01',1920,1080,False,False)
        self.assertFalse(lines); self.assertFalse(quads)

class WorkflowTests(unittest.TestCase):
    def test_pixel_size(self):
        m=projection.calculate(10,1,3840,2160)
        self.assertAlmostEqual(m.pixel_size_m*1000,2.6041666667)
        self.assertAlmostEqual(m.pixel_size_m*m.pixels_per_metre,1)
    def test_display_units(self):
        self.assertEqual(display.dimension(10,'m'),'10.000 m')
        self.assertEqual(display.dimension(10,'mm'),'10,000.0 mm')
        self.assertEqual(display.pixel_size(10/3840,'mm'),'2.60 mm/px')
        self.assertIn('m/px',display.pixel_size(10/3840,'m'))
        self.assertEqual(display.coordinates((1,2,3),'mm'),'1000.0, 2000.0, 3000.0 mm')
    def test_predictable_filenames(self):
        self.assertEqual(interchange.image_filename('PJ01 Coverage','12345678-rest'),'pj01-coverage--12345678.png')
        self.assertNotEqual(interchange.image_filename('Overview','aaaaaaaa'),interchange.image_filename('Overview','bbbbbbbb'))
        self.assertNotIn('/',interchange.image_filename('../../Unsafe','12345678'))
    def test_png_orientation(self):
        import tempfile,struct,zlib
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'tiny.png'
            interchange.write_png(path,1,2,bytes([255,0,0,255,0,0,255,255]))
            data=path.read_bytes(); self.assertEqual(data[:8],b'\x89PNG\r\n\x1a\n')
            pos=8; compressed=b''
            while pos<len(data):
                size=struct.unpack('!I',data[pos:pos+4])[0]
                if data[pos+4:pos+8]==b'IDAT': compressed+=data[pos+8:pos+8+size]
                pos+=size+12
            self.assertEqual(zlib.decompress(compressed),bytes([0,0,0,255,255,0,255,0,0,255]))
    def test_invalid_buffer(self):
        with self.assertRaises(ValueError): interchange.write_png('unused.png',2,2,b'')
    def test_timestamp(self):
        from datetime import datetime
        self.assertIsNotNone(datetime.fromisoformat(interchange.timestamp()).tzinfo)

if __name__=='__main__': unittest.main()
