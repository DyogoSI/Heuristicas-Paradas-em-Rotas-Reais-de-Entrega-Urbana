import sys, json, time, pickle
import numpy as np

S = sys.argv[1]
sys.path.insert(0, S)
import heur2 as H

routes = H.load_routes()
print('rotas', len(routes), 'paradas', sum(R['n'] - 1 for R in routes))
methods = [
    ('actual', 'Sequência real do motorista (referência)', lambda R: R['actual']),
    ('nn', 'Vizinho mais próximo', lambda R: H.nearest_neighbor(R['T'])),
    ('nn_ls', 'Vizinho mais próximo + 2-opt + Or-opt (proposta)', lambda R: H.local_search(H.nearest_neighbor(R['T']), R['T'])),
    ('ci', 'Inserção mais barata', lambda R: H.cheapest_insertion(R['T'])),
    ('ci_ls', 'Inserção mais barata + 2-opt + Or-opt', lambda R: H.local_search(H.cheapest_insertion(R['T']), R['T'])),
    ('nn_tw', 'Proposta com proteção de janelas de horário', lambda R: H.local_search(H.nn_windows(R), R['T'], R)),
]
res = {k: [] for k, _, _ in methods}
seqs = {k: [] for k, _, _ in methods}
for ri, R in enumerate(routes):
    for k, _, f in methods:
        t0 = time.perf_counter()
        seq = f(R)
        ms = (time.perf_counter() - t0) * 1000
        assert sorted(seq) == list(range(R['n'])) and seq[0] == 0
        v, nw = H.windows(seq, R)
        res[k].append(dict(travel=H.travel(seq, R['T']) / 60, total=H.total_time(seq, R) / 3600, viol=v, nw=nw, ms=ms,
                           occ=100 * R['vol'].sum() / R['cap']))
        seqs[k].append(seq)
    if ri % 10 == 0:
        print(ri, {k: round(res[k][-1]['travel'], 1) for k in res}, flush=True)

# busca mais longa (ILS) em 12 rotas para estimar o gap
gaps = []
long_res = []
for ri in range(0, 100, 8)[:12]:
    R = routes[ri]
    t0 = time.perf_counter()
    b = H.long_search(R['T'], 30, ri, seqs['nn_ls'][ri])
    ms = (time.perf_counter() - t0) * 1000
    base = res['nn_ls'][ri]['travel']
    lng = H.travel(b, R['T']) / 60
    gaps.append(100 * (base / lng - 1))
    long_res.append(dict(route=ri, n=R['n'], base=base, long=lng, ms=ms))
    print('ils', ri, R['n'], round(base, 1), round(lng, 1), round(gaps[-1], 2), round(ms / 1000, 1), flush=True)

pickle.dump(dict(res=res, seqs=seqs, gaps=gaps, long=long_res), open(S + '/resultados2.pkl', 'wb'))
for k, name, _ in methods:
    a = res[k]
    print(k, round(np.mean([x['travel'] for x in a]), 1), round(np.mean([x['ms'] for x in a]), 1),
          sum(x['viol'] for x in a), sum(x['nw'] for x in a))
red = [100 * (1 - b['travel'] / a['travel']) for a, b in zip(res['actual'], res['nn_ls'])]
print('red vs real', np.mean(red), min(red), max(red))
red2 = [100 * (1 - b['travel'] / a['travel']) for a, b in zip(res['actual'], res['nn_ls'])]
print('nn_ls vs real', np.mean(red2))
print('gap', np.mean(gaps), max(gaps))
