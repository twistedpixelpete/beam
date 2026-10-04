import unittest,math,importlib.util
from pathlib import Path
spec=importlib.util.spec_from_file_location('screen_math',Path(__file__).resolve().parents[1]/'projection_study/screen_math.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class ScreenMath(unittest.TestCase):
    def test_arc_defining_pairs(self):
        for mode in ['LENGTH_RADIUS','LENGTH_ANGLE','RADIUS_ANGLE','CHORD_RADIUS','CHORD_ANGLE']:
            v=m.arc_values(mode,10,90,5*math.pi,math.sqrt(200));self.assertAlmostEqual(v['radius'],10);self.assertAlmostEqual(v['angle'],90);self.assertAlmostEqual(v['length'],5*math.pi)
    def test_invalid(self):
        for args in [('CHORD_RADIUS',2,90,3,5),('RADIUS_ANGLE',1,361,1,1),('LENGTH_RADIUS',0,90,1,1),('CHORD_ANGLE',1,360,1,1)]:
            with self.assertRaises(ValueError):m.arc_values(*args)
    def test_led(self):
        v=m.led_values(.5,.5,192,192,20,8,2.5);self.assertEqual((v['width'],v['height'],v['rx'],v['ry'],v['angle']),(10,4,3840,1536,47.5));self.assertAlmostEqual(v['pitch_x'],2.6041666666667)
    def test_chain(self):
        p=m.faceted_path(.5,20,2.5);self.assertEqual(len(p),21)
        for a,b in zip(p,p[1:]):self.assertAlmostEqual(math.dist(a,b),.5)
        headings=[math.atan2(b[1]-a[1],b[0]-a[0]) for a,b in zip(p,p[1:])];self.assertAlmostEqual(math.degrees(headings[-1]-headings[0]),47.5)
    def test_closed_uv_seam(self):
        p=m.circular_path(3,360,96,closed=True);v,f,u=m.strip(p,4,closed=True);self.assertEqual(len(v),192);self.assertEqual(f[-1][1],0);self.assertEqual(u[-1][1][0],1)
    def test_distance_uv(self):
        v,f,u=m.strip([(0,0,0),(1,0,0),(1,3,0)],4);self.assertEqual(u[0][1][0],.25)
if __name__=='__main__':unittest.main()
