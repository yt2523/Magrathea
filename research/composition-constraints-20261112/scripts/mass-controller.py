import pathlib,json,hashlib,subprocess,time
p=pathlib.Path('D:/Codex/downloads/toi732c-composition-constraints-20261112');b=p/'stageB';dest=p/'mass-slices';dest.mkdir();bin=b/'source/native_audit';assert hashlib.sha256(bin.read_bytes()).hexdigest()=='1fad237de60ab2fd029c9ea64e7d51b86b246e7b8a8caad14ce14f5751b939cd'
obs={'source':'Bonfanti etal2024,A&A682A66,doi10.1051/0004-6361/202348180','M_ME':8.04,'M_minus':.48,'M_plus':.50,'R_RE':2.39,'R_minus':.11,'R_plus':.10,'mass_vector':[7.56,8.04,8.54],'joint_covariance':'notavailableinthisstage','purpose':'threeconditionalmasssensitivityslices;notcompositionposterior'};(dest/'observation-input.json').write_text(json.dumps(obs,indent=2))
cache={'wet_8.04':{'path':str(b/'results/notp14'),'binary_sha256':hashlib.sha256(bin.read_bytes()).hexdigest(),'reason':'identical currentbinary/nonTPAQUAscenario/inputmasses; outputpathnotphysicalinput'}};records=[]
for fam,template in [('wet',p/'results/grid14-aqua-commonaxis/run.cfg'),('dry-rocky',p/'results/dry-rocky/run.cfg'),('dry-iron',p/'results/dry-iron/run.cfg')]:
 for mass in [7.56,8.04,8.54]:
  if fam=='wet' and mass==8.04:continue
  case=f'{fam}_M{mass:.2f}';d=dest/case;d.mkdir(exist_ok=False);base=template.read_text();lines=[]
  for line in base.splitlines():
   key,sep,val=line.partition('=')
   if key.startswith('mass_of_') and sep:line=key+'='+format(float(val)*mass/8.04,'.17g')
   if key=='output_file':line='output_file="'+(d/'model.dat').as_posix().replace('D:','/mnt/d')+'"'
   if key=='verbose':line='verbose=false'
   lines.append(line)
  text='\n'.join(lines)+'\n';(d/'run.cfg').write_text(text)
  c=json.loads((p/'contract.json').read_text());assert sum(x['stage']=='C' for x in c['native_attempts'])<12;rec={'case':case,'stage':'C','family':fam,'mass_ME':mass,'status':'STARTED','binary_sha256':hashlib.sha256(bin.read_bytes()).hexdigest(),'config_sha256':hashlib.sha256(text.encode()).hexdigest()};c['native_attempts'].append(rec);(p/'contract.json').write_text(json.dumps(c,indent=2));t=time.time()
  try:
   with (d/'stdout.log').open('wb') as a,(d/'stderr.log').open('wb') as z:res=subprocess.run(['wsl','--cd',(b/'source').as_posix().replace('D:','/mnt/d'),'--exec',bin.as_posix().replace('D:','/mnt/d'),'--run',(d/'run.cfg').as_posix().replace('D:','/mnt/d'),(d/'runtime.json').as_posix().replace('D:','/mnt/d')],stdout=a,stderr=z,timeout=180)
   rec.update(status='COMPLETED',exit_code=res.returncode,seconds=time.time()-t,model_exists=(d/'model.dat').is_file())
   if (d/'runtime.json').is_file():rec['runtime']=json.loads((d/'runtime.json').read_text())
   if (d/'model.dat').is_file():
    data=[x.split(maxsplit=6) for x in (d/'model.dat').read_text().splitlines()[1:] if x.strip()];rec.update(R_RE=float(data[-1][1]),saved_rows=len(data))
  except subprocess.TimeoutExpired:rec.update(status='TIMEOUT',seconds=time.time()-t)
  (d/'attempt.json').write_text(json.dumps(rec,indent=2));(p/'contract.json').write_text(json.dumps(c,indent=2));records.append(rec);print(json.dumps({k:v for k,v in rec.items() if k!='runtime'}),flush=True)
(dest/'mass-slice-attempts.json').write_text(json.dumps({'mass_vector':obs['mass_vector'],'new_attempts':records,'reused_exact_identity':cache},indent=2))
