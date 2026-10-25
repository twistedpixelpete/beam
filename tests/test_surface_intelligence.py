import unittest, math
from test_surface_analysis import m

class IlluminanceTests(unittest.TestCase):
 def metrics(self,p=(0,0,-10),n=(0,0,1)):return m.local_metrics(p,n,1,2000,1000)
 def test_flat_perpendicular(self):
  for x in (-4,0,4):self.assertAlmostEqual(m.illuminance_lux(self.metrics((x,0,-10)),20000,2000,1000),400)
 def test_flux_stack_brightness(self):
  r=self.metrics()
  self.assertAlmostEqual(m.illuminance_lux(r,40000,2000,1000),800)
  self.assertAlmostEqual(m.illuminance_lux(r,20000,2000,1000,2),800)
  self.assertAlmostEqual(m.illuminance_lux(r,20000,2000,1000,2,50),400)
 def test_doubled_area(self):
  self.assertAlmostEqual(m.illuminance_lux(self.metrics((0,0,-10*math.sqrt(2))),20000,2000,1000),200)
 def test_incidence(self):
  self.assertAlmostEqual(m.illuminance_lux(self.metrics(n=(math.sqrt(3)/2,0,.5)),20000,2000,1000),200)
 def test_overlap_and_blocked(self):
  samples=[dict(area_m2=1,visible=[dict(illuminance_lux=400,distance_m=10),dict(illuminance_lux=350,distance_m=11)]),dict(area_m2=1,visible=[])]
  s=m.intelligence_statistics(samples)
  self.assertEqual(s['illuminance_max_lux'],750);self.assertEqual(s['illuminance_average_lux'],375)
  self.assertEqual(s['illuminance_min_lux'],0);self.assertEqual(s['illuminance_uniformity_min_average'],0)
 def test_dark_uniformity(self):
  self.assertIsNone(m.intelligence_statistics([dict(area_m2=1,visible=[])])['illuminance_uniformity_min_average'])

class DistanceTests(unittest.TestCase):
 def test_geometric_fixtures(self):
  # Constant radius, tilted plane, stepped and curved geometry all use Euclidean lens distance.
  for p,expected in [((0,0,-10),10),((3,0,-4),5),((0,0,-12),12),((6,0,-8),10)]:self.assertAlmostEqual(m.norm(p),expected)
 def test_source_and_variation(self):
  s=m.intelligence_statistics([dict(area_m2=1,visible=[dict(distance_m=8,illuminance_lux=1),dict(distance_m=12,illuminance_lux=1)]),dict(area_m2=3,visible=[dict(distance_m=10,illuminance_lux=1)])])
  self.assertEqual(s['distance_min_m'],8);self.assertEqual(s['distance_average_m'],9.5);self.assertEqual(s['distance_variation_m'],2)

class AcuityTests(unittest.TestCase):
 def test_known_pitch_distance(self):
  actual=m.angular_pixel_radians((.01,0,0),(0,.01,0),(0,0,10))
  self.assertAlmostEqual(actual,2*math.atan(.01/20))
 def test_threshold_distance_resolution(self):
  a=m.angular_pixel_radians((.003,0,0),(0,.003,0),(0,0,10))
  b=m.angular_pixel_radians((.003,0,0),(0,.003,0),(0,0,20))
  c=m.angular_pixel_radians((.0015,0,0),(0,.0015,0),(0,0,10))
  self.assertGreater(math.degrees(a)*60,1);self.assertLess(math.degrees(b)*60,1);self.assertAlmostEqual(b,c)
 def test_foreshortening(self):
  a=m.angular_pixel_radians((.02,0,0),(0,.01,0),(0,0,10))
  b=m.angular_pixel_radians((.02,0,0),(0,.01,0),(math.sqrt(75),0,5))
  self.assertAlmostEqual(b,2*math.atan(.01/20));self.assertGreater(a,b)
 def test_area_denominator_and_boundary(self):
  s=m.acuity_statistics([dict(area_m2=1,angular_pixel_arcmin=.5),dict(area_m2=3,angular_pixel_arcmin=1),dict(area_m2=7,angular_pixel_arcmin=None)],1)
  self.assertEqual(s['acuity_below_threshold_percent'],25);self.assertEqual(s['acuity_at_or_above_threshold_percent'],75)
 def test_eye_on_sample(self):self.assertIsNone(m.angular_pixel_radians((1,0,0),(0,1,0),(0,0,0)))
