"""Paper backtest: cross-sectional funding carry (Keel-style), stdlib only.
Every 24h: rank universe by trailing-24h avg funding; short 2 richest, long 2
cheapest; equal notional; hold 24h. Costs: taker 0.045%/fill x4. Funding
accrues hourly on notional. No leverage (1x each leg).
Usage: python3 funding_carry.py [--days 90]
"""
import json, sys, time, urllib.request, datetime as dt

API = 'https://api.hyperliquid.xyz/info'
UNI = ['BTC','ETH','SOL','HYPE','DOGE','AVAX','LINK','ARB','SUI','APT']
FEE = 0.00045  # taker per fill
TOPN = 2

def post(p, timeout=60, retries=6):
    import random
    for a in range(retries):
        try:
            req = urllib.request.Request(API, data=json.dumps(p).encode(),
                                         headers={'Content-Type':'application/json'})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                out = json.load(r)
            time.sleep(0.4)
            return out
        except Exception as e:
            if a == retries-1: raise
            time.sleep(2*(a+1) + random.random())
    raise RuntimeError('unreachable')

def funding_history(coin, start, end):
    out, cur = [], start
    while cur < end:
        nxt = min(cur + 30*24*3600*1000, end)
        b = post({'type':'fundingHistory','coin':coin,'startTime':cur,'endTime':nxt})
        if not b: break
        out.extend(b); cur = b[-1]['time'] + 1
        if len(b) < 2: break
    return sorted(out, key=lambda x: x['time'])

def candles(coin, interval, start, end):
    out, cur = [], start
    while cur < end:
        nxt = min(cur + 30*24*3600*1000, end)
        b = post({'type':'candleSnapshot','req':{'coin':coin,'interval':interval,
                 'startTime':cur,'endTime':nxt}})
        if not b: break
        out.extend(b); cur = b[-1]['T'] + 1
        if len(b) < 2: break
    return sorted(out, key=lambda c: c['t'])

def main():
    days = int(sys.argv[sys.argv.index('--days')+1]) if '--days' in sys.argv else 90
    end = int(time.time()*1000); start = end - days*24*3600*1000
    print(f'universe={UNI} window={days}d', flush=True)
    fh = {c: funding_history(c, start, end) for c in UNI}
    print('funding points:', {c: len(fh[c]) for c in UNI}, flush=True)
    px = {}
    for c in UNI:
        cs = candles(c, '1h', start, end)
        px[c] = {x['t']//3600000: float(x['c']) for x in cs}
    hours = sorted(set(h for c in UNI for h in [x['time']//3600000 for x in fh[c]]))
    # hourly funding map per coin
    fr = {c: {x['time']//3600000: float(x['fundingRate']) for x in fh[c]} for c in UNI}
    eq, peak, maxdd, wins, losses, fees, frecv = 100.0, 100.0, 0.0, 0, 0, 0.0, 0.0
    # align to daily rebalance at hours present in all coins
    common = sorted(set.intersection(*[set(fr[c]) for c in UNI]))
    t0 = common[0] + 24
    days_done = 0
    for h in range(t0, common[-1], 24):
        if h not in px.get(UNI[0], {}): continue
        # trailing 24h avg funding
        avg = {}
        for c in UNI:
            vals = [fr[c].get(h-i) for i in range(1, 25)]
            if all(v is not None for v in vals):
                avg[c] = sum(vals)/len(vals)
        if len(avg) < 6: continue
        ranked = sorted(avg, key=avg.get)
        longs, shorts = ranked[:TOPN], ranked[-TOPN:]
        # need prices now and +24h
        if any(h+24 not in px.get(c, {}) or h not in px.get(c, {}) for c in longs+shorts):
            continue
        if any(h+i not in fr.get(c, {}) for c in longs+shorts for i in range(0, 25)):
            continue
        n = 25.0  # $25 notional per leg -> $100 gross, delta neutral
        pnl = 0.0; legs = 0
        for c in shorts:
            r = (px[c][h+24]-px[c][h])/px[c][h]
            pnl += n*(-r)
            pnl += sum(fr[c][h+i]*n for i in range(0, 24))  # short receives +
            legs += 1
        for c in longs:
            r = (px[c][h+24]-px[c][h])/px[c][h]
            pnl += n*(r)
            pnl -= sum(fr[c][h+i]*n for i in range(0, 24))  # long pays funding, receives if neg
            legs += 1
        fl = legs*2*FEE*n
        pnl -= fl; fees += fl
        frecv += sum(fr[c][h+i]*n for c in shorts for i in range(0,24)) - sum(fr[c][h+i]*n for c in longs for i in range(0,24))
        eq += pnl
        peak = max(peak, eq); maxdd = max(maxdd, (peak-eq)/peak*100)
        if pnl >= 0: wins += 1
        else: losses += 1
        days_done += 1
    print(f'days={days_done} end={eq:.2f} ret={(eq-100):+.2f}% wins={wins} losses={losses} fees=${fees:.2f} funding_net=${frecv:.2f} maxDD={maxdd:.1f}%', flush=True)

if __name__ == '__main__':
    main()
