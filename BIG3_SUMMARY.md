# Foco BTC/ETH/SOL: 1209 combinações, 2 anos de dado diário + validação OOS (30/10)

Base 1000 USDC por estratégia, long-only spot, fills no open seguinte,
fee taker 0,045% + slippage 0,02% por lado. Arquivos: `results_big3.csv` (IS),
`oos_top40.csv` (fora da amostra). IS = primeiros ~18 meses, OOS = últimos ~6 meses.

- Testadas: 1209 (403 por moeda) | Lucrativas no IS: 441
- Top 40 do IS re-testadas no OOS (período nunca visto): 19/40 lucrativas
- Robustas no OOS (≥8 trades + lucro): **1**

| OOS | Estratégia | Trades | Win% | DD | PF |
| --- | --- | --- | --- | --- | --- |
| +39,7% | macd_6_19_5_SOL | 12 | 50,0 | 9,25% | 3,05 |

## Leitura honesta
1. Quase todo o resto do topo OOS tem 2-5 trades: sorte amostral, não validação.
2. A única candidata com double-digit de trades no OOS é a macd em SOL — promissora, NÃO validada para real.
3. O próximo passo honesto é forward paper dela (e das próximas) por semanas, não live.
4. Timeframe diário (holds de dias/semanas), não day trade intradiário.
