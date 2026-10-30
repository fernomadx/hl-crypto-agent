"""Backtest: 1x long-only, 1% risk, 2xATR stop, 2R target. Fees = Hyperliquid base taker."""
import json, sys, datetime as dt

FEE = 0.00045   # taker 0.045%
SLIP = 0.0002   # slippage per side
MIN_NOTIONAL = 10.0

def run(candles, start_equity=100.0, risk_pct=0.01, atr_mult=2.0, rr=2.0):
    sys.path.insert(0, '/workspace/home/hl-bot')
    from strategy import signals
    ind = signals(candles)
    eq = start_equity
    trades, equity_curve = [], [start_equity]
    pos, cooldown, day_key, day_start, day_block = None, 0, None, start_equity, False
    peak, maxdd = start_equity, 0.0
    for i in range(len(candles)):
        c = candles[i]
        d = dt.datetime.fromtimestamp(c['t'] / 1000, dt.timezone.utc).date()
        if d != day_key:
            day_key, day_start, day_block = d, eq, False
        px = c['c']
        if pos:
            pnl_pct = (px - pos['entry']) / pos['entry']
            hit_stop = c['l'] <= pos['stop']
            hit_tp = c['h'] >= pos['tp']
            timeout = i - pos['i'] >= 96
            trend_out = px < ind['e50'][i]
            exit_px = pos['stop'] if hit_stop and not hit_tp else (pos['tp'] if hit_tp else px)
            if hit_stop or hit_tp or timeout or trend_out:
                gross = (exit_px - pos['entry']) / pos['entry'] * pos['notional']
                cost = pos['notional'] * (FEE + SLIP) + pos['notional'] * (1 + (exit_px - pos['entry']) / pos['entry']) * (FEE + SLIP)
                eq += gross - cost
                trades.append({'r': (gross - cost) / pos['risk_amt'], 'pnl': gross - cost})
                pos = None
                cooldown = 6
        else:
            if cooldown: cooldown -= 1
            if (eq - day_start) / day_start <= -0.03: day_block = True
            if not day_block and cooldown == 0 and ind['sig'][i] and i + 1 < len(candles):
                entry = candles[i + 1]['o']
                stop_d = atr_mult * ind['atr'][i]
                if stop_d <= 0 or entry <= 0: continue
                risk_amt = eq * risk_pct
                notional = risk_amt / (stop_d / entry)
                notional = max(MIN_NOTIONAL, min(notional, eq))  # 1x, sem alavancagem
                if notional < MIN_NOTIONAL: continue
                pos = {'entry': entry, 'stop': entry - stop_d,
                       'tp': entry + stop_d * rr, 'notional': notional,
                       'risk_amt': risk_amt, 'i': i + 1}
        peak = max(peak, eq)
        maxdd = min(maxdd, (eq - peak) / peak)
        equity_curve.append(eq)
    wins = [t for t in trades if t['pnl'] > 0]
    gross_w = sum(t['pnl'] for t in trades if t['pnl'] > 0)
    gross_l = -sum(t['pnl'] for t in trades if t['pnl'] <= 0)
    return {'n': len(trades), 'win%': round(100 * len(wins) / len(trades), 1) if trades else 0,
            'net': round(eq - start_equity, 2), 'ret%': round(100 * (eq / start_equity - 1), 2),
            'maxDD%': round(100 * maxdd, 2),
            'pf': round(gross_w / gross_l, 2) if gross_l else None, 'end': round(eq, 2)}

if __name__ == '__main__':
    tot_net, all_trades = 0, []
    for coin in ('btc', 'eth', 'sol'):
        data = json.load(open(f'/workspace/home/hl-bot/{coin}15m.json'))
        r = run(data)
        print(coin.upper(), r)
