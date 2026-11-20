import sys, json, urllib.request, time

# uso: extract.py <url> <ids.json> <saida.json>
url, ids_f, out_f = sys.argv[1:4]
want = set(json.load(open(ids_f)))
dec = json.JSONDecoder()
req = urllib.request.Request(url, headers={'User-Agent': 'ifsuldeminas-class-project/1.0'})
resp = urllib.request.urlopen(req, timeout=120)
buf = ''
found = {}
total = 0
t0 = time.time()
started = False
pos = 0


def ws(s, i):
    while i < len(s) and s[i] in ' \n\r\t,':
        i += 1
    return i


while True:
    chunk = resp.read(8 * 1024 * 1024)
    if chunk:
        total += len(chunk)
        buf += chunk.decode('utf-8', errors='replace')
    elif not buf[pos:].strip():
        break
    progressed = True
    while progressed:
        progressed = False
        if not started:
            i = ws(buf, 0)
            if i < len(buf) and buf[i] == '{':
                pos = i + 1
                started = True
                progressed = True
            continue
        i = ws(buf, pos)
        if i >= len(buf) or buf[i] == '}':
            break
        try:
            key, j = dec.raw_decode(buf, i)
            j = ws(buf, j)
            if j >= len(buf):
                raise ValueError
            assert buf[j] == ':'
            j = ws(buf, j + 1)
            val, k = dec.raw_decode(buf, j)
        except (json.JSONDecodeError, ValueError):
            break
        if key in want:
            found[key] = val
        pos = k
        progressed = True
    buf = buf[pos:]
    pos = 0
    print(f'{total/1e6:.0f} MB lidos, {len(found)}/{len(want)} rotas, {time.time()-t0:.0f}s', flush=True)
    if len(found) == len(want) or not chunk:
        break
json.dump(found, open(out_f, 'w'))
print('fim', len(found), flush=True)
