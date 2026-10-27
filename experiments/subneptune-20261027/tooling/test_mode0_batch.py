import tempfile,unittest
from pathlib import Path
from mode0_batch import render_config, parse_profile, validate_case
ROW={'case_id':'demo','mass_of_core':'0.33','mass_of_mantle':'0.67','mass_of_hydro':'0','mass_of_atm':'0','surface_temp':'300','P_surface':'100000','tight':'0'}
class BatchTests(unittest.TestCase):
 def test_render_enforces_mode0_and_unique_destination(self):
  template='input_mode=0\nmass_of_core=1\nmass_of_mantle=0\nmass_of_hydro=0\nmass_of_atm=0\nsurface_temp=100\nP_surface=1\noutput_file="old"\n'
  result=render_config(template,ROW,'/mnt/d/new/profile.txt')
  self.assertIn('input_mode=0',result);self.assertIn('output_file="/mnt/d/new/profile.txt"',result);self.assertIn('mass_of_core=0.33',result)
 def test_reject_unsafe_or_unphysical_case(self):
  for update in ({'case_id':'../escape'},{'mass_of_atm':'nan'},{'surface_temp':'0'},{'mass_of_core':'-1'}):
   with self.subTest(update=update),self.assertRaises(ValueError):validate_case({**ROW,**update})
 def test_good_profile(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'profile.txt';p.write_text('Index Radius Pressure Mass Density Temp Phase\n0 0 1 0 5 400 Solid\n1 1 1e-5 1 3 300 Solid\n')
   r=parse_profile(p,ROW);self.assertEqual(r['radius_re'],1)
 def test_reject_appended_or_invalid_profile(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'profile.txt'
   for text in ('Index x\n0 0 1 0 5 400 X\n1 1 1e-5 1 -3 300 X\n','Index x\n0 0 1 0 5 400 X\nIndex x\n1 1 1e-5 1 3 300 X\n'):
    p.write_text(text)
    with self.assertRaises(ValueError):parse_profile(p,ROW)
if __name__=='__main__':unittest.main()
