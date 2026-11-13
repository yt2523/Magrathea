#!/usr/bin/env python3
# SYNTHETIC_PROTOCOL_ONLY: validates no physical EOS.
import pathlib,sys,csv
inp=pathlib.Path(sys.argv[2]);out=pathlib.Path(sys.argv[3]);h='index,R_RE,P_GPa,M_ME,T_K,rho_saved,rho_recomputed,rho_relerr,phase,selected_id,domain,thermal_code,dTdP_K_per_GPa,nabla,rejected_delta'.split(',')
with out.open('w',newline='') as f:
 w=csv.writer(f);w.writerow(h)
 for line in inp.read_text().splitlines()[1:]:
  a=line.split(maxsplit=6);i,r,p,m,rho,t=map(float,a[:6]);w.writerow([int(i),r,p,m,t,rho,rho,0,a[6],'Fe_hcp','true',0,0,0,0])
