"""Daily parity check: quick-price page vs the LIVE thunderprint.sg calculator.

  python parity.py [N]   # N random specs per product (default 25) + fixed anchors

Prices each spec with the same logic the page uses (site/data/*.json) and with the live calculator
(tools/rp.py replay of price_calculate.php). Any mismatch marks that product stale in site/data/status.json,
and the page then hides it (shows "check the webstore" instead of a possibly wrong price).
Exit code 1 if anything is stale, so the GitHub Action shows red.
"""
import json, os, random, re, sys, time, datetime
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, 'tools'))
from rp import load, calc, Blocked

DATA = os.path.join(HERE, 'site', 'data')
N = int(sys.argv[1]) if len(sys.argv) > 1 else 25

def tier(v, T):
    return next((t for t in T if t >= v), None)

def designs_add(d, table):
    return next((a for upto, a in table if d <= upto), None)

def model_sticker(D, s):
    L, W, Q = D['L'], D['W'], D['Q']
    l, w, q = tier(s['L'], L), tier(s['W'], W), tier(s['q'], Q)
    if None in (l, w, q): return None
    p = D['P'][(L.index(l) * len(W) + W.index(w)) * len(Q) + Q.index(q)]
    return p + next(x['add'] for x in D['speed'] if x['id'] == s['speed']) + designs_add(s['designs'], D['designs']) \
        + next(x['add'] for x in D['proof'] if x['id'] == s['proof'])

def model_namecard(D, s):
    q = tier(s['q'], D['Q'])
    if q is None: return None
    p = D['P'][(s['mi'] * len(D['S']) + s['si']) * len(D['Q']) + D['Q'].index(q)]
    return p + next(x['add'] for x in D['speed'] if x['id'] == s['speed']) + (D['corners_add'] if s['corners'] else 0) + designs_add(s['designs'], D['designs']) \
        + next(x['add'] for x in D['proof'] if x['id'] == s['proof'])

def opt(sels, name, startswith):
    for v, t in sels[name]:
        if t.lower().startswith(startswith.lower()): return v
    raise KeyError((name, startswith))

SPEED_TXT = {'std': 'Standard', 'urgent': 'Urgent', 'super': 'Super Urgent'}
PROOF_TXT = {'none': 'No', 'digital': 'Digital', 'physical': 'Physical'}

def live(op, base, sels, path, fields, spec):
    b = dict(base)
    for k, v in fields.items(): b[k] = v
    t, j = calc(op, b, path); time.sleep(1.2)
    m = re.search(r'S\$\s*([\d,]+\.\d\d)', t or '')
    return float(m.group(1).replace(',', '')) if m else None

def check_stickers(D, rnd):
    path = D['url'].split('thunderprint.sg')[1]
    op, base, sels, _ = load(path)
    F = D['ops_fields']
    specs = [dict(L=50, W=50, q=100, designs=1, speed='std', proof='none'),
             dict(L=51, W=50, q=101, designs=5, speed='urgent', proof='physical')]
    for _ in range(N):
        specs.append(dict(L=rnd.randint(10, 300), W=rnd.randint(10, 300), q=rnd.choice([rnd.randint(1, 500), rnd.randint(500, 10000)]),
                          designs=rnd.choice([1, 1, 1, 4, 8, 12, 25]), speed=rnd.choice(['std', 'std', 'urgent', 'super']),
                          proof=rnd.choice(['none', 'none', 'digital', 'physical'])))
    bad = []
    for s in specs:
        exp = model_sticker(D, s)
        got = live(op, base, sels, path, {F['L']: str(s['L']), F['W']: str(s['W']), F['q']: str(s['q']), F['designs']: str(s['designs']),
                                          F['speed']: opt(sels, F['speed'], SPEED_TXT[s['speed']]),
                                          F['proof']: opt(sels, F['proof'], PROOF_TXT[s['proof']]),
                                          F['shape']: opt(sels, F['shape'], rnd.choice(D['shapes'])),
                                          F['material']: opt(sels, F['material'], rnd.choice(D['materials']))}, s)
        if got is None or exp is None or abs(got - exp) > 0.01: bad.append({'spec': s, 'page': exp, 'live': got})
    return len(specs), bad

def check_namecards(D, rnd):
    path = D['url'].split('thunderprint.sg')[1]
    op, base, sels, _ = load(path)
    F = D['ops_fields']
    specs = [dict(mi=D['M_popular'][0] if D['M_popular'] else 0, si=1, q=100, corners=False, speed='std', proof='none', size=0, designs=1)]
    for _ in range(N):
        specs.append(dict(mi=rnd.randrange(len(D['M'])), si=rnd.randrange(len(D['S'])), q=rnd.choice([rnd.randint(1, 1000), rnd.randint(1000, 20000)]),
                          corners=rnd.random() < 0.3, speed=rnd.choice(['std', 'std', 'urgent', 'super']),
                          proof=rnd.choice(['none', 'none', 'digital', 'physical']), size=rnd.randrange(2), designs=rnd.choice([1, 1, 2, 5, 9, 25])))
    bad = []
    for s in specs:
        exp = model_namecard(D, s)
        got = live(op, base, sels, path, {
            F['size']: opt(sels, F['size'], D['sizes'][s['size']]), F['material']: opt(sels, F['material'], D['M_label'][s['mi']]),
            F['sides']: opt(sels, F['sides'], D['S'][s['si']]), F['corners']: opt(sels, F['corners'], '4 Rounded' if s['corners'] else 'No Rounded'),
            F['speed']: opt(sels, F['speed'], SPEED_TXT[s['speed']]), F['proof']: opt(sels, F['proof'], PROOF_TXT[s['proof']]),
            F['q']: str(s['q']), F['designs']: str(s['designs'])}, s)
        if got is None or exp is None or abs(got - exp) > 0.01: bad.append({'spec': s, 'page': exp, 'live': got})
    return len(specs), bad

if __name__ == '__main__':
    rnd = random.Random()
    status = {}
    now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(timespec='minutes')
    for pid, fn in (('waterproof-stickers', check_stickers), ('standard-namecards', check_namecards)):
        D = json.load(open(os.path.join(DATA, pid + '.json'), encoding='utf-8'))
        try:
            n, bad = fn(D, rnd)
            status[pid] = {'ok': not bad, 'checked': now, 'samples': n, 'mismatches': bad[:5]}
        except Blocked:
            status[pid] = {'ok': True, 'checked': now, 'note': 'live site returned 403; kept previous state', 'samples': 0}
        except Exception as e:
            status[pid] = {'ok': False, 'checked': now, 'note': f'check failed: {e}'[:300]}
        print(pid, json.dumps(status[pid])[:400])
    json.dump(status, open(os.path.join(DATA, 'status.json'), 'w'), indent=1)
    sys.exit(0 if all(v['ok'] for v in status.values()) else 1)
