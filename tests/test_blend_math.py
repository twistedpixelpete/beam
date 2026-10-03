import importlib.util
from pathlib import Path
import unittest
root=Path(__file__).resolve().parents[1]/'projection_study'
def load(name):
    spec=importlib.util.spec_from_file_location(name,root/(name+'.py')); module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module); return module
m=load('blend_math'); naming=load('interchange')
class BeamMathTests(unittest.TestCase):
    def test_overlap_units(self):
        for mode,value in [('PIXELS',400),('PERCENT',400/3840*100),('METRES',400/3840*10)]:
            result=m.overlap_values(value,mode,3840,10)
            self.assertAlmostEqual(result['pixels'],400); self.assertAlmostEqual(result['metres'],400/3840*10)
    def test_clamping(self):
        self.assertEqual(m.overlap_values(500,'PERCENT',1920,10)['fraction'],.95)
        self.assertEqual(m.overlap_values(-1,'PIXELS',1920,10)['fraction'],0)
    def test_array_neighbors(self):
        self.assertEqual(m.cells('ARRAY',6,3),[(0,0),(1,0),(2,0),(0,1),(1,1),(2,1)])
        self.assertEqual(len(m.adjacent('ARRAY',6,3)),7)
        self.assertEqual(len(m.adjacent('VERTICAL',4,3)),3)
    def test_polygon_overlap(self):
        a=[(0,0),(10,0),(10,5),(0,5)]; b=[(8,0),(18,0),(18,5),(8,5)]
        p=m.intersection(a,b)
        self.assertAlmostEqual(max(x for x,y in p)-min(x for x,y in p),2)
        self.assertEqual(m.intersection(a,[(20,0),(30,0),(30,5),(20,5)]),[])
        self.assertEqual(m.intersection(list(reversed(a)),b),p)
    def test_names(self):
        self.assertEqual(naming.beam_filename('Melbourne Town Hall','R02','PJ01 Coverage'),'Melbourne_Town_Hall_R02_PJ01_Coverage.png')
        self.assertEqual(naming.beam_filename('','','PJ01 Coverage'),'Beam_PJ01_Coverage.png')
        self.assertNotIn('/',naming.beam_filename('../Project: A','R02','View?A'))
        self.assertNotIn('__',naming.beam_filename('Project   A','___',' View A '))
