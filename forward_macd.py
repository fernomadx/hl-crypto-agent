"""Forward paper: MACD(6,19,5) long-only, 7 moedas, sizing 5% margem 20x (paper).
Sinais no último candle diário FECHADO (venue Hyperliquid); entrada a mercado.
Saída no sinal oposto (fiel ao backtest). Sem ordens reais.
Usage: python3 forward_macd.py --check | --enter
"""
import json, sys, time, urllib.request, datetime as dt
import grid_backtest as G

API=G.API
COINS=['HYPE','PUMP','NEAR','ONDO','UNI','SUI','BNB']
MARGIN_PCT,LEV=0.05,20
BASE=1000.0
STATE='/workspace/home/hl-bot/state.json'
LOG='/workspace/home/hl-bot/paper.log'

def mids():
    r=urllib.request.Request(API,data=json.dumps({'type':'allMids'}).encode(),headers={'Content-Type':'application/json'})
    with urllib.request.urlopen(r,timeout=30) as x: return json.load(x)

def log(m):
    line=f"{dt.datetime.now(dt.timezone.utc).strftime('%H:%M:%SZ')} {m}"
    print(line,flush=True)
    open(LOG,'a').write(line+'\n')

def signal(coin):
    end=int(time.time()*1000); start=end-400*24*3600*1000
    d=G.candles(coin,'1d',start,end)
    if len(d)<60: return None,None
    C=[float(c['c']) for c in d]
    m,s=G.macd(C,6,19,5)
    i=len(C)-2  # último fechado (penúltimo quando o último está formando)
    if m[i] is None: return None,None
    return (1 if m[i]>s[i] else 0), C[-1]

def main():
    mode=sys.argv[1] if len(sys.argv)>1 else '--check'
    st=json.load(open(STATE)) if __import__('os').path.exists(STATE) else {}
    macd=st.get('MACD',{'equity':BASE,'pos':{}})
    px=mids()
    for coin in COINS:
        sig,last=signal(coin)
        pos=macd['pos'].get(coin)
        if pos:
            log(f'MACD {coin}: segurando LONG entry={pos["entry"]} px={round(last,4) if last else "?"}')
            continue
        if sig==1 and last:
            entry=float(px[coin])
            macd['pos'][coin]={'side':1,'entry':entry,'notional':round(BASE*MARGIN_PCT*LEV,2),'at':int(time.time()*1000)}
            log(f"MACD {coin}: PAPER ENTRY LONG px={entry} notional={BASE*MARGIN_PCT*LEV:.0f} lev={LEV}x margem={BASE*MARGIN_PCT:.0f}")
        else:
            log(f'MACD {coin}: sem sinal (flat), nenhuma entrada')
    if mode=='--enter':
        st['MACD']=macd
        json.dump(st,open(STATE,'w'))
        log('MACD forward: estado salvo')
    else:
        log('MACD forward: dry-run, nada salvo')

if __name__=='__main__': main()
