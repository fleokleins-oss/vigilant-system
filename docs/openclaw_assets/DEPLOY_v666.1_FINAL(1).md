# 🦈 APEX PREDATOR NEO v666.1 — DEPLOY COMPLETO

## SKILL.md COMPLIANCE: 13/13 ✅

```
Module                    | Status | Key Feature
─────────────────────────────────────────────────────
1. Confluence God Mode    | ✅     | 8 filtros + ML sweep prediction
2. Predator Shadow        | ✅     | Jitter adaptativo + adversary detect
3. Anti-Rug v3            | ✅     | XGBoost 12-feature honeypot killer
4. Newtonian Regime       | ✅     | 4 regimes físicos (CONV/DIV/CONT/ISOL)
5. EconoPredator          | ✅     | Funding + OI + DXY + VIX (live feeds)
6. Narrative Divergence   | ✅     | CryptoPanic + Hyblock long/short
7. Robin Hood Risk        | ✅     | DD 4% = KILL + Auto-Earn > $0.05
8. APM                    | ✅     | VPIN + Ghost Reactor + Alpha Decay
9. DreamerV3              | ✅     | Monte Carlo imagination (50 sims)
10. ARE                   | ✅     | Jitter + subaccount + circuit breaker
11. Backtester            | ✅     | Tick-level + Sharpe + equity curve
12. External Feeds        | ✅     | CryptoPanic + Futures + DXY/VIX
13. FastAPI Gateway       | ✅     | 7 endpoints (/health /stats /risk...)
```

## ARQUITETURA
```
                    ┌──────────────────────────────────────┐
                    │      MAESTRO (FastAPI :8666)          │
                    │                                        │
                    │  Scanner (40ms) → Quick Eval           │
                    │       ↓                                │
                    │  9 Nodes em PARALELO (asyncio.gather)  │
                    │  ┌─────────────┬──────────────┐       │
                    │  │ Confluence  │ Shadow       │       │
                    │  │ Anti-Rug ⚡ │ Newtonian    │       │
                    │  │ Econo       │ Narrative    │       │
                    │  │ Robin Hood ⚡│ APM          │       │
                    │  │ DreamerV3   │              │       │
                    │  └─────────────┴──────────────┘       │
                    │       ↓ (⚡ = VETO power)             │
                    │  Score ≥ 60 + ≥4 votos → EXECUTE      │
                    │       ↓                                │
                    │  ARE Jitter → Executor → 3 pernas     │
                    │       ↓                                │
                    │  Robin Hood record → Auto-Earn $0.05+  │
                    └──────────────┬───────────────────────┘
                                   │
                    Redis Streams (persistent + ACK)
                    External Feeds (CryptoPanic/Futures/DXY)
```

## QUICK START
```bash
tar xzf apex-predator-neo-v666.1.tar.gz
cd apex-v666.1
cp .env.example .env && nano .env
# Preencher: BINANCE_TESTNET_API_KEY + SECRET
docker compose build --no-cache
docker compose up -d
docker compose logs -f maestro
```

## ENDPOINTS FastAPI
```bash
curl localhost:8666/           # Status
curl localhost:8666/health     # 9 nodes health check
curl localhost:8666/stats      # Maestro + Scanner + Executor stats
curl localhost:8666/risk       # Robin Hood state
curl localhost:8666/are        # ARE stats (backoff, circuit)
curl localhost:8666/feeds      # Macro (DXY/VIX) + Sentiment
```

## MONITORAMENTO REDIS
```bash
docker exec apex661_redis redis-cli xlen apex:v666:orders
docker exec apex661_redis redis-cli xrevrange apex:v666:orders + - COUNT 5
docker exec apex661_redis redis-cli xrevrange apex:v666:heartbeat + - COUNT 1
```

## PRODUÇÃO
```bash
docker compose down
nano .env  # TESTNET=False + chaves live (SOMENTE COM OK DO SABINO)
docker compose up -d && docker compose logs -f
```

## PARÂMETROS v666.1
```
Capital:     $81.75
Max/ciclo:   $6.00 (8% equity)
Auto-Earn:   > $0.05
Latência:    < 45ms
Drawdown:    4% = KILL (30min pause)
Shutdown:    equity < 50%
Scan:        40ms interval
Min profit:  0.06%
Min score:   60 (Maestro) / 65 (Confluence)
```

## 4.319 linhas | 21 módulos Python | 43 arquivos | Zero erros ✅
