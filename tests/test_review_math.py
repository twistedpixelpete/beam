"""Independent numerical checks added during PR #2 engineering review."""
import random
import unittest
from test_planning_math import p,c

class ReviewMath(unittest.TestCase):
 def test_array_units_both_axes(self):
  variants=[dict(units='PIXELS',overlap_h=192,overlap_v=216),dict(units='PERCENT',overlap_h=10,overlap_v=20),dict(units='METRES',overlap_h=1,overlap_v=1.125)]
  for variant in variants:
   result=p.plan(12,6,1920,1080,1,'ARRAY',columns=2,rows=2,fixed_distance=True,distance=10,**variant)
   for axis,expected in [('h',(1,192,10)),('v',(1.125,216,20))]:
    for key,value in zip(('metres','pixels','percent'),expected):self.assertAlmostEqual(result['overlap_'+axis][key],value)
 def test_auto_count_is_minimum(self):
  for layout,w,h in [('HORIZONTAL',16,3),('VERTICAL',5,12),('ARRAY',17,9)]:
   result=p.plan(w,h,1920,1080,1,layout,auto=True,distance=6)
   self.assertGreaterEqual(result['coverage_width']+1e-6,w);self.assertGreaterEqual(result['coverage_height']+1e-6,h)
   for n in range(1,result['count']):
    shapes=[(n,1)] if layout=='HORIZONTAL' else [(1,n)] if layout=='VERTICAL' else [(a,n//a) for a in range(1,n+1) if n%a==0]
    for cols,rows in shapes:
     with self.assertRaises(ValueError):p.plan(w,h,1920,1080,1,layout,count=n,columns=cols,rows=rows,fixed_distance=True,distance=6)
 def test_portrait_inverse_roundtrip(self):
  for mode in ('LENS','POSITION'):
   for field,value in [('WIDTH',3),('HEIGHT',6),('DENSITY',360),('PIXEL_SIZE',1/360)]:
    distance,ratio,_=p.inverse(field,value,mode,8,1.2,1080,1920)
    m=p.calculate(distance,ratio,1080,1920)
    actual={'WIDTH':m.width,'HEIGHT':m.height,'DENSITY':m.pixels_per_metre,'PIXEL_SIZE':m.pixel_size_m}[field]
    self.assertAlmostEqual(actual,value)
 def test_union_independent_integer_cell_oracle(self):
  rng=random.Random(2902)
  for _ in range(40):
   polygons=[];cells=set()
   for _ in range(8):
    x,y=rng.randrange(-5,5),rng.randrange(-5,5);w,h=rng.randrange(1,5),rng.randrange(1,5)
    polygons.append([(x,y),(x+w,y),(x+w,y+h),(x,y+h)])
    cells.update((a,b) for a in range(x,x+w) for b in range(y,y+h))
   self.assertAlmostEqual(c.union_area(polygons),len(cells))
 def test_nonfinite_and_overlap_limits(self):
  for value in (float('nan'),float('inf'),-1,95,100):
   with self.assertRaises(ValueError):p.plan(12,6,1920,1080,1,'ARRAY',units='PERCENT',overlap_h=value)
