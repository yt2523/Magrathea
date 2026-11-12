import os,json,pathlib,csv
os.environ['MPLCONFIGDIR']='D:/Codex/tmp/mpl-composition';os.environ['TEMP']=os.environ['TMP']='D:/Codex/tmp'
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
p=pathlib.Path('D:/Codex/downloads/toi732c-composition-constraints-20261112');r=pathlib.Path('D:/Codex/downloads/subneptune-research-workflow');v=json.loads((p/'verification-summary.json').read_text())
fig,(a,b)=plt.subplots(1,2,figsize=(12,4.8),layout='constrained')
for case,col in [('grid14','#1d70a2'),('grid20','#d8752a')]:
 for src,style,label in [(r/'research/unified-hhe-100bar-20261112/results'/case/'model.dat','--','stitched'),(p/'results'/(case+'-aqua-commonaxis')/'model.dat','-','AQUA')]:
  rows=[x.split(maxsplit=6) for x in src.read_text().splitlines()[1:] if x.strip()];w=[x for x in rows if x[6].startswith(('Water','Ice','H2O'))]
  a.plot([float(x[2]) for x in w],[float(x[5]) for x in w],style,color=col,label=case+' '+label)
a.axhline(1280,color='gray',lw=.8,alpha=.7);a.set_xscale('log');a.set_xlabel('Water-layer pressure (GPa)');a.set_ylabel('Temperature (K)');a.set_title('Water thermal structure: actual saved states');a.legend(fontsize=8)
labels=['Wet A\n0.1% H/He','Wet B\n0.3% H/He','Dry rocky\n0.1% H/He','Dry Fe\n0.1% H/He'];new=[v['profiles'][x]['R_RE'] for x in ['grid14-aqua-commonaxis','grid20-aqua-commonaxis','dry-rocky','dry-iron']];old=[2.3688889,2.5427244]
b.axhspan(2.28,2.49,color='gray',alpha=.18,label='Adopted R comparison interval');b.axhline(2.39,color='gray',lw=1,ls=':')
b.scatter(range(4),new,s=65,color=['#1d70a2','#d8752a','#4b9460','#795492'],label='New conditional runs',zorder=3)
b.scatter([0,1],old,s=65,facecolors='none',edgecolors='black',marker='s',label='Previous stitched-water runs',zorder=3)
for i,y in enumerate(new):b.annotate(f'{y:.5f}',(i,y),xytext=(0,9),textcoords='offset points',ha='center',fontsize=9)
b.set_xticks(range(4),labels);b.set_xlim(-.5,3.5);b.set_ylim(0,2.85);b.set_ylabel('Forward radius (Earth radii)');b.set_title('Representative checks; fixed mass 8.04 Earth masses');b.legend(fontsize=8,loc='lower left')
fig.suptitle('TEST ASSUMPTIONS: T0=350 K, P0=0.1 bar, prescribed 100-bar thermal break',fontsize=11)
fig.savefig(p/'stageA-wet-dry-comparison.png',dpi=180)
print('saved',str(p/'stageA-wet-dry-comparison.png'))
