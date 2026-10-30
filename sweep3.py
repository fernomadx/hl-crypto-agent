"""Sweep focado BTC/ETH/SOL: grade densa + validação fora da amostra (OOS).
IS = primeiros 75% dos dias (~18m), OOS = últimos 25% (~6m). Base 1000 USDC,
long-only spot, fills no open seguinte, fee taker 0,045% + slippage 0,02%/lado.
Usage: python3 sweep3.py [--out results_big3.csv]
"""
import json, sys, time, math, urllib.request, datetime as dt
import grid_backtest as G

API=G.API; FEE=0.00045+0.0002
UNI=['BTC','ETH','SOL']; SPLIT=0.75

def nz(x): return x is not None
def fetch(coin,start,end,retries=8):
    import random
    out,cur,blank=[],start,0
    while cur<end:
        nxt=min(cur+365*24*3600*1000,end)
        try:
            b=G.post({'type':'candleSnapshot','req':{'coin':coin,'interval':'1d','startTime':cur,'endTime':nxt}})
        except Exception:
            b=[]
        if not b:
            blank+=1
            if blank<=retries:
                time.sleep(10+random.random()*5); continue
            break
        blank=0; out.extend(b); cur=b[-1]['T']+1
        if len(b)<2: break
        time.sleep(1)
    seen,clean=set(),[]
    for c in out:
        if c['t'] not in seen:
            seen.add(c['t']); clean.append({k:(float(c[k]) if k in 'ohlcv' else c[k]) for k in ('t','o','h','l','c','v')})
    clean.sort(key=lambda c:c['t']); return clean
def load(coin,path,days=800):
    import os as _os
    if _os.path.exists(path):
        d=json.load(open(path))
        if len(d)>200: print(coin,'cache',len(d),flush=True); return d
    end=int(time.time()*1000); start=end-days*24*3600*1000
    d=fetch(coin,start,end)
    json.dump(d,open(path,'w')); print(coin,'download',len(d),flush=True); return d

def obv(c,v):
    o=[0.0]*len(c)
    for i in range(1,len(c)):
        o[i]=o[i-1]+(v[i] if c[i]>c[i-1] else (-v[i] if c[i]<c[i-1] else 0.0))
    return o

def willr(h,l,c,p):
    o=[None]*len(c)
    for i in range(len(c)):
        if i>=p-1:
            hh=max(h[i-p+1:i+1]); ll=min(l[i-p+1:i+1]); o[i]=-100.0 if hh==ll else 100*(hh-c[i])/(hh-ll)-100 if False else 100-100*(c[i]-ll)/(hh-ll)-100 if False else None
    # simpler: %R = (hh - c)/(hh - ll) * -100
    for i in range(len(c)):
        if i>=p-1:
            hh=max(h[i-p+1:i+1]); ll=min(l[i-p+1:i+1]); o[i]=0.0 if hh==ll else (hh-c[i])/(hh-ll)*-100.0
    return o

def cci(h,l,c,p):
    tp=[(h[i]+l[i]+c[i])/3 for i in range(len(c))]; o=[None]*len(c)
    for i in range(len(c)):
        if i>=p-1:
            w=tp[i-p+1:i+1]; m=sum(w)/p; mad=sum(abs(x-m) for x in w)/p
            o[i]=0.0 if mad==0 else (tp[i]-m)/(0.015*mad)
    return o

def supertrend(h,l,c,ap,mult):
    n=len(c); hl2=[(h[i]+l[i])/2 for i in range(n)]
    tr=[(h[0]-l[0])]
    for i in range(1,n): tr.append(max(h[i]-l[i],abs(h[i]-c[i-1]),abs(l[i]-c[i-1])))
    a=[None]*n
    for i in range(n):
        if i>=ap-1: a[i]=sum(tr[i-ap+1:i+1])/ap
    fu,fd=[None]*n,[None]*n; t=[1]*n
    for i in range(n):
        if a[i] is None:
            if i>0: t[i]=t[i-1]
            continue
        bu,bl=hl2[i]+mult*a[i],hl2[i]-mult*a[i]
        fu[i]=bu if (i==0 or fu[i-1] is None or c[i-1]>fu[i-1]) else min(bu,fu[i-1])
        fd[i]=bl if (i==0 or fd[i-1] is None or c[i-1]<fd[i-1]) else max(bl,fd[i-1])
        if i>0:
            t[i]= -1 if (t[i-1]==1 and c[i]<fd[i]) else (1 if (t[i-1]==-1 and c[i]>fu[i]) else t[i-1])
    return t

def ind(df):
    O=[float(x['o']) for x in df];H=[float(x['h']) for x in df];L=[float(x['l']) for x in df]
    C=[float(x['c']) for x in df];V=[float(x['v']) for x in df]
    A={'C':C,'O':O,'H':H,'L':L,'V':V}
    for n in [3,5,8,10,12,15,20,21,30,34,40,50,55,60,100,150,200]: A[f'S{n}']=G.sma(C,n)
    for n in [5,8,12,19,20,21,34,50,55,100,200]: A[f'E{n}']=G.ema(C,n)
    for n in [2,3,4,5,7,10,14,21,28]: A[f'R{n}']=G.rsi(C,n)
    for n in [5,10,20,40,60,120]: A[f'DH{n}']=G.hilo(H,L,n,max); A[f'DL{n}']=G.hilo(H,L,n,min)
    A['SD10']=G.stdev(C,10);A['SD20']=G.stdev(C,20);A['SD30']=G.stdev(C,30);A['SD50']=G.stdev(C,50)
    for f,s,sg in [(12,26,9),(8,21,7),(12,21,9),(19,39,9),(8,17,9),(12,26,7),(24,52,9),(5,13,4),(6,19,5),(8,13,5),(21,34,8),(8,21,9),(8,26,7),(8,26,9),(12,21,7)]:
        m,ss=G.macd(C,f,s,sg); A[f'M{f}_{s}_{sg}']=m; A[f'Ms{f}_{s}_{sg}']=ss
    for k in [5,9,14,21,28]:
        K,D=G.stoch(H,L,C,k,3); A[f'K{k}']=K; A[f'D{k}']=D
    A['OBV']=obv(C,V)
    for n in [7,10,14,21,28]: A[f'W{n}']=willr(H,L,C,n)
    for n in [10,14,20,30]: A[f'CCI{n}']=cci(H,L,C,n)
    trs=[H[0]-L[0]]+[max(H[i]-L[i],abs(H[i]-C[i-1]),abs(L[i]-C[i-1])) for i in range(1,len(C))]
    for n in [7,10,14,21,28]: A[f'A{n}']=G.sma(trs,n)
    return A

def build(coin,A,C):
    S=lambda n:A[f'S{n}']; E=lambda n:A[f'E{n}']; R=lambda n:A[f'R{n}']
    CF=[]
    def add(fam,params,fn): CF.append({'fam':fam,'coin':coin,'params':params,'fn':fn,'name':fam+'_'+'_'.join(map(str,params))+'_'+coin})
    for f in [3,5,8,10,15,20,30,40,60]:
        for s in [50,100,150,200]:
            ff,ss=S(f),S(s); add('sma',[f,s],lambda i,ff=ff,ss=ss:(1 if (nz(ff[i]) and nz(ss[i]) and ff[i]>ss[i]) else (-1 if (nz(ff[i]) and nz(ss[i])) else 0)))
    for f in [5,8,12,21,34,55]:
        for s in [50,100,200]:
            ff,ss=E(f),E(s); add('ema',[f,s],lambda i,ff=ff,ss=ss:(1 if (nz(ff[i]) and nz(ss[i]) and ff[i]>ss[i]) else (-1 if (nz(ff[i]) and nz(ss[i])) else 0)))
    for p in [2,3,4,5,7,10,14,21,28]:
        for lo in [10,20,30]:
            for hi in [70,80,90]:
                rr=R(p); add('rsi_rev',[p,lo,hi],lambda i,rr=rr,lo=lo,hi=hi:(-1 if (nz(rr[i]) and rr[i]>hi) else (1 if (nz(rr[i]) and rr[i]<lo) else 0)))
    for p in [2,4,7,14,21,28]:
        for lo in [40,45,50]:
            rr=R(p); add('rsi_tr',[p,lo],lambda i,rr=rr,lo=lo:(1 if (nz(rr[i]) and rr[i]>lo+5) else (-1 if (nz(rr[i]) and rr[i]<lo) else 0)))
    for e in [5,10,20,40,60,120]:
        for x in [5,10,20]:
            hh,ll=A[f'DH{e}'],A[f'DL{x}']; add('donch',[e,x],lambda i,hh=hh,ll=ll:(1 if (nz(hh[i]) and C[i]>=hh[i]) else (-1 if (nz(ll[i]) and C[i]<=ll[i]) else 0)))
    for w in [10,20,30,50]:
        for k in [1.0,1.5,2.0,2.5,3.0]:
            sw,sd=A[f'S{w}'],A[f'SD{w}']; add('boll',[w,k],lambda i,sw=sw,sd=sd,k=k:(1 if (nz(sw[i]) and nz(sd[i]) and C[i]<sw[i]-k*sd[i]) else (-1 if (nz(sw[i]) and nz(sd[i]) and C[i]>sw[i]+k*sd[i]) else 0)))
    for f,s,sg in [(8,21,7),(12,26,9),(12,21,9),(19,39,9),(8,17,9),(12,26,7),(24,52,9),(5,13,4),(6,19,5),(8,13,5),(21,34,8)]:
        mm,ss=A[f'M{f}_{s}_{sg}'],A[f'Ms{f}_{s}_{sg}']; add('macd',[f,s,sg],lambda i,mm=mm,ss=ss:(1 if (nz(mm[i]) and nz(ss[i]) and mm[i]>ss[i]) else (-1 if (nz(mm[i]) and nz(ss[i])) else 0)))
    for lb in [5,7,14,21,30,45,60,90,120,180,240,365]:
        for hd in [7,14,30]:
            add('mom',[lb,hd],lambda i,lb=lb,hd=hd:(1 if (i>=lb and C[i]>C[i-lb] and (i-hd<0 or (i-hd>=lb and C[i-hd]>C[i-hd-lb]))) else 0))
    for an in [7,10,14,21,28]:
        for m in [1.5,2.0,3.0,4.0]:
            for en in [50,200]:
                aa,ee=A[f'A{an}'],E(en); add('atrtr',[an,m,en],lambda i,aa=aa,ee=ee,m=m:(1 if (nz(ee[i]) and C[i]>ee[i]) else 0))
    for kp in [5,9,14,21,28]:
        for hi in [70,75,80,85]:
            kk,dd=A[f'K{kp}'],A[f'D{kp}']; add('stoch',[kp,hi],lambda i,kk=kk,dd=dd,hi=hi:(1 if (nz(kk[i]) and nz(dd[i]) and kk[i]<20 and dd[i]<20) else (-1 if (nz(kk[i]) and kk[i]>hi) else 0)))
    for en in [12,50,200]:
        for b in [0.005,0.01,0.02,0.03,0.05]:
            ee=E(en); add('emad',[en,b],lambda i,ee=ee,b=b:(1 if (nz(ee[i]) and C[i]>ee[i]*(1+b)) else (-1 if (nz(ee[i]) and C[i]<ee[i]*(1-b)) else 0)))
    for f in [8,12,21,34]:
        for s in [50,100,200]:
            ff,ss=E(f),E(s); add('emarsi',[f,s],lambda i,ff=ff,ss=ss:(1 if (nz(ff[i]) and nz(ss[i]) and nz(R(14)[i]) and ff[i]>ss[i] and R(14)[i]>50) else (-1 if (nz(ff[i]) and nz(ss[i]) and ff[i]<ss[i]) else 0)))
    for f in [8,12]:
        for s in [21,26]:
            for sg in [7,9]:
                mm,ss=A[f'M{f}_{s}_{sg}'],A[f'Ms{f}_{s}_{sg}']; add('mach',[f,s,sg],lambda i,mm=mm,ss=ss:(1 if (nz(mm[i]) and nz(ss[i]) and mm[i]>ss[i]) else (-1 if (nz(mm[i]) and nz(ss[i])) else 0)))
    for en in [20,50]:
        for an in [14,21]:
            for k in [1.0,1.5,2.0,2.5,3.0]:
                ee,aa=E(en),A[f'A{an}']; add('kelt',[en,an,k],lambda i,ee=ee,aa=aa,k=k:(1 if (nz(ee[i]) and nz(aa[i]) and C[i]<ee[i]-k*aa[i]) else (-1 if (nz(ee[i]) and nz(aa[i]) and C[i]>ee[i]+k*aa[i]) else 0)))
    for an in [7,10,14,21,28]:
        for m in [1.5,2.0,2.5,3.0]:
            tt=supertrend(A['H'],A['L'],C,an,m); add('super',[an,m],lambda i,tt=tt:(1 if tt[i]==1 else (-1 if tt[i]==-1 else 0)))
    for f in [5,10,20]:
        for s in [50,100,200]:
            of,os=G.sma(A['OBV'],f),G.sma(A['OBV'],s); add('obv',[f,s],lambda i,of=of,os=os:(1 if (nz(of[i]) and nz(os[i]) and of[i]>os[i]) else (-1 if (nz(of[i]) and nz(os[i])) else 0)))
    for p in [7,10,14,21,28]:
        ww=A[f'W{p}']; add('willr',[p],lambda i,ww=ww:(1 if (nz(ww[i]) and ww[i]>-80 and (i==0 or not nz(ww[i-1]) or ww[i-1]<=-80)) else (-1 if (nz(ww[i]) and ww[i]<-20) else 0)))
    for p in [10,14,20,30]:
        cc=A[f'CCI{p}']; add('cci',[p],lambda i,cc=cc:(1 if (nz(cc[i]) and cc[i]<-100) else (-1 if (nz(cc[i]) and cc[i]>100) else 0)))
    for f in [10,20]:
        for s in [50,100,200]:
            for b in [0.01,0.03]:
                ff,ss=S(f),S(s); add('smah',[f,s,b],lambda i,ff=ff,ss=ss,b=b:(1 if (nz(ff[i]) and nz(ss[i]) and ff[i]>ss[i]*(1+b)) else (-1 if (nz(ff[i]) and nz(ss[i]) and ff[i]<ss[i]*(1-b)) else 0)))
    return CF

def ev(bt,px):
    eq,fees,mdd,n,w,l,pf=G.run(bt,px)
    return eq,fees,mdd,n,w,l,pf

def main():
    out=sys.argv[sys.argv.index('--out')+1] if '--out' in sys.argv else 'results_big3.csv'
    data={}
    for c in UNI: data[c]=load(c,f'daily_{c.lower()}_2y.json')
    CUT={c:int(len(data[c])*SPLIT) for c in UNI}
    allcf=[]
    for c in UNI:
        A=ind(data[c]); C=[float(x['c']) for x in data[c]]
        cf=build(c,A,C); print(c,len(cf),'combos',flush=True); allcf+=cf
    print('TOTAL',len(allcf),flush=True)
    import csv
    rows=[]
    for g in allcf:
        df=data[g['coin']]; cut=CUT[g['coin']]; px=df[:cut]
        if cut<200: rows.append((g['name'],g['fam'],g['coin'],'-'.join(map(str,g['params'])),len(df),0,0,0.0,0.0,0.0,0.0,0.0,'SHORT_IS')); continue
        bt=[g['fn'](i) for i in range(cut)]
        eq,fees,mdd,n,w,l,pf=ev(bt,px)
        wr=round(100*w/(w+l),1) if w+l else 0.0
        rows.append((g['name'],g['fam'],g['coin'],'-'.join(map(str,g['params'])),cut,n,wr,round((eq-1000)/10,2),round(mdd,2),round(fees,2),round(eq,2),pf,'OK'))
    ok=[r for r in rows if r[-1]=='OK']
    print('IS OK:',len(ok),'profitable:',sum(1 for r in ok if r[7]>0),flush=True)
    cand=sorted([r for r in ok if r[5]>=5 and r[7]>0 and (r[11]==float('inf') or r[11]>1.2)], key=lambda r:-r[7])[:40]
    print('OOS candidates:',len(cand),flush=True)
    oos=[]
    for g in [x for x in allcf if x['name'] in {c[0] for c in cand}]:
        df=data[g['coin']]; cut=CUT[g['coin']]
        bt=[g['fn'](i) for i in range(len(df))]
        sub=bt[cut:]; px=df[cut:]
        if len(sub)<20: continue
        eq,fees,mdd,n,w,l,pf=ev(sub,px)
        wr=round(100*w/(w+l),1) if w+l else 0.0
        oos.append((g['name'],n,wr,round((eq-1000)/10,2),round(mdd,2),round(fees,2),pf))
    oos_sorted=sorted(oos,key=lambda r:-r[3])
    print('OOS validated (top):',flush=True)
    for r in oos_sorted[:15]: print(f"  {r[3]:+.2f}% {r[0]} tr={r[1]} wr={r[2]}% dd={r[4]}% pf={r[6]}",flush=True)
    print('OOS profitable:',sum(1 for r in oos if r[3]>0),'/',len(oos),flush=True)
    with open(out,'w',newline='') as f:
        w=csv.writer(f); w.writerow(['name','family','coin','params','is_bars','trades_is','winrate_is','return_is_pct','maxdd_is_pct','fees_usd','equity_end','profit_factor','status'])
        w.writerows(rows)
    with open('oos_top40.csv','w',newline='') as f:
        w=csv.writer(f); w.writerow(['name','trades_oos','winrate_oos','return_oos_pct','maxdd_oos_pct','fees_oos_usd','profit_factor_oos'])
        w.writerows(oos_sorted)
    print('wrote',out,'oos_top40.csv',flush=True)

if __name__=='__main__': main()
