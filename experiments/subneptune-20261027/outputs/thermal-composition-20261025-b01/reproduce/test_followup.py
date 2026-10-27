import math,unittest
from followup_comparisons import recipe,select_bracket
class Checks(unittest.TestCase):
 def test_mass_and_rock_ratio(self):
  for m in (5,8.04):
   for f in (.0001,.003,.01,.03,.1):
    r=recipe('a',m,f,360)
    vals=[float(r[k]) for k in ('mass_of_core','mass_of_mantle','mass_of_hydro','mass_of_atm')]
    self.assertAlmostEqual(sum(vals),m);self.assertAlmostEqual(vals[3]/m,f)
    self.assertAlmostEqual(vals[0]/sum(vals[:2]),.325)
 def test_invalid_recipe(self):
  for m,f,t in ((0,.01,360),(5,0,360),(5,1,360),(5,float('nan'),360),(5,.01,-1)):
   with self.assertRaises(ValueError):recipe('a',m,f,t)
 def test_bracket_sorted(self):
  self.assertEqual(select_bracket([(.03,3),(.003,1),(.01,2)],2.5),((.01,2),(.03,3)))
 def test_bad_bracket(self):
  for points,target in (([(.1,1),(.2,2)],3),([(.1,2),(.2,1)],1.5)):
   with self.assertRaises(ValueError):select_bracket(points,target)
if __name__=='__main__':unittest.main()
