import pathlib,json,os
p=pathlib.Path('D:/Codex/downloads/toi732c-composition-constraints-20261112');d=p/'mass-slices';v=json.loads((d/'verification-summary.json').read_text());os.environ['MPLCONFIGDIR']='D:/Codex/tmp/mpl-composition';os.environ['TEMP']=os.environ['TMP']='D:/Codex/tmp';import matplotlib;matplotlib.use('Agg');import matplotlib.pyplot as plt
fig,axs=plt.subplots(1,3,figsize=(12,4.5),layout='constrained');ms=[7.56,8.04,8.54];titles=['Wet: nongas Fe/H2O=30/70','Dry: nongas Fe/silicate=1/3:2/3','Dry: nongas Fe=100%']
for ax,(fam,mp),col,title in zip(axs,v['points'].items(),['#1d70a2','#4b9460','#795492'],titles):
 ys=[mp[str(m)]['R_RE'] for m in ms];ax.plot(ms,ys,'o-',color=col);ax.set_xlim(7.4,8.7);ax.set_ylim(min(ys)-.018,max(ys)+.018);ax.set_xticks(ms);ax.set_xlabel('Mass (Earth masses)');ax.set_ylabel('Radius (Earth radii)');ax.set_title(title+'\nH/He=0.1%',fontsize=10);ax.grid(alpha=.2)
 for m,y in zip(ms,ys):ax.annotate(f'{y:.5f}',(m,y),xytext=(0,8),textcoords='offset points',ha='center',fontsize=9)
fig.suptitle('Conditional forward models: T0=350 K, P0=0.1 bar, prescribed 100-bar thermal break',fontsize=11);fig.supxlabel('Each panel has its own radius scale; connecting segments guide the eye, not a posterior',fontsize=9);fig.savefig(d/'mass-slices.png',dpi=180)
print('figurecaption completed')
