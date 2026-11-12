import pathlib,json,subprocess,csv,math,hashlib,struct,bisect
p=pathlib.Path('D:/Codex/downloads/toi732c-composition-constraints-20261112');v=p/'verification';v.mkdir(exist_ok=False)
base=['wsl','--cd','/mnt/d/Codex/downloads/toi732c-composition-constraints-20261112/source','--exec','tests/native_water_audit']
results=[]
def check(name,mode,text,expected):
 i=v/(name+('.dat' if mode=='--profile' else '.csv'));o=v/(name+'-output.csv');i.write_text(text)
 z=subprocess.run(base+[mode,i.as_posix().replace('D:','/mnt/d'),o.as_posix().replace('D:','/mnt/d')],capture_output=True,timeout=40);rec={'test':name,'exit_code':z.returncode,'expected':expected,'passed':(z.returncode==0)==(expected==0),'stderr':z.stderr.decode()};results.append(rec);assert rec['passed'],rec
 return list(csv.DictReader(o.open())) if z.returncode==0 else None
h='case_id,P_GPa,T_K,eos_id\n'
for n,t in [('query-empty',h+'\n'),('query-badP',h+'x,nan,1280,H2O_AQUA\n'),('query-unknown',h+'x,3.5,1280,bogus\n'),('query-quoted',h+'"x",3.5,1280,H2O_AQUA\n'),('query-emptycase',h+',3.5,1280,H2O_AQUA\n')]:check(n,'--query',t,1)
for n,t in [('profile-empty','Index header\n\n'),('profile-badheader','Bad header\n0 0 1 0 1 350 Fe hcp (Smith)\n'),('profile-fractional-index','Index header\n0.5 0 1 0 1 350 Fe hcp (Smith)\n')]:check(n,'--profile',t,1)
a=check('table-golden-and-domain','--query',h+'node,1.0009e-7,100,H2O_AQUA\noutside,1,50000,H2O_AQUA\n',0)
assert abs(float(a[0]['rho_g_cm3'])-.93304)<1e-12 and abs(float(a[0]['dTdP_K_per_GPa'])-3.7224)<1e-12
assert a[1]['domain']=='false' and math.isnan(float(a[1]['rho_g_cm3'])) and int(a[1]['rejected_delta'])==0
inp=v/'table-golden-and-domain.csv';out=v/'table-golden-and-domain-output.csv';before=out.read_bytes();z=subprocess.run(base+['--query',inp.as_posix().replace('D:','/mnt/d'),out.as_posix().replace('D:','/mnt/d')],capture_output=True,timeout=40);assert z.returncode!=0 and out.read_bytes()==before;results.append({'test':'overwrite-refusal','exit_code':z.returncode,'passed':True})
profiles={}
for case in ['grid14-aqua-commonaxis','grid20-aqua-commonaxis','grid14-aqua-commonaxis-tight','grid20-aqua-commonaxis-tight','dry-rocky','dry-iron','dry-rocky-tight','dry-iron-tight']:
 inp=p/'results'/case/'model.dat';assert inp.exists(),case;out=p/'results'/case/'checked.csv';assert not out.exists()
 z=subprocess.run(base+['--profile',inp.as_posix().replace('D:','/mnt/d'),out.as_posix().replace('D:','/mnt/d')],capture_output=True,timeout=40);assert z.returncode==0,(case,z.stderr.decode());rows=list(csv.DictReader(out.open()));assert rows
 err=max(abs(float(a['rho_relerr'])) for a in rows);assert err<2e-6;assert all(a['domain']=='true' and int(a['rejected_delta'])==0 and math.isfinite(float(a['rho_recomputed'])) and math.isfinite(float(a['dTdP_K_per_GPa'])) for a in rows)
 rt=json.loads((inp.parent/'runtime.json').read_text());assert rt['strict_table_audit'] and rt['rejected_table_queries']==0
 assert all(rt['density_audit_counts'].get(k,0)==0 for k in ['Gas_iso','Gas'])
 gas=[a for a in rows if a['selected_id'] in ['Gas_hhe','Gas_hhe_iso100']];water=[a for a in rows if a['selected_id']=='H2O_AQUA']
 if case.startswith('dry'):assert not water and not any('Water' in a['selected_id'] or a['selected_id'].startswith('Ice') for a in rows);assert not any(rt['density_audit_counts'].get(k,0)>0 for k in ['H2O_AQUA','Water_Brown','Water_sc_Mazevet','IceX'])
 low=[a for a in gas if a['selected_id']=='Gas_hhe_iso100'];assert max(abs(float(a['T_K'])-350)/350 for a in low)<2e-6
 assert abs(float(rows[-1]['M_ME'])-8.04)/8.04<1e-7 and abs(float(rows[-1]['P_GPa'])-1e-5)/1e-5<1e-7
 phases={a['phase'] for a in rows};profiles[case]={'rows':len(rows),'R_RE':float(rows[-1]['R_RE']),'max_density_relerr':err,'phase_labels':sorted(phases),'max_saved_T':max(float(a['T_K']) for a in rows),'water_T_range':[min(float(a['T_K']) for a in water),max(float(a['T_K']) for a in water)] if water else None,'rho_surface':float(rows[-1]['rho_saved'])}
 print(case,profiles[case]['R_RE'],len(rows),err,flush=True)
for basecase in ['grid14-aqua-commonaxis','grid20-aqua-commonaxis','dry-rocky','dry-iron']:
 a=profiles[basecase]['R_RE'];b=profiles[basecase+'-tight']['R_RE'];e=abs(a-b)/b;assert e<1e-5;profiles[basecase]['tight_radius_rel_difference']=e
summary={'fixed_guard_tests':results,'profiles':profiles,'stored_rows_checked':sum(x['rows'] for x in profiles.values()),'diagnostic_sha256':hashlib.sha256((p/'source/tests/native_water_audit.cpp').read_bytes()).hexdigest(),'scope':'saved-state/strict-domain/tolerance checks only; internalODEstatus/fitresidual not exposed;no scientificdefault approval'}
(p/'verification-summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps({'guards':len(results),'stored_rows_checked':summary['stored_rows_checked'],'all_radius_pairs_passed':True}),flush=True)
