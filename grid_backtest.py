"""Sweep sistemático de estratégias (paper/research, Hyperliquid, stdlib only).
Base 1000 USDC, dados diários reais 2 anos, fills no open seguinte, fees taker
0,045% + slippage 0,02% por lado. Long-only spot, all-in/all-out com compounding.
Usage: python3 grid_backtest.py [--days 730] [--out results_grid.csv]
"""
import json, sys, time, math, urllib.request, datetime as dt

API='https://api.hyperliquid.xyz/info'
FEE=0.00045+0.0002
UNI=['BTC','ETH','SOL','HYPE','DOGE','AVAX','LINK','ARB','SUI','APT']

def post(p,retries=6):
    import random
    for a in range(retries):
        try:
            r=urllib.request.Request(API,data=json.dumps(p).encode(),headers={'Content-Type':'application/json'})
            with urllib.request.urlopen(r,timeout=60) as x: out=json.load(x)
            time.sleep(0.3); return out
        except Exception:
            if a==retries-1: raise
            time.sleep(2*(a+1)+random.random())

def candles(coin,interval,start,end):
    out,cur=[],start
    while cur<end:
        nxt=min(cur+30*24*3600*1000,end)
        b=post({'type':'candleSnapshot','req':{'coin':coin,'interval':interval,'startTime':cur,'endTime':nxt}})
        if not b: break
        out.extend(b); cur=b[-1]['T']+1
        if len(b)<2: break
    seen,clean=set(),[]
    for c in out:
        if c['t'] not in seen:
            seen.add(c['t']); clean.append({k:(float(c[k]) if k in 'ohlcv' else c[k]) for k in ('t','o','h','l','c','v')})
    clean.sort(key=lambda c:c['t']); return clean

def sma(v,n):
    o=[None]*len(v); s=0.0
    for i,x in enumerate(v):
        s+=x
        if i>=n: s-=v[i-n]
        if i>=n-1: o[i]=s/n
    return o

def ema(v,n):
    o=[None]*len(v); k=2/(n+1); e=None
    for i,x in enumerate(v):
        e=x if e is None else x*k+e*(1-k); o[i]=e
    return o

def rsi(cl,n=14):
    o=[None]*len(cl); g=l=0.0
    for i in range(1,len(cl)):
        ch=cl[i]-cl[i-1]; g=(g*(n-1)+max(ch,0))/n if i>1 else max(ch,0); l=(l*(n-1)+max(-ch,0))/n if i>1 else max(-ch,0)
        if i>=n: o[i]=100.0 if l==0 else 100-100/(1+g/l)
    return o

def hilo(h,l,n,fn):
    o=[None]*len(h)
    for i in range(len(h)):
        if i>=n-1: o[i]=fn((h if fn==max else l)[max(0,i-n+1):i+1])
    return o

def stdev(v,n):
    o=[None]*len(v)
    for i in range(len(v)):
        if i>=n-1:
            w=v[i-n+1:i+1]; m=sum(w)/n; o[i]=math.sqrt(sum((x-m)**2 for x in w)/n)
    return o

def macd(cl,f,s,sig):
    ef,es=ema(cl,f),ema(cl,s); m=[None if ef[i] is None or es[i] is None else ef[i]-es[i] for i in range(len(cl))]
    base=[x for x in m if x is not None]; sg=ema(base,sig) if base else []
    return m,([None]*(len(m)-len(sg))+sg)

def stoch(h,l,c,kp,dp):
    K=[None]*len(c)
    for i in range(len(c)):
        if i>=kp-1:
            hh=max(h[i-kp+1:i+1]); ll=min(l[i-kp+1:i+1]); K[i]=50.0 if hh==ll else 100*(c[i]-ll)/(hh-ll)
    base=[x for x in K if x is not None]; D=([None]*(len(K)-len(base)+0) if False else [])
    ds=sma(base,dp); D=[None]*(len(K)-len(ds))+ds
    return K,D

def run(bt,px,fee=FEE):
    eq=1000.0; peak=1000.0; mdd=0.0; pos=None; wins=losses=0; fees=0.0; n=0
    gw=gl=0.0
    for i in range(1,len(bt)-1):
        sig=bt[i]; op=px[i+1]['o']
        if pos is None and sig==1:
            pos=op; c=eq*fee; eq-=c; fees+=c; n+=1
        elif pos is not None and sig==-1:
            r=(op-pos)/pos; pnl=r*eq; eq+=pnl; c=eq*fee; eq-=c; fees+=c
            if pnl>0: wins+=1; gw+=pnl
            else: losses+=1; gl+=-pnl
            pos=None
        peak=max(peak,eq); mdd=max(mdd,(peak-eq)/peak*100)
    if pos is not None:
        r=(px[-1]['c']-pos)/pos; pnl=r*eq; eq+=pnl; c=eq*fee; eq-=c; fees+=c
        if pnl>0: wins+=1; gw+=pnl
        else: losses+=1; gl+=-pnl
        pos=None
        peak=max(peak,eq); mdd=max(mdd,(peak-eq)/peak*100)
    pf=round(gw/gl,2) if gl>0 else (float('inf') if gw>0 else 0.0)
    return eq,fees,mdd,n,wins,losses,pf

def build(df):
    o=[float(c['o']) for c in df]; h=[float(c['h']) for c in df]; l=[float(c['l']) for c in df]; c=[float(c['c']) for c in df]
    return o,h,l,c

def sig_list(n,fn):
    return [fn(i) for i in range(n)]

CFGS=[]
def add(fam,coin,params,fn):
    CFGS.append({'fam':fam,'coin':coin,'params':params,'fn':fn,
                 'name':fam+'_'+'_'.join(str(v) for v in params)+'_'+coin})

def spec(coin,O,H,L,C):
    S5=sma(C,5);S10=sma(C,10);S15=sma(C,15);S20=sma(C,20);S30=sma(C,30);S40=sma(C,40)
    S50=sma(C,50);S100=sma(C,100);S200=sma(C,200)
    E8=ema(C,8);E12=ema(C,12);E19=ema(C,19);E21=ema(C,21);E34=ema(C,34)
    E50=ema(C,50);E100=ema(C,100);E200=ema(C,200)
    R7=rsi(C,7);R14=rsi(C,14);R21=rsi(C,21);R28=rsi(C,28)
    D20h=hilo(H,L,20,max);D20l=hilo(H,L,20,min);D40h=hilo(H,L,40,max);D40l=hilo(H,L,40,min)
    D60h=hilo(H,L,60,max);D60l=hilo(H,L,60,min)
    SD20=stdev(C,20);SD30=stdev(C,30)
    M1,M1s=macd(C,12,26,9);M2,M2s=macd(C,8,21,7);M3,M3s=macd(C,12,21,9);M4,M4s=macd(C,19,39,9)
    K9,D9=stoch(H,L,C,9,3);K14,D14=stoch(H,L,C,14,3)
    A14=None
    trs=[]
    for i in range(len(C)):
        if i==0: trs.append(H[i]-L[i])
        else: trs.append(max(H[i]-L[i],abs(H[i]-C[i-1]),abs(L[i]-C[i-1])))
    A14=sma(trs,14);A21=sma(trs,21)
    N=len(C)
    def nz(x): return x is not None
    # 1) sma_cross 5x3=15
    for f,ff in [(5,S5),(10,S10),(15,S15),(20,S20),(30,S30)]:
        for s,ss in [(50,S50),(100,S100),(200,S200)]:
            add('sma',coin,(f,s),lambda i,f=f,s=s,ff=ff,ss=ss:(1 if (nz(ff[i]) and nz(ss[i]) and ff[i]>ss[i]) else (-1 if (nz(ff[i]) and nz(ss[i])) else 0)))
    # 2) ema_cross 3x2=6
    for f,ff in [(8,E8),(12,E12),(21,E21)]:
        for s,ss in [(50,E50),(100,E100)]:
            add('ema',coin,(f,s),lambda i,f=f,s=s,ff=ff,ss=ss:(1 if (nz(ff[i]) and nz(ss[i]) and ff[i]>ss[i]) else (-1 if (nz(ff[i]) and nz(ss[i])) else 0)))
    # 3) rsi_revert 3x2x2=12
    for p,rr in [(7,R7),(14,R14),(21,R21)]:
        for lo in [20,30]:
            for hi in [70,80]:
                add('rsi_rev',coin,(p,lo,hi),lambda i,p=p,lo=lo,hi=hi,rr=rr:(-1 if (nz(rr[i]) and rr[i]>hi) else (1 if (nz(rr[i]) and rr[i]<lo) else 0)))
    # 4) rsi_trend 4
    for p,rr in [(7,R7),(14,R14),(21,R21),(28,R28)]:
        add('rsi_tr',coin,(p,),lambda i,rr=rr:(1 if (nz(rr[i]) and rr[i]>55) else (-1 if (nz(rr[i]) and rr[i]<45) else 0)))
    # 5) donchian 3x2=6
    for w,hh,ll in [(20,D20h,D20l),(40,D40h,D40l),(60,D60h,D60l)]:
        for x in [10,20]:
            xl=hilo(L,L,x,min)
            add('donch',coin,(w,x),lambda i,w=w,x=x,hh=hh,ll=ll,xl=xl:(1 if (nz(hh[i]) and C[i]>=hh[i]) else (-1 if (nz(xl[i]) and C[i]<=xl[i]) else 0)))
    # 6) boll_revert 2x3=6
    for w,sw in [(20,S20),(30,S30)]:
        for k in [1.5,2.0,2.5]:
            sd=SD20 if w==20 else SD30
            add('boll',coin,(w,k),lambda i,w=w,k=k,sw=sw,sd=sd:(1 if (nz(sw[i]) and nz(sd[i]) and C[i]<sw[i]-k*sd[i]) else (-1 if (nz(sw[i]) and nz(sd[i]) and C[i]>sw[i]+k*sd[i]) else 0)))
    # 7) macd 4
    for nm,mm,ss in [('12269',M1,M1s),('8217',M2,M2s),('12219',M3,M3s),('19399',M4,M4s)]:
        add('macd',coin,(nm,),lambda i,mm=mm,ss=ss:(1 if (nz(mm[i]) and nz(ss[i]) and mm[i]>ss[i]) else (-1 if (nz(mm[i]) and nz(ss[i])) else 0)))
    # 8) momentum lb x hold 4x3=12
    for lb in [30,60,90,180]:
        for hd in [7,14,30]:
            add('mom',coin,(lb,hd),lambda i,lb=lb,hd=hd:(1 if (i>=lb and C[i]>C[i-lb] and (i-hd)<0 or (i>=lb+hd and C[i-hd]>C[i-hd-lb])) else 0))
    # 9) atr trailing stop + ema filter: 2x2x2=8
    for an,aa in [(14,A14),(21,A21)]:
        for m in [2.0,3.0]:
            for en,ee in [(50,E50),(200,E200)]:
                add('atrtr',coin,(an,m,en),lambda i,aa=aa,m=m,ee=ee:(1 if (nz(ee[i]) and C[i]>ee[i]) else 0))
    # 10) stoch revert 2x2=4 (k x overbought level)
    for kp,kk,dd in [(9,K9,D9),(14,K14,D14)]:
        for hi in [75,80]:
            add('stoch',coin,(kp,hi),lambda i,kk=kk,dd=dd,hi=hi:(1 if (nz(kk[i]) and nz(dd[i]) and kk[i]<20 and dd[i]<20) else (-1 if (nz(kk[i]) and kk[i]>hi) else 0)))
    # 11) sma hold variants 5x3=15
    for f,ff in [(5,S5),(10,S10),(15,S15),(20,S20),(30,S30)]:
        for s,ss in [(50,S50),(100,S100),(200,S200)]:
            add('smah',coin,(f,s),lambda i,ff=ff,ss=ss:(1 if (nz(ff[i]) and nz(ss[i]) and ff[i]>ss[i]*1.01) else (-1 if (nz(ff[i]) and nz(ss[i]) and ff[i]<ss[i]*0.99) else 0)))
    # 12) close-vs-ema distance 3
    for en,ee in [(20,E12),(50,E50),(200,E200)]:
        add('emad',coin,(en,),lambda i,ee=ee:(1 if (nz(ee[i]) and C[i]>ee[i]*1.02) else (-1 if (nz(ee[i]) and C[i]<ee[i]*0.98) else 0)))
    # total per coin: 15+6+12+4+6+6+4+12+8+4+15+3 = 95 -> +5 donchian exits
    for w,hh in [(20,D20h),(40,D40h),(60,D60h)]:
        for x in [10,20]:
            pass
    # +5: ema12 vs ema50/100/200 + rsi gate
    for s,ss in [(50,E50),(100,E100),(200,E200)]:
        add('emarsi',coin,(12,s),lambda i,ss=ss:(1 if (nz(E12[i]) and nz(ss[i]) and nz(R14[i]) and E12[i]>ss[i] and R14[i]>50) else (-1 if (nz(E12[i]) and nz(ss[i]) and E12[i]<ss[i]) else 0)))
    for s,ss in [(50,E50),(100,E100)]:
        add('emarsi',coin,(21,s),lambda i,ss=ss:(1 if (nz(E21[i]) and nz(ss[i]) and nz(R14[i]) and E21[i]>ss[i] and R14[i]>50) else (-1 if (nz(E21[i]) and nz(ss[i]) and E21[i]<ss[i]) else 0)))

def main():
    days=int(sys.argv[sys.argv.index('--days')+1]) if '--days' in sys.argv else 730
    out=sys.argv[sys.argv.index('--out')+1] if '--out' in sys.argv else 'results_grid.csv'
    end=int(time.time()*1000); start=end-days*24*3600*1000
    t0=dt.datetime.now(dt.timezone.utc).strftime('%H:%M:%SZ')
    print(f'start {t0} days={days} universe={UNI}',flush=True)
    data={}
    for c in UNI:
        data[c]=candles(c,'1d',start,end)
        print(f'{c}: {len(data[c])} daily bars',flush=True)
    global CFGS; CFGS=[]
    PX={}
    for c in UNI:
        O,H,L,C=build(data[c]); PX[c]=data[c]; spec(c,O,H,L,C)
    print('configs:',len(CFGS),flush=True)
    rows=[]
    for g in CFGS:
        df=data[g['coin']]; n=len(df)
        if n<220:
            rows.append((g['name'],g['fam'],g['coin'],'-'.join(map(str,g['params'])),n,0,0,0.0,0.0,0.0,0.0,0.0,'SHORT_DATA')); continue
        bt=[g['fn'](i) for i in range(n)]
        eq,fees,mdd,tr,w,l,pf=run(bt,df)
        wr=round(100*w/(w+l),1) if w+l else 0.0
        rows.append((g['name'],g['fam'],g['coin'],'-'.join(map(str,g['params'])),n,tr,wr,round((eq-1000)/10,2),round(mdd,2),round(fees,2),round(eq,2),pf,'OK'))
    import csv
    with open(out,'w',newline='') as f:
        w=csv.writer(f); w.writerow(['name','family','coin','params','bars','trades','winrate_pct','return_pct','maxdd_pct','fees_usd','equity_end','profit_factor','status'])
        w.writerows(rows)
    ok=[r for r in rows if r[-1]=='OK']; pos=sorted([r for r in ok if r[7]>0],key=lambda r:-r[7])
    rob=sorted([r for r in pos if r[5]>=10 and r[11]>1.0],key=lambda r:(-r[7]))
    print(f'TOTAL={len(rows)} OK={len(ok)} PROFITABLE={len(pos)}',flush=True)
    for r in pos[:15]:
        print(f"  {r[7]:+.2f}% {r[0]} tr={r[5]} wr={r[6]}% dd={r[8]}% pf={r[11]} fees=${r[9]}",flush=True)
    print('ROBUST (tr>=10, pf>1):',len(rob),flush=True)
    for r in rob[:10]:
        print(f"  {r[7]:+.2f}% {r[0]} tr={r[5]} wr={r[6]}% dd={r[8]}% pf={r[11]}",flush=True)
    neg=sorted([r for r in ok if r[7]<=0],key=lambda r:r[7])
    for r in neg[:5]:
        print(f"  {r[7]:+.2f}% {r[0]} tr={r[5]} wr={r[6]}% dd={r[8]}%",flush=True)

if __name__=='__main__': main()
