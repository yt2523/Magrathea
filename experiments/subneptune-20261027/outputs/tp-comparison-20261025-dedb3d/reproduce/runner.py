"""Numerical test-agent driver: fixed-input assembly, checks and diagnostics.
The mathematical kernel is unchanged DeepSeek code, independently GPT reviewed.
Read-only computation; the trusted collector, not this process, writes artifacts.
"""
import csv,importlib.util,json,math,pathlib,sys,time
import numpy as np
root=pathlib.Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('reviewed_kernel',root/'source/compare_tp.py');kernel=importlib.util.module_from_spec(spec);spec.loader.exec_module(kernel)
KB=1.380649e-23;AMU=1.66053906660e-27;G=10.;MU=2.3;TEQ=350.;KAPPA=10**-1.5;NABLA=2/7

def require(condition,message):
 if not condition:raise ValueError(message)
def validate(p,t):
 require(p.ndim==1 and t.shape==p.shape and len(p)>=2,'profile arrays')
 require(np.isfinite(p).all() and (p>0).all() and (np.diff(p)>0).all(),'positive increasing finite pressure')
 require(np.isfinite(t).all() and (t>0).all(),'positive finite temperature')
def rad(p,tint,gamma):
 p=np.asarray(p,dtype=float);require(np.isfinite(p).all() and (p>0).all(),'radiative input')
 t=np.asarray(kernel.radiative_temperature(p,TEQ,tint,G,KAPPA,gamma));require(np.isfinite(t).all() and (t>0).all(),'radiative output');return t

def execute(pilot=False):
 start=time.perf_counter();levels=[181] if pilot else [181,361,721];checks={}
 p=np.array([.1,1.,10.]);tau=KAPPA*.1*p*1e5/G
 checks['intrinsic_limit_and_SI_units']=bool(np.allclose(kernel.radiative_temperature(p,0,100,G,KAPPA,.1),(.75*100**4*(tau+2/3))**.25,rtol=1e-12))
 checks['deep_irradiation_limit']=bool(np.allclose(kernel.radiative_temperature(np.array([1000.]),350,0,G,KAPPA,.1),350*(.5*(1+1/.1))**.25,rtol=1e-12))
 q=np.geomspace(1,1000,61);t=np.full(q.shape,400.);exact=KB/(MU*AMU*G)*400*np.log(1000)
 checks['isothermal_hydrostatic_integral']=abs(float(kernel.thickness(q,t,G,MU))/exact-1)<1e-12
 reference_error=0.
 for tint in (25,50):
  path=(root/'reference')/f'guillot_tint{tint}.csv'
  with path.open() as f:data=list(csv.DictReader(f))
  p=np.array([float(r['pressure_bar']) for r in data]);ref=np.array([float(r['temperature_K']) for r in data])
  reference_error=max(reference_error,float(np.max(np.abs(rad(p,tint,.1)/ref-1))))
 checks['saved_PICASO_agreement_0p2percent']=reference_error<.002
 rows=[];max_anchor_error=0.;max_integral_error=0.;max_slope_error=0.
 for nlevel in levels:
  pfull=np.logspace(-6,3,nlevel)
  for tint in (25.,50.):
   for gamma in (.03,.1,.3):
    tfull=rad(pfull,tint,gamma);validate(pfull,tfull)
    grad=np.gradient(np.log(tfull),np.log(pfull),edge_order=2)
    for anchor in (1.,10.,100.):
     p=np.r_[anchor,pfull[pfull>anchor*(1+1e-12)]]
     ta=float(rad(np.array([anchor]),tint,gamma)[0]);ref=rad(p,tint,gamma)
     ad=np.asarray(kernel.adiabat_temperature(p,anchor,ta));validate(p,ref);validate(p,ad)
     anchor_error=abs(float(ad[0])/ta-1);max_anchor_error=max(max_anchor_error,anchor_error)
     slope=np.diff(np.log(ad))/np.diff(np.log(p));max_slope_error=max(max_slope_error,float(np.max(np.abs(slope-NABLA))))
     href=float(kernel.thickness(p,ref,G,MU));had=float(kernel.thickness(p,ad,G,MU))
     exact_adiabat=(KB/(MU*AMU*G))*ta/NABLA*((1000/anchor)**NABLA-1)
     relerr=had/exact_adiabat-1;max_integral_error=max(max_integral_error,abs(relerr))
     rows.append(dict(nlevel=nlevel,tint_K=tint,gamma=gamma,anchor_bar=anchor,reference_bottom_K=float(ref[-1]),adiabat_bottom_K=float(ad[-1]),bottom_delta_percent=float(100*(ad[-1]/ref[-1]-1)),reference_thickness_m=href,adiabat_thickness_m=had,thickness_delta_m=had-href,adiabat_integral_relative_error=relerr,max_radiative_gradient=float(max(grad)),radiative_superadiabatic=bool(max(grad)>NABLA)))
 checks['anchor_continuity']=max_anchor_error<1e-12
 checks['adiabat_log_slope']=max_slope_error<1e-10
 checks['adiabat_analytic_integral_0p02percent']=max_integral_error<.0002
 convergence=None
 if not pilot:
  fine={(r['tint_K'],r['gamma'],r['anchor_bar']):r for r in rows if r['nlevel']==721};errors=[]
  for r in rows:
   if r['nlevel']==361:
    f=fine[(r['tint_K'],r['gamma'],r['anchor_bar'])]
    errors.extend([abs(r[k]/f[k]-1) for k in ('reference_thickness_m','adiabat_thickness_m')])
  convergence=max(errors);checks['361_to_721_thickness_change_under_0p1percent']=convergence<.001
 p=np.logspace(-6,3,61);ref=rad(p,25,.1);plot={'pressure_bar':p.tolist(),'reference_K':ref.tolist()}
 for anchor in (1,10,100):
  ta=float(rad(np.array([float(anchor)]),25,.1)[0]);curve=ref.copy();mask=p>anchor;curve[mask]=kernel.adiabat_temperature(p[mask],anchor,ta)
  validate(p,curve);require(np.array_equal(curve[~mask],ref[~mask]),'upper profile changed');plot[f'adiabat_{anchor}bar_K']=curve.tolist()
 checks['upper_profile_preserved']=True
 checks={k:bool(v) for k,v in checks.items()}
 require(all(checks.values()),'numerical acceptance failed: '+str(checks))
 output={'status':'controlled_sensitivity_only','phase':'pilot' if pilot else 'full','compute_seconds':time.perf_counter()-start,'parameters':{'teq_K':TEQ,'gravity_m_s2':G,'kappa_ir_cm2_g':KAPPA,'kappa_ir_m2_kg':KAPPA*.1,'mu_amu':MU,'nabla':NABLA,'levels':levels,'pressure_range_bar':[1e-6,1000],'opacity_table_used':False,'target_planet':None},'checks':checks,'diagnostics':{'saved_picaso_max_relative_error':reference_error,'max_adiabat_integral_relative_error':max_integral_error,'max_anchor_relative_error':max_anchor_error,'max_adiabat_slope_error':max_slope_error,'max_361_to_721_thickness_relative_change':convergence},'rows':rows,'plot':plot,'limitations':['Not RCE; constant opacity analytic reference is not a physical ground truth.','No target or observational constraint, no chemistry, no EOS coupling or composition inference.','Imposed joins are not predicted radiative-convective boundaries.','Constant-g ideal-gas thickness is not a planet radius; constant diatomic cp may fail at high T/P.']}
 json.dumps(output,allow_nan=False);return output
if __name__=='__main__':print(json.dumps(execute('--pilot' in sys.argv[1:]),separators=(',',':'),allow_nan=False))

