import sys, pickle
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

S = sys.argv[1]
sys.path.insert(0, S)
import heur2 as H

routes = H.load_routes()
d = pickle.load(open(S + '/resultados2.pkl', 'rb'))
res, seqs = d['res'], d['seqs']

# escolhe uma rota representativa: mediana de reducao da proposta
red = np.array([100 * (1 - b['travel'] / a['travel']) for a, b in zip(res['actual'], res['nn_tw'])])
ri = int(np.argsort(red)[len(red) // 2])
R = routes[ri]
fig, axs = plt.subplots(1, 2, figsize=(11, 5.2))
for ax, key, title in [(axs[0], 'actual', 'Sequência real do motorista'), (axs[1], 'nn_tw', 'Proposta (com janelas)')]:
    seq = seqs[key][ri]
    xy = R['xy'][seq]
    ax.plot(xy[:, 0], xy[:, 1], '-', color='#1f77b4', lw=1, alpha=.8, zorder=1)
    sc = ax.scatter(xy[1:, 0], xy[1:, 1], c=np.arange(1, len(seq)), cmap='viridis', s=14, zorder=2)
    ax.scatter([xy[0, 0]], [xy[0, 1]], marker='s', s=70, color='black', zorder=3)
    ax.set_title(f'{title}\n{H.travel(seq, R["T"]) / 60:.0f} min de deslocamento, {R["n"] - 1} paradas', fontsize=10)
    ax.ticklabel_format(useOffset=False, style='plain')
    ax.tick_params(axis='x', labelrotation=30, labelsize=8)
    ax.set_xlabel('longitude')
    ax.set_ylabel('latitude')
    ax.set_aspect(1 / np.cos(np.radians(34)))
    st_ = R['xy'][1:]
    mx, my = (st_[:, 0].max() - st_[:, 0].min()) * .08, (st_[:, 1].max() - st_[:, 1].min()) * .08
    ax.set_xlim(st_[:, 0].min() - mx, st_[:, 0].max() + mx)
    ax.set_ylim(st_[:, 1].min() - my, st_[:, 1].max() + my)
    ax.grid(alpha=.25)
fig.colorbar(sc, ax=axs, label='ordem de visita', shrink=.8)
plt.savefig(S + '/fig1_rota.png', dpi=170, bbox_inches='tight')
plt.close()
print('rota exemplo', ri, R['station'], R['date'], R['n'] - 1, red[ri])

names = [('actual', 'Sequência real\ndo motorista'), ('nn', 'Vizinho\nmais próximo'), ('ci', 'Inserção\nmais barata'),
         ('ci_ls', 'Inserção\n+ 2-opt + Or-opt'), ('nn_ls', 'NN + 2-opt\n+ Or-opt (proposta)'), ('nn_tw', 'Proposta com\njanelas')]
fig, ax = plt.subplots(figsize=(8.8, 4.2))
means = [np.mean([x['travel'] for x in res[k]]) for k, _ in names]
colors = ['#d62728', '#9aa0a6', '#9aa0a6', '#7fb3d5', '#1f77b4', '#0b4f8a']
b = ax.bar([n for _, n in names], means, color=colors)
for r_, m in zip(b, means):
    ax.text(r_.get_x() + r_.get_width() / 2, m + 2, f'{m:.0f}', ha='center', fontsize=9)
ax.set_ylabel('Tempo de deslocamento médio (min/rota)')
ax.set_ylim(0, max(means) * 1.15)
ax.grid(axis='y', alpha=.25)
plt.xticks(fontsize=8)
plt.tight_layout()
plt.savefig(S + '/fig2_tempo.png', dpi=170)
plt.close()

fig, ax = plt.subplots(figsize=(8.8, 3.6))
ax.hist(red, bins=20, color='#1f77b4', edgecolor='white')
ax.axvline(red.mean(), color='k', ls='--', lw=1)
ax.axvline(0, color='#d62728', lw=1)
ax.set_xlabel('Redução do tempo de deslocamento vs. sequência real (%)')
ax.set_ylabel('Nº de rotas')
plt.tight_layout()
plt.savefig(S + '/fig3_hist.png', dpi=170)
print('ok')
