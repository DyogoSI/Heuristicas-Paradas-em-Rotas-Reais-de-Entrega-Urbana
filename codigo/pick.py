import json
r=json.load(open('route_data.json'))
ids=[k for k,v in r.items() if v['route_score']=='High' and v['station_code'].startswith('DLA')][:100]
json.dump(ids,open('ids.json','w'))
sub={k:r[k] for k in ids}
json.dump(sub,open('route_sel.json','w'))
import collections
print(len(ids),collections.Counter(r[k]['station_code'] for k in ids),sum(len(r[k]['stops']) for k in ids))
