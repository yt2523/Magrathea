import pathlib,json,hashlib,subprocess,csv,math,time
p=pathlib.Path('D:/Codex/downloads/toi732c-composition-constraints-20261112');r=pathlib.Path('D:/Codex/downloads/subneptune-research-workflow');s=p/'source';q=p/'queries'
# Restrict the isolated comparison fixture to rows with a verified common T axis. No values are changed.
f=s/'tabulated/AQUA.txt';original=(r/'tabulated/AQUA.txt').read_bytes();(p/'AQUA-original.sha256').write_text(hashlib.sha256(original).hexdigest())
lines=original.splitlines(keepends=True);retained=[line for line in lines[1:] if line.strip() and float(line.split()[1])<=10000]
blocks={}
for line in retained:
 a=line.split();blocks.setdefault(float(a[0]),[]).append(float(a[1]))
ref=next(iter(blocks.values()));assert all(ts==ref for ts in blocks.values());assert ref[-1]==10000
bounded=lines[0]+b''.join(retained);f.write_bytes(bounded)
meta={'original_repo_table_sha256':hashlib.sha256(original).hexdigest(),'bounded_fixture_sha256':hashlib.sha256(bounded).hexdigest(),'pressure_blocks':len(blocks),'T_rows_per_block':len(ref),'T_range':[ref[0],ref[-1]],'rows':len(retained),'rule':'keep exact original rows with T<=10000; no density/gradient/coordinate edits; canonical repo table untouched','reason':'strict tabledomain now rejects all runtime queries above verified common-axis region','scope':'isolated opt-in AQUA sensitivity only;not new scientificdefault'}
(p/'bounded-aqua-fixture.json').write_text(json.dumps(meta,indent=2))
c=json.loads((p/'contract.json').read_text());c['stage_A_fixture_amendment']=meta;(p/'contract.json').write_text(json.dumps(c,indent=2))
base=['wsl','--cd','/mnt/d/Codex/downloads/toi732c-composition-constraints-20261112/source','--exec','tests/native_water_audit']
def run(name,args):
 dest=q/(name+'.csv');assert not dest.exists();args=[str(x).replace('\\','/').replace('D:','/mnt/d') for x in args+[dest]];t=time.time();z=subprocess.run(base+args,capture_output=True,timeout=60)
 (p/(name+'.stdout.log')).write_bytes(z.stdout);(p/(name+'.stderr.log')).write_bytes(z.stderr);assert z.returncode==0,(name,z.returncode,z.stderr.decode());rows=list(csv.DictReader(dest.open()));assert rows;print(name,len(rows),round(time.time()-t,2),flush=True);return rows
qr=list(csv.DictReader((q/'seams-r2.csv').open()));assert len(qr)==60
assert all(a['domain']=='true' and int(a['rejected_delta'])==0 and math.isfinite(float(a['rho_g_cm3'])) for a in qr)
for a in qr:
 if a['requested_id']=='water_default':
  if a['case_id'].startswith('1280_'):assert a['selected_id']==('Water_sc_Mazevet' if float(a['T_K'])>1280 else 'Water_Brown')
 if a['requested_id']=='IceX':assert float(a['dTdP_K_per_GPa'])==0
summ={'query_records':len(qr),'distinct_query_PT':len(set((a['P_GPa'],a['T_K']) for a in qr)),'query_rejected':sum(int(a['rejected_delta']) for a in qr),'profile_rechecks':{}}
for case in ['grid14','grid20']:
 rr=run(case+'-stored-recheck-r2',['--profile',r/'research/unified-hhe-100bar-20261112/results'/case/'model.dat'])
 err=max(abs(float(a['rho_relerr'])) for a in rr);assert err<=2e-6 and all(a['domain']=='true' and int(a['rejected_delta'])==0 for a in rr)
 summ['profile_rechecks'][case]={'stored_rows':len(rr),'max_density_rel_error':err}
for pval in [1.4422569,3.5128559,700]:
 t=1280 if pval<10 else 2082.6391
 rr={a['requested_id']:a for a in qr if float(a['P_GPa'])==pval and float(a['T_K'])==t}
 old='Water_Brown' if pval<10 else 'IceX'
 b=float(rr[old]['rho_g_cm3']);m=float(rr['Water_sc_Mazevet']['rho_g_cm3']);aq=float(rr['H2O_AQUA']['rho_g_cm3']);summ[str(pval)]={'T_K':t,'rho_old':b,'rho_Mazevet':m,'rho_AQUA':aq,'inward_old_to_Mazevet_rel':(m-b)/b,'gradient_old':float(rr[old]['dTdP_K_per_GPa']),'gradient_Mazevet':float(rr['Water_sc_Mazevet']['dTdP_K_per_GPa']),'gradient_AQUA':float(rr['H2O_AQUA']['dTdP_K_per_GPa'])}
(p/'stageA-probe-summary.json').write_text(json.dumps(summ,indent=2));print(json.dumps(summ),flush=True)

