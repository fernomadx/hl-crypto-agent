import json, sys, datetime as dt
sys.path.insert(0, '/workspace/home/hl-bot')
from strategy import ema, rsi, atr, session_vwap
from backtest2 import run2
data={c:json.load(open(f'/workspace/home/hl-bot/{c}15m.json')) for c in ('btc','eth','sol')}
# mean-reversion: fade RSI extremes back toward VWAP, tight stop
import backtest2 as B
def run_mr(candles, start_equity=100.0):
    closes=[c['c'] for c in candles]
    e20,e50,r,a,vw=ema(closes,20),ema(closes,50),rsi(closes),atr(candles),session_vwap(candles)
    eq,trades,pos,cd=start_equity,[],None,0
    dk,ds,db=None,start_equity,False
    peak,maxdd=start_equity,0.0
    for i in range(51,len(candles)-1):
        c=candles[i]
        d=dt.datetime.fromtimestamp(c['t']/1000,dt.timezone.utc).date()
        if d!=dk: dk,ds,db=d,eq,False
        px=c['c']
        if pos:
            if pos['side']==1: hs,ht=c['l']<=pos['stop'],c['h']>=pos['tp']
            else: hs,ht=c['h']>=pos['stop'],c['l']<=pos['tp']
            to=i-pos['i']>=48
            xp=pos['stop'] if hs and not ht else (pos['tp'] if ht else px)
            if hs or ht or to:
                chg=(xp-pos['entry'])/pos['entry']*pos['side']
                gross=chg*pos['notional']; cost=pos['notional']*(B.FEE+B.SLIP)*2
                eq+=gross-cost; trades.append((gross-cost)/pos['risk_amt']); pos,cd=None,6
        else:
            if cd: cd-=1
            if (eq-ds)/ds<=-0.03: db=True
            if db or cd: peak=max(peak,eq);maxdd=min(maxdd,(eq-peak)/peak); continue
            dev=(px-vw[i])/px
            long_mr=r[i]<30 and dev<-0.003
            short_mr=r[i]>70 and dev>0.003
            side=1 if long_mr else (-1 if short_mr else 0)
            if side:
                entry=candles[i+1]['o']; sd=1.0*a[i]
                ra=eq*0.01; notional=max(B.MIN_NOTIONAL,min(ra/(sd/entry),eq))
                pos={'side':side,'entry':entry,'stop':entry-side*sd,'tp':entry+side*sd*1.5,'notional':notional,'risk_amt':ra,'i':i+1}
        peak=max(peak,eq);maxdd=min(maxdd,(eq-peak)/peak)
    w=[t for t in trades if t>0]; gw=sum(t for t in trades if t>0); gl=-sum(t for t in trades if t<=0)
    return {'n':len(trades),'win%':round(100*len(w)/len(trades),1) if trades else 0,'ret%':round(100*(eq/start_equity-1),2),'maxDD%':round(100*maxdd,2),'pf':round(gw/gl,2) if gl else None}
for c,d in data.items():
    print('MR',c,run_mr(d))
