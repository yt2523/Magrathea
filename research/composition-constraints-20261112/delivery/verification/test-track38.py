from pathlib import Path
import sys,numpy as np,json,copy
p=Path('D:/Codex/downloads/toi732c-composition-constraints-20261112/stageC-driver');sys.path.insert(0,str(p/'source/run'));import plot_compositions as a;s,sh=a.read_samples([p/'SYNTHETIC_PROTOCOL_TESTS/SYNTHETIC_plot.csv']);a.apply_phase_groups(s,None)
U,V=np.meshgrid([.2,.8],[-2.5,-1.5]);r=a.interpolate_track(s,'dryrocky',2,U,V);expected=2+.2*(V+3)-.3*(U-.5);assert np.max(abs(r-expected))<1e-11,(r,expected)
lo=a.interpolate_track(s,'dryrocky',1,U,V);assert np.max(abs(r-lo-.1))<1e-11
bad=a.interpolate_track(s,'wet',3,np.array([[.5]]),np.array([[-3.]]));assert np.ma.getmaskarray(bad)[0,0]
out=a.interpolate_track(s,'wet',2,np.array([[.01]]),np.array([[-3.]]));assert np.ma.getmaskarray(out)[0,0]
# all water nodes assigned dense except lowgasu.1 vapor; transition mustbe withheld
for z in s.values():z['phase_group']='no_water' if z['fWater']==0 else 'vapor' if z['fGas']==.0001 and abs(z['fFe']/(1-z['fGas'])-.1)<1e-10 else 'dense_fluid'
hole=a.interpolate_track(s,'wet',2,np.array([[.2]]),np.array([[-3.5]]));assert np.ma.getmaskarray(hole)[0,0]
g=a.grids(s,'dryrocky',[1,2,3],2,2,.1,.1,n=31,method='track-pchip');assert g['R_central'].count()>0
(p/'SYNTHETIC_PROTOCOL_TESTS/track38-results.json').write_text(json.dumps({'SYNTHETIC_ONLY':True,'tests_passed':['affine analytic answer','exact M separation','failed gas point barrier','out of domain masked','vapor/dense crossing withheld','grids optionalmethod integrated']},indent=2));print('PASS 6 track38 analytic/protection checks')
