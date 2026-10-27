"""Independent bounded scientific acceptance checks. Read-only, stdout only."""
import csv,importlib.util,json,math,pathlib,sys,unittest
import numpy as np
source=pathlib.Path(sys.argv[1]);spec=importlib.util.spec_from_file_location('comparison_under_test',source/'compare_tp.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class PhysicsChecks(unittest.TestCase):
 def test_internal_flux_limit_and_opacity_units(self):
  p=np.array([0.1,1.,10.]);tau=(10**-1.5*0.1)*p*1e5/10
  expected=(0.75*100**4*(tau+2/3))**0.25
  np.testing.assert_allclose(m.radiative_temperature(p,0,100,10,10**-1.5,0.1),expected,rtol=1e-12)
 def test_deep_irradiation_limit(self):
  t=m.radiative_temperature(np.array([1000.]),350,0,10,10**-1.5,0.1)
  np.testing.assert_allclose(t,350*(0.5*(1+1/0.1))**0.25,rtol=1e-12)
 def test_saved_picaso_reference(self):
  for tint in (25,50):
   path=pathlib.Path(r'D:\GPT\projects\Sub-Neptune\tp-lab\runs\smoke')/f'guillot_tint{tint}.csv'
   with path.open() as f: rows=list(csv.DictReader(f))
   p=np.array([float(r['pressure_bar']) for r in rows]);ref=np.array([float(r['temperature_K']) for r in rows])
   actual=m.radiative_temperature(p,350,tint,10,10**-1.5,0.1)
   np.testing.assert_allclose(actual,ref,rtol=0.002,err_msg='Direct Eq49 vs saved PICASO interpolation')
 def test_anchor_continuity_and_log_slope(self):
  for anchor in (1.,10.,100.):
   ta=float(np.asarray(m.radiative_temperature(np.array([anchor]),350,25,10,10**-1.5,0.1))[0])
   p=np.array([anchor,anchor*2,anchor*4]);t=m.adiabat_temperature(p,anchor,ta)
   self.assertAlmostEqual(float(t[0]),ta,places=10)
   np.testing.assert_allclose(np.diff(np.log(t))/np.diff(np.log(p)),2/7,rtol=1e-12)
 def test_isothermal_hydrostatic_integral(self):
  p=np.logspace(0,3,61);t=np.full(p.shape,400.)
  expected=1.380649e-23*400/(2.3*1.66053906660e-27*10)*np.log(1000)
  self.assertAlmostEqual(m.thickness(p,t,10,2.3)/expected,1,places=12)
 def test_bad_inputs(self):
  for p,t in (([1,0.1],[300,400]),([1,2],[300,-1]),([1,2],[300,float('nan')]),([1,2],[300]),([0,1],[300,400])):
   with self.subTest(p=p,t=t),self.assertRaises(ValueError):m.thickness(np.array(p),np.array(t),10,2.3)
 def test_pilot_shape_and_finiteness(self):
  result=m.run_experiment({'levels':[181]});self.assertEqual(len(result['rows']),18)
  for row in result['rows']:
   for k,v in row.items():
    if isinstance(v,(float,int)): self.assertTrue(math.isfinite(v),k)
   self.assertLess(abs(row['adiabat_integral_relative_error']),0.0002)
 def test_unknown_config_rejected(self):
  with self.assertRaises(ValueError):m.run_experiment({'wrong_parameter':1})
class OutputChecks(unittest.TestCase):
 def test_full_shape_and_strict_json(self):
  result=m.run_experiment();self.assertEqual(len(result['rows']),54);json.dumps(result,allow_nan=False)
  self.assertEqual(sorted(set(r['nlevel'] for r in result['rows'])),[181,361,721])
  for r in result['rows']:self.assertLess(abs(r['adiabat_integral_relative_error']),0.0002)
 def test_upper_profile_unchanged(self):
  result=m.run_experiment({'levels':[181]});plot=result['plot'];p=np.array(plot['pressure_bar']);ref=np.array(plot['reference_K'])
  for anchor in (1,10,100):np.testing.assert_allclose(np.array(plot[f'adiabat_{anchor}bar_K'])[p<=anchor],ref[p<=anchor],rtol=1e-12)
 def test_only_levels_overridable(self):
  for k in ('teq','gravity','mu','anchors_bar'):
   with self.subTest(k=k),self.assertRaises(ValueError):m.run_experiment({k:10})
 def test_invalid_radiative_parameters(self):
  for args in (([0],350,25,10,0.03,0.1),([1],350,25,0,0.03,0.1),([1],350,25,10,0.03,0)):
   with self.subTest(args=args),self.assertRaises(ValueError):m.radiative_temperature(*args)
if __name__=='__main__':unittest.main(argv=[sys.argv[0]],verbosity=2)
