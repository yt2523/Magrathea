#!/usr/bin/env python3
# SYNTHETIC_PROTOCOL_ONLY: not a planetary solver.
import sys,json,pathlib
cfg=pathlib.Path(sys.argv[2]);runtime=pathlib.Path(sys.argv[3]);o={}
for a in cfg.read_text().splitlines():
 if '=' in a and not a.lstrip().startswith('#'):
  k,v=a.split('=',1);o[k.strip()]=v.strip().strip('"')
m=[float(o[k]) for k in ['mass_of_core','mass_of_mantle','mass_of_hydro','mass_of_atm']];mass=sum(m);mode=o.get('MOCK_MODE','OK');d={'cli_exit_code':0,'strict_table_audit':True,'rejected_table_queries':0,'density_audit_counts':{'Fe_hcp':2,'Gas_hhe':3},'gradient_audit_counts':{},'SYNTHETIC_PROTOCOL_ONLY':True}
if m[2]>0:d['density_audit_counts']['H2O_AQUA']=1
if m[1]>0:d['density_audit_counts']['Si_Pv']=1
if mode=='GHOST_WATER':d['density_audit_counts']['Water_Brown']=1
runtime.write_text(json.dumps(d))
if mode=='NO_MODEL':sys.exit(0)
if mode=='HANG':
 import time;print('SYNTHETIC_SLEEP',flush=True);time.sleep(10)
out=pathlib.Path(o['output_file']);mass+=1 if mode=='WRONG_MASS' else 0;p=float(o['P_surface'])/1e10;temp=float(o['surface_temp']);out.write_text('Index Radius (earth) P (GPa) M (earth) Density (g cm^-3) T (K) Phase\n0 0 1 0 1 '+str(temp)+' SYNTHETIC_CENTER\n1 2 '+str(p)+' '+str(mass)+' 0.1 '+str(temp)+' SYNTHETIC, TEST ONLY\n')
