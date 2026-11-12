import pathlib,json,math,bisect,csv,hashlib,struct
r=pathlib.Path('D:/Codex/downloads/subneptune-research-workflow');o=pathlib.Path('D:/Codex/downloads/toi732c-composition-constraints-20261112')
def load(path,official=False):
 ps=[];blocks=[];last=None
 with path.open() as f:
  if not official:next(f)
  for line in f:
   a=line.split()
   if not a:continue
   try:p,t,rho,g=map(float,a[:4])
   except ValueError:continue
   if official:p/=1e9;rho/=1000
   if p!=last:ps.append(p);blocks.append([]);last=p
   blocks[-1].append((t,rho,g))
 return ps,blocks
ps,blocks=load(r/'tabulated/AQUA.txt');op,ob=load(o/'literature/aqua_eos_pt_v1_0.dat',True)
def interp(ps,bs,p,t,log=False):
 i=max(0,min(len(ps)-2,bisect.bisect_right(ps,p)-1));v=[]
 for k in [i,i+1]:
  ts=[x[0] for x in bs[k]];j=max(0,min(len(ts)-2,bisect.bisect_right(ts,t)-1))
  assert ts[j]<=t<=ts[j+1]
  q=math.log10 if log else lambda x:x;b=(q(t)-q(ts[j]))/(q(ts[j+1])-q(ts[j]));v.append([(1-b)*bs[k][j][m]+b*bs[k][j+1][m] for m in [1,2]])
 q=math.log10 if log else lambda x:x;a=(q(p)-q(ps[i]))/(q(ps[i+1])-q(ps[i]));return [(1-a)*v[0][m]+a*v[1][m] for m in [0,1]]
rows=[]
for p in [.30402673,.74992743,1.4422569,3.5128559,30.9,68.7155,100,300,500,700,738.8308]:
 for t in [899.02447,1159.5197,1280,2082.6391,3000,4617.2827]:
  lr,lg=interp(ps,blocks,p,t);orr,og=interp(op,ob,p,t,True);gn=lg*p/t
  rows.append({'P_GPa':p,'T_K':t,'local_rho':lr,'official_rho':orr,'rho_rel_difference':(lr-orr)/orr,'local_nabla':gn,'official_nabla':og,'nabla_rel_difference':(gn-og)/og})
with (o/'official-local-comparison.csv').open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
s={'official_pressures':len(op),'official_block_lengths':sorted(set(map(len,ob))),'samples':len(rows),'max_abs_rho_rel_difference':max(abs(a['rho_rel_difference']) for a in rows),'max_abs_nabla_rel_difference':max(abs(a['nabla_rel_difference']) for a in rows),'largest_rho_difference':max(rows,key=lambda a:abs(a['rho_rel_difference'])),'largest_nabla_difference':max(rows,key=lambda a:abs(a['nabla_rel_difference'])),'source_units':'officialP/1e9,rho/1000;localdTdP*nativeP/T=dimensionlessnabla','source_interpolation':'official logP/logT bilinear;local linearP/linearT bilinear','scope':'66offgrid comparisons are corroboration,not exhaustive physical validation','hashes':{str(p.name):hashlib.sha256(p.read_bytes()).hexdigest() for p in [r/'tabulated/AQUA.txt',o/'literature/aqua_eos_pt_v1_0.dat']}}
(o/'official-local-comparison.json').write_text(json.dumps(s,indent=2));print(json.dumps(s))
q=[]
for p in [1.4422569,3.5128559]:
 for t in [1280*(1-1e-8),1280,1280*(1+1e-8)]:
  for e in ['Water_Brown','Water_sc_Mazevet','H2O_AQUA','water_default']:q.append([f'1280_{p}_{t}',p,t,e])
for p in [30.9*(1-1e-8),30.9*(1+1e-8),68.7155,100,300,500,700*(1-1e-8),700,700*(1+1e-8)]:
 for e in ['IceX','Water_sc_Mazevet','H2O_AQUA','water_default']:q.append([f'ice_{p}',p,2082.6391,e])
with (o/'queries/seams-input.csv').open('w',newline='') as f:w=csv.writer(f);w.writerow(['case_id','P_GPa','T_K','eos_id']);w.writerows(q)
print('probe query records',len(q),'distinct pairedPT',len(set((x[1],x[2]) for x in q)))
