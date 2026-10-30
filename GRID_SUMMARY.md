# Varredura: 1000 estratégias × 2 anos de dado real (Hyperliquid, 30/10/2026)

Base 1000 USDC por estratégia, candles diários (~730 barras; HYPE ~695, listada em nov/2024).
Long-only spot, all-in/all-out com compounding, fills no open seguinte.
Custos: taker 0,045% + slippage 0,02% por lado. Arquivo completo: `results_grid.csv`.

## Resultado
- Testadas: 1000 | OK: 1000 | Lucrativas (líquido de fees): **262**
- Robustas (≥10 trades e profit factor > 1): **65**

## Top robustas (retorno líquido, com drawdown — ler os dois)
| Retorno | Estratégia | Trades | Win% | MaxDD | PF |
| --- | --- | --- | --- | --- | --- |
| +389,9% | boll_20_2.0_HYPE | 10 | 80,0 | 16,77% | 10,03 |
| +365,7% | macd_8217_HYPE | 35 | 45,7 | 45,62% | 2,42 |
| +337,3% | rsi_tr_7_HYPE | 30 | 40,0 | 33,93% | 2,33 |
| +74,5% | emad_50_ETH | 10 | 40,0 | 28,07% | 2,17 |
| +70,7% | rsi_tr_14_ETH | 10 | 30,0 | 35,39% | 1,91 |

## Leitura honesta
1. As maiores são concentradas na HYPE, que subiu ~3-4x no período: long-only num foguete imprime lucro no backtest. É regime, não prova de edge.
2. Top por retorno puro (ex.: +182,9% rsi_rev_21_30_80_ETH) têm 2-3 trades: sorte amostral, não validação.
3. Drawdowns de 30-50% aparecem até nas lucrativas: sem stop/sizing, conta real quebraria no caminho.
4. Tudo aqui é **in-sample**: falta walk-forward e forward paper antes de qualquer conclusão. Nada vai para conta real sem edge validado.
5. Timeframe diário (holds de dias/semanas), não day trade intradiário.
