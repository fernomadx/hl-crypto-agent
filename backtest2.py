import json, sys, datetime as dt
sys.path.insert(0, '/workspace/home/hl-bot')
from strategy import ema, rsi, atr, session_vwap
FEE, SLIP, MIN_NOTIONAL = 0.00045, 0.0002, 10.0

def run2(candles, start_equity=100.0, risk_pct=0.01, atr_mult=2.0, rr=2.0, sides='both'):
    closes = [c['c'] for c in candles]
    e20, e50, r, a, vw = ema(closes,20), ema(closes,50), rsi(closes), atr(candles), session_vwap(candles)
    eq, pos, cooldown = start_equity, None, 0
    trades = []
    day_key, day_start, day_block = None, start_equity, False
    peak, maxdd = start_equity, 0.0
    for i in range(51, len(candles)):
        c = candles[i]
        d = dt.datetime.fromtimestamp(c['t']/1000, dt.timezone.utc).date()
        if d != day_key: day_key, day_start, day_block = d, eq, False
        px = c['c']
        if pos:
            if pos['side'] == 1:
                hit_stop, hit_tp = c['l'] <= pos['stop'], c['h'] >= pos['tp']
            else:
                hit_stop, hit_tp = c['h'] >= pos['stop'], c['l'] <= pos['tp']
            timeout = i - pos['i'] >= 96
            exit_px = pos['stop'] if hit_stop and not hit_tp else (pos['tp'] if hit_tp else px)
            if hit_stop or hit_tp or timeout:
                chg = (exit_px - pos['entry'])/pos['entry']*pos['side']
                gross = chg * pos['notional']
                cost = pos['notional']*(FEE+SLIP)*2
                eq += gross - cost
                trades.append((gross-cost)/pos['risk_amt'])
                pos, cooldown = None, 6
        else:
            if cooldown: cooldown -= 1
            if (eq-day_start)/day_start <= -0.03: day_block = True
            if day_block or cooldown or i+1 >= len(candles): 
                peak=max(peak,eq); maxdd=min(maxdd,(eq-peak)/peak); continue
            long_ok = closes[i]>e50[i] and e50[i]>e50[i-5] and e20[i]>e50[i] and 45<=r[i]<=68 and closes[i]>vw[i]
            short_ok = closes[i]<e50[i] and e50[i]<e50[i-5] and e20[i]<e50[i] and 32<=r[i]<=55 and closes[i]<vw[i]
            side = 0
            if sides in ('long','both') and long_ok: side = 1
            elif sides in ('short','both') and short_ok and side == 0: side = -1
            if side:
                entry = candles[i+1]['o']; stop_d = atr_mult*a[i]
                risk_amt = eq*risk_pct
                notional = max(MIN_NOTIONAL, min(risk_amt/(stop_d/entry), eq))
                pos = {'side':side,'entry':entry,
                       'stop':entry-side*stop_d,'tp':entry+side*stop_d*rr,
                       'notional':notional,'risk_amt':risk_amt,'i':i+1}
        peak=max(peak,eq); maxdd=min(maxdd,(eq-peak)/peak)
    wins=[t for t in trades if t>0]
    gw=sum(t for t in trades if t>0); gl=-sum(t for t in trades if t<=0)
    return {'n':len(trades),'win%':round(100*len(wins)/len(trades),1) if trades else 0,
            'ret%':round(100*(eq/start_equity-1),2),'maxDD%':round(100*maxdd,2),
            'pf':round(gw/gl,2) if gl else None,'end':round(eq,2)}

if __name__ == '__main__':
    data={c:json.load(open(f'/workspace/home/hl-bot/{c}15m.json')) for c in ('btc','eth','sol')}
    for sides in ('long','both'):
        for am,rr in ((2.0,2.0),(1.5,1.5),(2.5,2.0)):
            line=[]
            for c,d in data.items():
                r=run2(d,atr_mult=am,rr=rr,sides=sides)
                line.append(f"{c}:{r['ret%']}% n={r['n']} pf={r['pf']}")
            print(f"sides={sides} atr={am} rr={rr} |", ' '.join(line))
