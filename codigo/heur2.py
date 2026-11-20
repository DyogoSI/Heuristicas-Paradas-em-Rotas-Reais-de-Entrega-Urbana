"""Heuristica de sequenciamento de paradas (Amazon Last Mile) - construcao + busca local."""
import json, math, random, datetime as dt
import numpy as np

import os
A = os.environ.get('DADOS_AMAZON', os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'dados'))


def isnan(x):
    return x is None or (isinstance(x, float) and math.isnan(x))


def load_routes(path=A):
    r = json.load(open(path + '/route_sel.json'))
    p = json.load(open(path + '/pkg_sel.json'))
    t = json.load(open(path + '/tt_sel.json'))
    s = json.load(open(path + '/actual_sequences.json'))
    out = []
    for rid, meta in r.items():
        stops = meta['stops']
        # indice 0 = estacao (deposito)
        station = [c for c, v in stops.items() if v['type'] == 'Station'][0]
        codes = [station] + [c for c in stops if c != station]
        idx = {c: i for i, c in enumerate(codes)}
        n = len(codes)
        T = np.zeros((n, n))
        for a in codes:
            row = t[rid][a]
            for b in codes:
                T[idx[a], idx[b]] = row[b]
        serv = np.zeros(n)
        vol = np.zeros(n)
        ws = np.full(n, -np.inf)
        we = np.full(n, np.inf)
        d0 = dt.datetime.strptime(meta['date_YYYY_MM_DD'] + ' ' + meta['departure_time_utc'], '%Y-%m-%d %H:%M:%S')
        for c, pk in p[rid].items():
            if c not in idx:
                continue
            i = idx[c]
            for pid, v in pk.items():
                serv[i] += v['planned_service_time_seconds']
                dm = v['dimensions']
                vol[i] += dm['depth_cm'] * dm['height_cm'] * dm['width_cm']
                tw = v['time_window']
                if not isnan(tw['start_time_utc']):
                    a = (dt.datetime.strptime(tw['start_time_utc'], '%Y-%m-%d %H:%M:%S') - d0).total_seconds()
                    b = (dt.datetime.strptime(tw['end_time_utc'], '%Y-%m-%d %H:%M:%S') - d0).total_seconds()
                    ws[i] = max(ws[i], a)
                    we[i] = min(we[i], b)
        act = s[rid]['actual']
        order = sorted(act, key=lambda c: act[c])
        actual = [idx[c] for c in order]
        assert actual[0] == 0 and len(actual) == n
        xy = np.array([[stops[c]['lng'], stops[c]['lat']] for c in codes])
        out.append(dict(id=rid, station=meta['station_code'], date=meta['date_YYYY_MM_DD'], cap=meta['executor_capacity_cm3'],
                        n=n, T=T, serv=serv, vol=vol, ws=ws, we=we, actual=actual, xy=xy))
    return out


# ---------------- avaliacao ----------------
def travel(seq, T):
    return float(sum(T[seq[i], seq[i + 1]] for i in range(len(seq) - 1)))


def windows(seq, R):
    """retorna (n de paradas com janela violada, n de paradas com janela)."""
    t = 0.0
    viol = 0
    for i in range(1, len(seq)):
        a, b = seq[i - 1], seq[i]
        t += R['serv'][a] + R['T'][a, b]
        if t < R['ws'][b]:
            t = R['ws'][b]
        if t > R['we'][b] + 1e-9:
            viol += 1
    nw = int(np.sum(np.isfinite(R['we'][1:])))
    return viol, nw


def total_time(seq, R):
    return travel(seq, R['T']) + float(R['serv'][seq].sum())


# ---------------- construcao ----------------
def nearest_neighbor(T):
    n = len(T)
    seq = [0]
    un = set(range(1, n))
    while un:
        c = seq[-1]
        j = min(un, key=lambda j: T[c, j])
        seq.append(j)
        un.remove(j)
    return seq


def cheapest_insertion(T):
    """Insercao mais barata (path aberto, deposito fixo no inicio)."""
    n = len(T)
    # semente: parada mais proxima do deposito
    seq = [0, int(np.argmin(T[0, 1:])) + 1]
    un = set(range(1, n)) - {seq[1]}
    while un:
        best = None
        for j in un:
            for m in range(len(seq)):
                q = seq[m]
                if m + 1 < len(seq):
                    r = seq[m + 1]
                    c = T[q, j] + T[j, r] - T[q, r]
                else:
                    c = T[q, j]
                if best is None or c < best[0]:
                    best = (c, j, m + 1)
        _, j, pos = best
        seq.insert(pos, j)
        un.remove(j)
    return seq


# ---------------- melhoria ----------------
def two_opt(seq, T, R=None):
    p = seq[:]
    n = len(p)
    v0 = windows(p, R)[0] if R else 0
    imp = True
    while imp:
        imp = False
        arr = np.array(p)
        fw = np.concatenate([[0], np.cumsum(T[arr[:-1], arr[1:]])])
        rv = np.concatenate([[0], np.cumsum(T[arr[1:], arr[:-1]])])
        for i in range(1, n - 1):
            for j in range(i + 1, n):
                old = T[p[i - 1], p[i]] + (fw[j] - fw[i])
                new = T[p[i - 1], p[j]] + (rv[j] - rv[i])
                if j < n - 1:
                    old += T[p[j], p[j + 1]]
                    new += T[p[i], p[j + 1]]
                if new < old - 1e-9:
                    cand = p[:i] + p[i:j + 1][::-1] + p[j + 1:]
                    if R:
                        v1 = windows(cand, R)[0]
                        if v1 > v0:
                            continue
                        v0 = v1
                    p = cand
                    imp = True
                    break
            if imp:
                break
    return p


def or_opt(seq, T, R=None):
    p = seq[:]
    n = len(p)
    v0 = windows(p, R)[0] if R else 0
    imp = True
    while imp:
        imp = False
        for L in (1, 2, 3):
            for i in range(1, n - L + 1):
                j = i + L - 1
                seg0, seg1 = p[i], p[j]
                prev = p[i - 1]
                nxt = p[j + 1] if j + 1 < n else None
                gain = T[prev, seg0] + (T[seg1, nxt] - T[prev, nxt] if nxt is not None else 0.0)
                rest = p[:i] + p[j + 1:]
                best = None
                for m in range(len(rest)):
                    q = rest[m]
                    if m + 1 < len(rest):
                        r = rest[m + 1]
                        c = T[q, seg0] + T[seg1, r] - T[q, r]
                    else:
                        c = T[q, seg0]
                    if c < gain - 1e-9 and (best is None or c < best[0]):
                        best = (c, m)
                if best is not None and rest[best[1]] != prev:
                    m = best[1]
                    cand = rest[:m + 1] + p[i:j + 1] + rest[m + 1:]
                    if R:
                        v1 = windows(cand, R)[0]
                        if v1 > v0:
                            continue
                        v0 = v1
                    p = cand
                    imp = True
                    break
                if best is not None and rest[best[1]] == prev:
                    continue
            if imp:
                break
    return p


def local_search(seq, T, R=None):
    p = seq
    while True:
        c0 = travel(p, T)
        p = two_opt(p, T, R)
        p = or_opt(p, T, R)
        if travel(p, T) > c0 - 1e-9:
            return p


def long_search(T, iters, seed, start):
    """ILS: perturbacao double-bridge + busca local, a partir da melhor solucao conhecida."""
    rng = random.Random(seed)
    best = local_search(start, T)
    bc = travel(best, T)
    cur, cc = best, bc
    n = len(T)
    for _ in range(iters):
        a, b, c = sorted(rng.sample(range(1, n), 3))
        cand = cur[:a] + cur[b:c] + cur[a:b] + cur[c:]
        cand = local_search(cand, T)
        cv = travel(cand, T)
        if cv < cc - 1e-9:
            cur, cc = cand, cv
            if cv < bc:
                best, bc = cand, cv
    return best


def nn_windows(R, slack=900.0):
    """Vizinho mais proximo com urgencia: se alguma parada com janela esta prestes a vencer, vai primeiro nela."""
    T = R['T']
    n = len(T)
    seq = [0]
    un = set(range(1, n))
    t = 0.0
    while un:
        c = seq[-1]
        urgent = None
        for j in un:
            if np.isfinite(R['we'][j]):
                arr = t + R['serv'][c] + T[c, j]
                sl = R['we'][j] - arr
                if sl < slack and (urgent is None or sl < urgent[0]):
                    urgent = (sl, j)
        j = urgent[1] if urgent else min(un, key=lambda j: T[c, j])
        t += R['serv'][c] + T[c, j]
        if t < R['ws'][j]:
            t = R['ws'][j]
        seq.append(j)
        un.remove(j)
    return seq
