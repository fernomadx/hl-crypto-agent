# HL paper bot (Hyperliquid, $100)
Motor de paper-trade, stdlib only (sem deps). Estratégia: trend-pullback 15m
(EMA20/50, RSI14, VWAP sessão, stop 2xATR, alvo 2R, risco 1%, mín $10, kill -3%/dia).
- `hl_data.py` — lê candles públicos da Hyperlink (`/info`, sem auth).
- `strategy.py` — indicadores + sinais.
- `backtest.py` / `backtest2.py` / `backtest3.py` — validação com fees reais.
- `bot.py` — engine paper: `python3 bot.py --once --coin BTC` (estado em `state.json`, diário em `paper.log`).
- `VALIDATION.md` — resultado honesto atual: sem edge; paper apenas.
Fees base Hyperliquid (14d vol < $5M): taker 0,045%, maker 0,015%, sem gas. Mín $10/ordem.
Testnet: `https://api.hyperliquid-testnet.xyz` — faucet exige 1 depósito mainnet prévio na mesma carteira.
