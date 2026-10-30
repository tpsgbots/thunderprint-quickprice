"""Compile the quick-price page's JSON from the quote-tool's verified price data (ONE price pipeline).

  python build.py     # reads ../quote-tool/data/<slug>.json (read-only), writes site/data/<id>.json

Source of truth = quote-tool/data/*.json (format: quote-tool/SCHEMA.md), each proven exact against the live
calculator. After ANY price change: follow quote-tool/README.md first (rebuild + verify), then run this,
then parity.py, then commit + push this repo.
"""
import json, os, re, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
QT = os.path.join(HERE, '..', 'quote-tool', 'data')
OUT = os.path.join(HERE, 'site', 'data')

def qt(slug):
    return json.load(open(os.path.join(QT, slug + '.json'), encoding='utf-8'))

def addon(d, key):
    return next(a for a in d['addons'] if a['key'] == key)

def flat(fee):
    return fee.get('flat', 0) if isinstance(fee, dict) else (fee or 0)

def days(label):
    m = re.search(r'\(([^)]*)\)', label)
    return m.group(1).replace('Working Days', 'working days').replace('Working Day', 'working day') if m else ''

def speed(d):
    out = []
    for o in addon(d, 'speed')['options']:
        lab = o['label'].split(' (')[0]
        out.append({'id': {'Standard': 'std', 'Urgent': 'urgent', 'Super Urgent': 'super'}[lab], 'label': lab,
                    'days': days(o['label']), 'add': flat(o['fee'])})
    assert out[0]['id'] == 'std' and out[0]['add'] == 0, 'default speed must be first and free'
    return out

def proof(d):
    out = []
    for o in addon(d, 'proof')['options']:
        k = 'none' if o['label'].startswith('No') else 'digital' if o['label'].startswith('Digital') else 'physical'
        out.append({'id': k, 'label': {'none': 'No proof', 'digital': 'Digital proof (free)', 'physical': 'Physical proof'}[k],
                    'add': flat(o['fee']), 'days': 0 if k == 'none' else 1})
    return out

def designs(d):
    a = addon(d, 'designs')
    assert a['max'] == 25 and a['fee']['on'] == 'self'
    return a['fee']['bands']

def stickers():
    d = qt('custom-sized-waterproof-stickers')
    keys = [i['key'] for i in d['inputs']]
    assert keys == ['length_mm', 'width_mm', 'qty'], keys
    L, W, Q = (i['tiers'] for i in d['inputs'])
    assert len(d['grid']) == len(L) * len(W) * len(Q) and None not in d['grid']
    return {
        'id': 'waterproof-stickers', 'name': d['name'], 'ops_product': d['id'], 'url': d['url'],
        'source': f"quote-tool/data/custom-sized-waterproof-stickers.json (verified {d['verified']['date']})",
        'L': L, 'W': W, 'Q': Q, 'P': [int(p) for p in d['grid']],    # index = (li*len(W)+wi)*len(Q)+qi, same order as quote-tool
        'shapes': [o['label'] for o in addon(d, 'shape')['options']],
        'materials': [o['label'] for o in addon(d, 'material')['options']],
        'designs': designs(d), 'speed': speed(d), 'proof': proof(d),
        'ops_fields': {'L': 'aoptions[700]', 'W': 'aoptions[701]', 'q': 'aoptions[699]', 'designs': 'aoptions[705]',
                       'shape': 'aoptions[706]', 'material': 'aoptions[707]', 'speed': 'aoptions[702]', 'proof': 'aoptions[704]'},
    }

def namecards():
    d = qt('standard-namecards')
    keys = [i['key'] for i in d['inputs']]
    assert keys == ['material', 'sides', 'qty'], keys
    M, S = d['inputs'][0]['options'], d['inputs'][1]['options']
    Q = d['inputs'][2]['tiers']
    assert len(d['grid']) == len(M) * len(S) * len(Q) and None not in d['grid']
    corners = addon(d, 'corners')['options']
    return {
        'id': 'standard-namecards', 'name': d['name'], 'ops_product': d['id'], 'url': d['url'],
        'source': f"quote-tool/data/standard-namecards.json (verified {d['verified']['date']})",
        'M': M, 'M_label': M, 'M_popular': [M.index(d['inputs'][0]['default'])], 'S': S, 'Q': Q,
        'P': [int(p) for p in d['grid']],    # index = (mi*len(S)+si)*len(Q)+qi
        'sizes': sorted([o['label'] for o in addon(d, 'size')['options']], key=lambda s: '90' not in s),
        'corners_add': flat(next(o for o in corners if o['label'].startswith('4'))['fee']),
        'designs': designs(d), 'speed': speed(d), 'proof': proof(d),
        'ops_fields': {'size': 'prdsize', 'material': 'aoptions[403]', 'sides': 'aoptions[404]', 'corners': 'aoptions[400]',
                       'speed': 'aoptions[401]', 'proof': 'aoptions[628]', 'q': 'aoptions[630]', 'designs': 'aoptions[629]'},
    }

if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    for f in (stickers, namecards):
        d = f(); d['built'] = datetime.date.today().isoformat()
        json.dump(d, open(os.path.join(OUT, d['id'] + '.json'), 'w', encoding='utf-8'), separators=(',', ':'), ensure_ascii=False)
        print(d['id'], len(d['P']), 'cells <-', d['source'])
    st = os.path.join(OUT, 'status.json')
    if not os.path.exists(st):   # parity.py owns this file afterwards
        json.dump({k: {'ok': True, 'checked': None, 'note': 'not yet checked'} for k in ('waterproof-stickers', 'standard-namecards')}, open(st, 'w'), indent=1)
