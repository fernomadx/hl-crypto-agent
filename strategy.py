"""Indicators + long-only trend-pullback strategy. Stdlib only."""
def ema(vals, n):
    k = 2 / (n + 1)
    out, e = [], None
    for v in vals:
        e = v if e is None else v * k + e * (1 - k)
        out.append(e)
    return out

def rsi(closes, n=14):
    out = [None] * len(closes)
    gains, losses = [], []
    for i in range(1, len(closes)):
        ch = closes[i] - closes[i - 1]
        gains.append(max(ch, 0)); losses.append(max(-ch, 0))
        if i >= n:
            g = sum(gains[-n:]) / n; l = sum(losses[-n:]) / n
            out[i] = 100.0 if l == 0 else 100 - 100 / (1 + g / l)
    return out

def atr(candles, n=14):
    trs, out = [], []
    for i, c in enumerate(candles):
        if i == 0:
            trs.append(c['h'] - c['l'])
        else:
            p = candles[i - 1]['c']
            trs.append(max(c['h'] - c['l'], abs(c['h'] - p), abs(c['l'] - p)))
        out.append(sum(trs[-n:]) / min(len(trs), n))
    return out

def session_vwap(candles):
    """Reset VWAP at each UTC day boundary."""
    out, pv, vv = [], 0.0, 0.0
    day = None
    for c in candles:
        import datetime as dt
        d = dt.datetime.fromtimestamp(c['t'] / 1000, dt.timezone.utc).date()
        if d != day:
            day, pv, vv = d, 0.0, 0.0
        typ = (c['h'] + c['l'] + c['c']) / 3
        pv += typ * c['v']; vv += c['v']
        out.append(pv / vv if vv else typ)
    return out

def signals(candles):
    closes = [c['c'] for c in candles]
    e20, e50 = ema(closes, 20), ema(closes, 50)
    r, a, vw = rsi(closes), atr(candles), session_vwap(candles)
    sig = [False] * len(candles)
    for i in range(51, len(candles)):
        if e50[i] is None or r[i] is None:
            continue
        sig[i] = (closes[i] > e50[i] and e50[i] > e50[i - 5]
                  and e20[i] > e50[i]
                  and 45 <= r[i] <= 68
                  and closes[i] > vw[i])
    return {'e20': e20, 'e50': e50, 'rsi': r, 'atr': a, 'vwap': vw, 'sig': sig}
