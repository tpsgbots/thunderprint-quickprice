import sys,re,json,time,urllib.request,urllib.parse,http.cookiejar
from bs4 import BeautifulSoup
UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126 Safari/537.36"
class Blocked(Exception): pass
def load(path):
    cj=http.cookiejar.CookieJar();op=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    op.addheaders=[('User-Agent',UA)]
    try: h=op.open('https://www.thunderprint.sg'+path,timeout=30).read().decode('utf8','replace')
    except urllib.error.HTTPError as e:
        if e.code==403: raise Blocked()
        raise
    s=BeautifulSoup(h,'html.parser')
    tok=s.find('meta',{'name':'csrf-token'})['content']
    form=None
    for f in s.find_all('form'):
        if f.find(attrs={'name':'prdsize'}) or f.find(attrs={'name':re.compile(r'^aoptions\[')}): form=f;break
    base={}
    for i in form.find_all('input'):
        n=i.get('name')
        if not n or i.get('type') in('submit','button','file'):continue
        if i.get('type') in('radio','checkbox') and not i.has_attr('checked'):continue
        base[n]=i.get('value','')
    sels={};labels={}
    for fg in form.find_all(class_='form-group'):
        lab=fg.find('label'); l=re.sub(r'\s+',' ',lab.get_text(' ',strip=True)) if lab else ''
        for x in fg.find_all(['select','input']):
            if x.get('name'): labels[x['name']]=l
    for sl in form.find_all('select'):
        n=sl.get('name')
        if not n:continue
        sels[n]=[(o.get('value'),o.get_text(strip=True)) for o in sl.find_all('option')]
        sel=sl.find('option',selected=True) or sl.find_all('option')[0]
        base[n]=sel.get('value')
    base['price_calculator']='newcalc';base['ops_csrf_token']=tok
    return op,base,sels,labels
def calc(op,base,path,cel=''):
    b=dict(base); b['cElement']=cel
    req=urllib.request.Request('https://www.thunderprint.sg/price_calculate.php',data=urllib.parse.urlencode(b).encode(),headers={'Content-Type':'application/x-www-form-urlencoded','X-Requested-With':'XMLHttpRequest','Referer':'https://www.thunderprint.sg'+path,'User-Agent':UA})
    try:
        t=op.open(req,timeout=30).read().decode('utf8','replace')
    except urllib.error.HTTPError as e:
        if e.code==403: raise Blocked()
        return 'HTTP%d'%e.code,None
    try: j=json.loads(t)
    except: return 'NOJSON',t[:100]
    return re.sub(r'\s+',' ',re.sub(r'<[^>]*>','',str(j.get('productpricetotal')))).strip(),j
if __name__=='__main__':
    p='/flyers-leaflets/custom-flyers/'
    op,base,sels,labels=load(p)
    print({k:(v,labels.get(k)) for k,v in base.items() if k not in('ops_csrf_token',)})
    base['aoptions[818]']='210';base['aoptions[819]']='148';base['aoptions[820]']='100';base['aoptions[821]']=sels['aoptions[821]'][1][0]
    t,j=calc(op,base,p); print(t); print(json.dumps(j)[:1500])
