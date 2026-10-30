# HL Crypto Paper Agent — Hyperliquid, $100 USDC

Agente de análise + paper-trade para Hyperliquid. **Não opera dinheiro real sozinho.**
Testado com dados reais em 30/10/2026: nenhuma das 3 famílias (trend long-only, trend long+short, mean-reversion) deu lucro em BTC/ETH/SOL (~44 dias, 15m, com taxas reais) — todas ficaram entre -11% e -23%. Por isso o motor roda em **paper only**.

## O que ele faz
- Lê candles públicos da Hyperliquid (`/info`, sem chave)
- Estratégia base: trend-pullback 15m (EMA20/50, RSI14, VWAP da sessão, stop 2xATR, alvo 2R, risco 1%/trade, mín $10/ordem, kill -3%/dia)
- `bot.py --once` avalia a última vela fechada e registra entrada/saída paper em `state.json` + `paper.log`
- Backtests com taxas reais (taker 0,045% + slippage 0,02% por lado)

## Rodar
```
python3 bot.py --once --coin BTC
python3 bot.py --once --coin ETH
python3 bot.py --once --coin SOL
python3 backtest.py   # trend long-only
python3 backtest2.py  # grade de parâmetros
python3 backtest3.py  # mean-reversion
```

## Fees Hyperliquid (conta < $5M/14d)
- taker 0,045%, maker 0,015%, sem gas. Mínimo $10/ordem.
- Testnet: https://api.hyperliquid-testnet.xyz (faucet exige 1 depósito mainnet prévio na mesma carteira).

## Por que tem stop (mesmo você pedindo "sem stop")
Sem stop a perda média fica ilimitada e uma cauda limpa a conta de $100. O stop 2xATR + risco 1% é o que impede ruína. "Só lucro" não existe: expectancy = win%×ganho − loss%×perda − taxas. Backtests acima provam.

## Para ir live (quando você acordar, com calma)
1. Criar carteira só para isso, depositar 100 USDC na Hyperliquid
2. Gerar API key com permissão só de trade (nunca withdraw)
3. Rodar 2-4 semanas em paper e só ligar live se PF > 1.2 em 50+ trades
4. Live começa com 0.5% de risco, nunca alavancagem > 2x

Aviso: day trade tem >90% de prejuízo (FGV/CVM). Isso aqui é estudo + automação paper, não garantia de lucro.

## Regra de venue (correção 30/10)
Preço que vale para stops, alvos e entradas do paper é SEMPRE o da Hyperliquid,
a venue operada. Nunca substituir por spot de outra venue (ex.: Coinbase): em
30/10 a Coinbase marcou 77293 enquanto a Hyperlink imprimiu wick a 78094 e
stopou o SHORT — venue errada = decisão errada. O bot trava sem decidir se o
dado da Hyperliquid estiver defasado (fail closed).
