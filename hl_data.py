"""Public market data from Hyperliquid (no auth needed). Stdlib only."""
import json, time, urllib.request

API = 'https://api.hyperliquid.xyz/info'

def post(payload, timeout=30):
    req = urllib.request.Request(API, data=json.dumps(payload).encode(),
                                 headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)

def candles(coin, interval='15m', days=90):
    end = int(time.time() * 1000)
    start = end - days * 24 * 3600 * 1000
    out, cur = [], start
    while cur < end:
        nxt = min(cur + 30 * 24 * 3600 * 1000, end)  # API caps ~5000 candles
        batch = post({"type": "candleSnapshot",
                      "req": {"coin": coin, "interval": interval,
                              "startTime": cur, "endTime": nxt}})
        if not batch:
            break
        out.extend(batch)
        cur = batch[-1]['T'] + 1
        if len(batch) < 2:
            break
    seen, clean = set(), []
    for c in out:
        if c['t'] not in seen:
            seen.add(c['t'])
            clean.append({k: (float(c[k]) if k in 'ohlcv' else c[k]) for k in ('t', 'o', 'h', 'l', 'c', 'v')})
    clean.sort(key=lambda c: c['t'])
    return clean

def mids():
    return post({"type": "allMids"})
