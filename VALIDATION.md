# Validação (dados reais Hyperliquid, 2026-10-30)
Janela: ~44 dias de 15m (limite de histórico da API), BTC/ETH/SOL, banca $100.
Custos: taker 0,045% + slippage 0,02% por lado. Risco 1%/trade, stop 2xATR, alvo 2R, kill diário -3%.

| Família | BTC | ETH | SOL |
| --- | --- | --- | --- |
| Trend long-only | -14,6% (PF 0,5) | -11,7% (PF 0,64) | -14,3% (PF 0,65) |
| Trend long+short | -17,5% (PF 0,57) | -16,7% (PF 0,72) | -11,5% (PF 0,82) |
| Mean-reversion | -18,5% (PF 0,42) | -18,9% (PF 0,55) | -22,9% (PF 0,53) |

Veredito: SEM edge validado neste regime (queda picotada BTC ~83k→~78k). Nenhum dinheiro real até o forward paper provar o contrário.
Motor `bot.py` roda em paper (dry-run, sem chave privada, sem ordens reais).
