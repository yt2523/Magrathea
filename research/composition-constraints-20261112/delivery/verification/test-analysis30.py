from pathlib import Path
import sys,json,numpy as np
p=Path('D:/Codex/downloads/toi732c-composition-constraints-20261112/stageC-driver');sys.path.insert(0,str(p/'source/run'));import composition_analysis_candidate as a
samples,sh=a.read_samples([p/'SYNTHETIC_PROTOCOL_TESTS/SYNTHETIC_plot.csv']);res=[]
assert len(samples)==60
assert [len(a.family_samples(samples,k)) for k in ['wet','dryrocky','dryFe']]==[36,36,12];res.append('pureFe shared edge included in both families')
U=np.array([[.2]]);V=np.array([[-1.5]]);r1=a.interpolate(samples,'wet',1,U,V);r2=a.interpolate(samples,'wet',2,U,V);assert abs(float(r2[0,0]-r1[0,0])-.1)<1e-12;expected=2+.2*1.5-.3*(.2-.5)+.1*.8;assert abs(float(r2[0,0])-expected)<1e-12;res.append('independent affine answer and exact mass separation')
x=a.interpolate(samples,'wet',3,np.array([[.5]]),np.array([[-3.]]));assert np.ma.getmaskarray(x)[0,0];res.append('failed vertex masked rather than bridged')
x=a.interpolate(samples,'wet',2,np.array([[.01]]),np.array([[-3.]]));assert np.ma.getmaskarray(x)[0,0];res.append('outside sampled domain masked')
g=a.grids(samples,'wet',[1,2,3],2,2,.1,.1,n=181);i=np.argmin(abs(g['V'][:,0]+3));j=np.argmin(abs(g['U'][0]-.5));assert np.ma.getmaskarray(g['band_mass'])[i,j];assert not np.ma.getmaskarray(g['band_radius'])[i,j];res.append('mass envelope uses common valid mask, central band independent')
U=np.array([[.95]]);V=np.array([[-1.8]]);v=[float(a.interpolate(samples,'wet',m,U,V)[0,0]) for m in [1,2,3]];assert not 1.9<=v[1]<=2.1 and min(v)<=2.1 and max(v)>=1.9;res.append('mass uncertainty compatibility beyond central radius band')
(p/'SYNTHETIC_PROTOCOL_TESTS/analysis30-results.json').write_text(json.dumps({'SYNTHETIC_ONLY':True,'passed':res},indent=2));print(json.dumps(res,indent=2))
