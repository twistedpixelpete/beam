import unittest,math,importlib.util
from pathlib import Path
spec=importlib.util.spec_from_file_location('surface_analysis',Path(__file__).resolve().parents[1]/'projection_study/surface_analysis.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class SurfaceTests(unittest.TestCase):
 def test_perpendicular_off_axis(self):
  for point in [(0,0,-6),(2,1,-6)]:
   r=m.local_metrics(point,(0,0,1),1,1920,1080)
   self.assertAlmostEqual(r['density_px_m'],320);self.assertAlmostEqual(r['anisotropy'],1)
 def test_oblique_analytic(self):
  r=m.local_metrics((0,0,-6),(math.sin(math.pi/3),0,math.cos(math.pi/3)),1,1920,1080)
  self.assertAlmostEqual(r['anisotropy'],2);self.assertAlmostEqual(r['density_px_m'],160)
 def test_outside_and_behind(self):
  self.assertIsNone(m.local_metrics((5,0,-6),(0,0,1),1,1920,1080))
  self.assertIsNone(m.local_metrics((0,0,6),(0,0,1),1,1920,1080))
 def test_invalid(self):
  with self.assertRaises(ValueError):m.local_metrics((0,0,-6),(0,0,0),1,1920,1080)
 def test_weighted_coverage(self):
  a=m.local_metrics((0,0,-6),(0,0,1),1,1920,1080)
  r=m.summarise([dict(area_m2=3,nominal=[a],visible=[a]),dict(area_m2=1,nominal=[a],visible=[])])
  self.assertEqual(r['coverage_percent'],75);self.assertEqual(r['occluded_sample_percent'],50)
 def test_jacobian_finite_difference(self):
  point=(1,.5,-6);n=(.6,0,.8);r=m.local_metrics(point,n,1,1920,1080)
  # Two nearby raster rays intersect the same tangent plane.
  plane=m.dot(n,point);ray=(point[0]/6,point[1]/6,-1)
  for axis,key in [(0,'pixel_width_m'),(1,'pixel_height_m')]:
   q=list(ray);q[axis]+=1e-3/1920;t=plane/m.dot(n,q);hit=[x*t for x in q]
   pitch=m.norm([a-b for a,b in zip(hit,point)])/1e-3
   self.assertAlmostEqual(pitch,r[key],places=7)
