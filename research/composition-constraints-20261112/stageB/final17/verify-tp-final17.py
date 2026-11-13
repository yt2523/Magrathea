import pathlib,sys,json,importlib.util
r=pathlib.Path('D:/Codex/downloads/subneptune-research-workflow');p=pathlib.Path('D:/Codex/downloads/toi732c-composition-constraints-20261112');b=p/'stageB';sys.path.insert(0,str(r/'tests'))
s=(r/'tests/check_pilot_model.py').read_text();assert s.count("allowed_water={")==1;s=s.replace("allowed_water={","allowed_water={'H2O_AQUA',",1);f=b/'fixed-check-aqua-model.py';f.write_text(s);spec=importlib.util.spec_from_file_location('aqua_acceptance',f);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
res={}
for case,frac in [('final14',[.2997,0,.6993,.001]),('final20',[.2991,0,.6979,.003]),('final20-tight',[.2991,0,.6979,.003])]:
 d=b/'results'/case;cfg={'fractions':frac,'mass_earth':8.04,'surface_pressure_cgs':100000};(d/'acceptance-input.json').write_text(json.dumps(cfg));out=m.verify(d/'model.dat.tp.json',d/'acceptance-input.json',b/'profile-example.csv',b/'source/tabulated/ChabrierHHe0275.txt');res[case]=out
 print(case,json.dumps(out),flush=True)
(b/'final17-tp-model-checks.json').write_text(json.dumps(res,indent=2))
