"""HL paper engine (Hyperliquid, dry-run default). Stdlib only.
Usage: python3 bot.py --once [--coin BTC] [--equity 100]
State in state.json, human log in paper.log. Never touches real money:
no private key is ever loaded; live orders are not implemented.
"""
import json, sys, os, time, datetime as dt
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hl_data import candles
from strategy import signals

BASE = os.path.dirname(os.path.abspath(__file__))
STATE = os.path.join(BASE, 'state.json')
LOG = os.path.join(BASE, 'paper.log')
ATR_MULT, RR = 2.0, 2.0
MARGIN_FRAC, LEV = 0.05, 20  # 5% do capital a 20x (paper)
MIN_NOTIONAL = 10.0  # Hyperliquid protocol minimum

def load_state():
    try: return json.load(open(STATE))
    except Exception: return {}

def log(msg):
    line = f"{dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%d %H:%M:%SZ')} {msg}"
    print(line, flush=True)
    with open(LOG, 'a') as f: f.write(line + '\n')

def once(coin='BTC', equity=100.0):
    st = load_state()
    data = candles(coin, '15m', 3)
    if len(data) < 60:
        log(f'{coin}: sem dados suficientes ({len(data)})'); return
    ind = signals(data)
    i = len(data) - 2  # last CLOSED bar
    c, px = data[i], data[i]['c']
    key = f'{coin}'
    pos = st.get(key)
    if pos:
        if pos['side'] == 1: hs, ht = c['l'] <= pos['stop'], c['h'] >= pos['tp']
        else: hs, ht = c['h'] >= pos['stop'], c['l'] <= pos['tp']
        xp = pos['stop'] if hs and not ht else (pos['tp'] if ht else None)
        if xp is not None:
            chg = (xp - pos['entry']) / pos['entry'] * pos['side']
            pnl = chg * pos['notional'] - pos['notional'] * 0.0013
            eq = st.get('equity', equity) + pnl
            st['equity'] = round(eq, 2)
            log(f"{coin}: PAPER EXIT {'STOP' if hs else 'TP'} {pos['side']>0 and 'LONG' or 'SHORT'} entry={pos['entry']} exit={round(xp,2)} pnl={round(pnl,2)} eq={round(eq,2)}")
            st.pop(key, None)
            json.dump(st, open(STATE, 'w'))
            return
        log(f"{coin}: segurando {'LONG' if pos['side']>0 else 'SHORT'} entry={pos['entry']} px={px}")
        return
    long_ok = px > ind['e50'][i] and ind['e50'][i] > ind['e50'][i-5] and ind['e20'][i] > ind['e50'][i] and (ind['rsi'][i] is not None and 45 <= ind['rsi'][i] <= 68) and px > ind['vwap'][i]
    short_ok = px < ind['e50'][i] and ind['e50'][i] < ind['e50'][i-5] and ind['e20'][i] < ind['e50'][i] and (ind['rsi'][i] is not None and 32 <= ind['rsi'][i] <= 55) and px < ind['vwap'][i]
    eq = st.get('equity', equity)
    if (long_ok or short_ok):
        side = 1 if long_ok else -1
        stop_d = ATR_MULT * ind['atr'][i]
        margin = eq * MARGIN_FRAC
        notional = max(MIN_NOTIONAL, margin * LEV)
        risk_amt = notional * (stop_d / px)
        st[key] = {'side': side, 'entry': px, 'stop': round(px - side * stop_d, 2),
                   'tp': round(px + side * stop_d * RR, 2), 'notional': round(notional, 2),
                   'risk_amt': round(risk_amt, 2), 'at': data[i]['t']}
        json.dump(st, open(STATE, 'w'))
        log(f"{coin}: PAPER ENTRY {'LONG' if side>0 else 'SHORT'} px={px} stop={st[key]['stop']} tp={st[key]['tp']} notional={st[key]['notional']} lev={LEV}x margem={round(margin,2)} liq~4.5%contra rsi={round(ind['rsi'][i],1)}")
    else:
        log(f"{coin}: sem sinal px={px} ema50={round(ind['e50'][i],1)} rsi={round(ind['rsi'][i] or -1,1)}")

if __name__ == '__main__':
    coin = sys.argv[sys.argv.index('--coin')+1] if '--coin' in sys.argv else 'BTC'
    eq = float(sys.argv[sys.argv.index('--equity')+1]) if '--equity' in sys.argv else 1000.0
    once(coin, eq)
