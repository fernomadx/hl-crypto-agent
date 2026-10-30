# Pesquisa: day trade lucrativo de crypto com 100 USDC (30/10/2026)

## Veredito em uma linha
Nenhuma estratégia testada aqui mostrou edge lucrativo após taxas. O bot deste
repo roda em **paper only** por isso.

## O que foi testado com dados reais
Motor próprio (`backtest.py`, `backtest2.py`, `backtest3.py`), candles de 15m da
Hyperliquid (~44 dias), BTC/ETH/SOL, banca $100, risco 1%/trade, stop 2xATR,
alvo 2R, taker 0,045% + slippage 0,02% por lado:

| Família | BTC | ETH | SOL |
| --- | --- | --- | --- |
| Trend long-only | -14,6% (PF 0,50) | -11,7% (PF 0,64) | -14,3% (PF 0,65) |
| Trend long+short | -17,5% (PF 0,57) | -16,7% (PF 0,72) | -11,5% (PF 0,82) |
| Reversão à média | -18,5% (PF 0,42) | -18,9% (PF 0,55) | -22,9% (PF 0,53) |

Grade de parâmetros (ATR 1,5/2,0/2,5, RR 1,5/2,0): todas negativas (-5% a -24%).

## Terceiros honestos confirmam
- `Crypto-Data-API/hyperliquid-backtester` (71 dias): melhor exemplo +1,64%,
  pagando **$605 de taxas para lucrar $164** (taxa comeu 79% do bruto).
  Tendência -17,45% no mesmo período. Conclusão do autor: sem taxas o mesmo
  backtest "vira" vencedor — ou seja, a maioria dos backtests por aí mente.
- Revisão de 402 estratégias em pares crypto: 0 passaram correção
  Benjamini-Hochberg; mediana -39,5 pts/ano vs benchmark.
- Estudo FGV/CVM (19.696 iniciantes): 91% dos que persistiram tiveram prejuízo.
- CVM: promessa de "robô com lucro garantido / sem loss" é indício de fraude.

## Por que "sem stop e só lucro" não existe
Expectancy = win% × ganho médio − loss% × perda média − taxas. Sem stop, a perda
média fica ilimitada e uma cauda limpa a conta de $100. Win rate de 90% ainda
perde se os 10% correm longe. Stop + risco de 1–2% por trade é o que bota um
teto na perda.

## Custos para $100 (conta pequena)
- Hyperliquid (<$5M/14d): taker 0,045%, maker 0,015%, sem gas, mínimo $10/ordem.
- Ida+volta a mercado ≈ 0,13% + slippage → precisa de ~0,3–0,4% só para empatar.
- 5 trades/dia ≈ 1%/dia de fricção, ~22%/mês só para empatar.

## Para ligar live um dia (checklist, com calma)
1. Carteira só para isso, depositar 100 USDC na Hyperlink.
2. API key com permissão só de trade (nunca withdraw).
3. 2–4 semanas de paper com PF > 1,2 em 50+ trades antes de qualquer real.
4. Começar com 0,5% de risco, alavancagem máxima 2x, kill diário -3%.

## Riscos
Day trade tem >90% de prejuízo (FGV/CVM). Isto aqui é estudo + automação paper,
não garantia de lucro. Repos do próprio autor (Crypto-Monitor: monitor +
scorecard com 10x, sem lucro validado publicado) reforçam o quadro.

## Nova missão (30/10, pós 04:52): funding carry cross-sectional
Réplica própria estilo Keel (short 2 fundings mais ricos / long 2 mais baratos,
rebalance diário, 10 perps, 1x, taker 0,045%): **90 dias → -29,76%**
(36 wins / 52 losses, taxas $7,92, funding líquido só +$1,04, maxDD 32,6%).
Funding recebido não cobre a deriva dos preços das pernas. Janela do Keel
(08/2024–09/2026, +49,2% líquido) é outro regime/construção — não replicado aqui.
Próximas frentes: grid/MM open-source, momentum long-only com filtro BTC.

## Varredura 1000 estratégias (30/10, dados diários 2 anos, base 1000)
`grid_backtest.py` + `results_grid.csv` + `GRID_SUMMARY.md`: 1000 combinações
(10 moedas × 100 parametrizações em 12 famílias), líquido de fees.
262 lucrativas, 65 robustas (≥10 trades, PF>1) — concentradas na HYPE
(subiu 3-4x no período: regime, não edge provado). Maiores retornos com 2-3
trades = sorte amostral. Tudo in-sample; falta walk-forward. Nada live.
