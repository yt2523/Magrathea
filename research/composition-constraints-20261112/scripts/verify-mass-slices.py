import pathlib,json,subprocess,csv,math,hashlib,os
p=pathlib.Path('D:/Codex/downloads/toi732c-composition-constraints-20261112');b=p/'stageB';d=p/'mass-slices';data=json.loads((d/'mass-slice-attempts.json').read_text());allrows=[];points={'wet':{},'dry-rocky':{},'dry-iron':{}}
for rec in data['new_attempts']:
 path=d/rec['case'];assert rec['model_exists'] and rec['exit_code']==0;rt=json.loads((path/'runtime.json').read_text());assert rt['strict_table_audit'] and rt['rejected_table_queries']==0;assert rt['density_audit_counts'].get('Gas_iso',0)==0 and rt['density_audit_counts'].get('Gas',0)==0
 out=path/'checked.csv';assert not out.exists();z=subprocess.run(['wsl','--cd',(b/'source').as_posix().replace('D:','/mnt/d'),'--exec',(p/'source/tests/native_water_audit').as_posix().replace('D:','/mnt/d'),'--profile',(path/'model.dat').as_posix().replace('D:','/mnt/d'),out.as_posix().replace('D:','/mnt/d')],capture_output=True,timeout=40);assert z.returncode==0,(rec['case'],z.stderr.decode());rows=list(csv.DictReader(out.open()));assert rows
 err=max(abs(float(x['rho_relerr'])) for x in rows);assert err<=2e-6;assert all(x['domain']=='true' and int(x['rejected_delta'])==0 for x in rows)
 assert abs(float(rows[-1]['M_ME'])-rec['mass_ME'])/rec['mass_ME']<=1e-7 and float(rows[-1]['T_K'])==350
 if rec['family'].startswith('dry'):assert rt['density_audit_counts'].get('H2O_AQUA',0)==0 and not any(x['selected_id']=='H2O_AQUA' for x in rows)
 points[rec['family']][str(rec['mass_ME'])]={'R_RE':float(rows[-1]['R_RE']),'model_sha256':hashlib.sha256((path/'model.dat').read_bytes()).hexdigest(),'max_saved_density_error':err,'rows':len(rows),'case':rec['case']};allrows.extend(rows)
# Exact saved-byte+currentELF/cfg scenario identity reuse of previously verified noTP14 central wet point.
new=b/'results/notp14/model.dat';old=p/'results/grid14-aqua-commonaxis/model.dat';assert new.read_bytes()==old.read_bytes();points['wet']['8.04']={'R_RE':2.4251107,'case':'stageB/notp14','model_sha256':hashlib.sha256(new.read_bytes()).hexdigest(),'reuse':'samecurrentELF/noTPAQUAparameters; savedbytesmatchverifiedStageA'}
for fam,mp in points.items():
 lo=mp['7.56']['R_RE'];hi=mp['8.54']['R_RE'];mid=mp['8.04']['R_RE'];pred=lo+(.48/.98)*(hi-lo);mp['mass_interpolation_holdout']={'method':'endpointlinearM interpolation predicting independent centralmass run','predicted_R_RE':pred,'actual_R_RE':mid,'absolute_error_RE':abs(pred-mid),'pass_local_0.01RE_target':abs(pred-mid)<.01,'scope':'three representativecompositions only; notglobalerrorbound'}
summary={'status':'PASS_BOUNDED_MASS_SLICE_REPRESENTATIVES','points':points,'new_native_attempts':8,'exact_reused_central_wet':1,'new_saved_rows_checked':len(allrows),'max_density_error':max(abs(float(x['rho_relerr'])) for x in allrows),'scope':'conditionalmasssensitivitynotcompositionposterior; noTPinternalODEstatusunexposed; fullgridnotrun'};(d/'verification-summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary),flush=True)
os.environ['MPLCONFIGDIR']='D:/Codex/tmp/mpl-composition';os.environ['TEMP']=os.environ['TMP']='D:/Codex/tmp';import matplotlib;matplotlib.use('Agg');import matplotlib.pyplot as plt
fig,axs=plt.subplots(1,3,figsize=(12,4),layout='constrained');ms=[7.56,8.04,8.54]
for ax,(fam,mp),col in zip(axs,points.items(),['#1d70a2','#4b9460','#795492']):
 ys=[mp[str(m)]['R_RE'] for m in ms];ax.plot(ms,ys,'o-',color=col);ax.set_ylim(min(ys)-.018,max(ys)+.018);ax.set_xticks(ms);ax.set_xlabel('Mass (Earth masses)');ax.set_ylabel('Radius (Earth radii)');ax.set_title(fam+'; H/He=0.1%');ax.grid(alpha=.2)
 for m,y in zip(ms,ys):ax.annotate(f'{y:.5f}',(m,y),xytext=(0,8),textcoords='offset points',ha='center',fontsize=9)
fig.suptitle('Conditional mass sensitivity at fixed composition; connecting lines guide the eye',fontsize=11);fig.savefig(d/'mass-slices.png',dpi=180);print('saved mass-slices.png',flush=True)
