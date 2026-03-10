---
name: apex-predator-neo
description: >
  Autonomous HFT AI assistant for Binance. 8 distributed AI nodes orchestrated by Maestro v3
  (Brain, ShadowGlass, SpoofHunter, Newtonian, Narrative, Dreamer, AntiRug, Executioner),
  7-module ConfluenceEngine for triangular arbitrage, 4-weapon Active Position Manager (VPIN,
  Dynamic OBI, Ghost Liquidity, Alpha Decay), EconoPredator macro intelligence with 6 pollers,
  Robin Hood Risk Engine, and Auto-Earn Hook. Integrates all 7 official Binance AI Agent Skills.
  Built for the Binance OpenClaw Challenge.
metadata:
  clawdbot:
    emoji: "🦈"
    always: false
    requires:
      bins: [curl, jq, python3, docker, redis-cli]
      env: [BINANCE_API_KEY, BINANCE_SECRET]
---

# 🦈 APEX PREDATOR NEO v666.1 — OpenClaw Skill

## Autonomous Multi-Node HFT AI for Binance

> 8 distributed AI nodes. 7-module ConfluenceEngine. 4-weapon APM. Sub-40ms scans. Zero human intervention.

---

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `BINANCE_API_KEY` | API Key (Spot trading enabled) | Yes |
| `BINANCE_SECRET` | API Secret | Yes |
| `APEX_MODE` | `testnet` (default) or `live` | No |
| `APEX_ROLE` | `scanner`, `executor`, or `lob_service` | No |
| `APEX_REGION` | `curitiba`, `singapore`, or `tokyo` | No |
| `APEX_CAPITAL` | Total capital USDT (default: 22) | No |
| `APEX_MAX_TRADE` | Max per trade USDT (default: 8) | No |
| `APEX_MAX_DRAWDOWN` | Max drawdown % before freeze (default: 4.0) | No |
| `APEX_SCAN_INTERVAL_MS` | Scan cycle ms (default: 40) | No |
| `REDIS_HOST` | Redis host (default: localhost) | No |
| `MIN_CONFLUENCE_SCORE` | Minimum score 0-100 (default: 65) | No |

---

## Binance AI Agent Skills Integration

| # | Binance Skill | APEX Module That Uses It |
|---|--------------|--------------------------|
| 1 | **CEX Spot Trading** | BinanceConnector — tickers, depth@100ms, bookTicker, order execution (market/limit/OCO), testnet+mainnet |
| 2 | **Address Insight** | EconoPredator `poll_onchain` — whale wallet analysis, exchange netflow, reserve tracking |
| 3 | **Token Details** | Scanner `discover()` — validate liquidity + active status before including pairs |
| 4 | **Market Rankings** | Scanner — auto-select top pairs by 24h volume for triangle path discovery |
| 5 | **Meme Rush** | EconoPredator — detect sudden surges creating temporary arb dislocations |
| 6 | **Trading Signals** | Maestro v3 — cross-reference with Brain node for higher confidence |
| 7 | **Token Contract Audit** | AntiRug node — audit contracts via `token_metrics` before scanning new pairs |

---

## Architecture: Maestro v3 + 8 Distributed AI Nodes

```
POST /orchestrate { symbol, venue, confluence_mode }

1. _gather_signals() → parallel async calls to all nodes
2. ConfluenceEngine.evaluate(signals) → weighted consensus
3. Publish to Redis stream → executors act

Nodes (all parallel via asyncio.wait + circuit breakers):
┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌────────────┐
│    Brain     │ │ ShadowGlass │ │ SpoofHunter │ │ Newtonian  │
│  LLM reason │ │ L2 micro-   │ │ Ghost walls │ │  Physics   │
│  (needs SG) │ │  structure  │ │  icebergs   │ │  momentum  │
└─────────────┘ └─────────────┘ └─────────────┘ └────────────┘
┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌────────────┐
│  Narrative   │ │   Dreamer   │ │   AntiRug   │ │ Executioner│
│  Sentiment   │ │  Scenario   │ │  Contract   │ │   Trade    │
│  analysis    │ │  prediction │ │   audit     │ │  execution │
└─────────────┘ └─────────────┘ └─────────────┘ └────────────┘
```

### SpoofHunter Details (from `spoofhunter.py`)
- `WallTracker`: tracks wall_id, side, price, initial_qty, first_seen, reduction_pct, distance_bps
- `IcebergTracker`: detects BBO refills (iceberg if refill_count ≥ threshold)
- `GhostWallEvent`: confirmed detections with lifetime_s, notional_usd
- `SpoofEngine.process_depth()`: L2 snapshot analysis, active wall tracking
- Contrarian signals: fake bids → SHORT, fake asks → LONG
- Intensity: LOW / MED / HIGH based on ghost_notional vs threshold × multiplier
- Confidence blend: ghost_conf + micro_conf + alignment bonus

### Brain (needs ShadowGlass data)
Brain receives `micro_price_shift` and `orderbook_imbalance` from ShadowGlass raw metrics. Called sequentially after ShadowGlass completes.

---

## ConfluenceEngine: 7-Module Weighted Filter

From `core/confluence_engine.py` — calibrated weights (sum = 1.0):

```python
WEIGHTS = {
    "tire":     0.18,  # Tire Pressure — bid/ask directional force (top-5 levels)
    "leadlag":  0.14,  # Lead-Lag Gravitacional — temporal sync between legs
    "fake":     0.16,  # Fake Momentum Filter — wash trading detection
    "oi_cons":  0.10,  # OI Spike Consistency — sustained volume vs noise
    "oi_ratio": 0.10,  # OI Delta/Volume Ratio — buy/sell equilibrium
    "reversal": 0.16,  # Post-Spike Reversal — price position in 24h range
    "entropy":  0.16,  # Order Book Entropy — Shannon H anti-spoof
}
```

Validation (ALL must pass):
```python
is_valid = (
    score >= MIN_CONFLUENCE_SCORE
    and not fake_momentum_flag
    and reversal_risk < 0.70
    and book_entropy > 0.20
)
```

Module 7 — Shannon Entropy Anti-Spoof:
```python
probs = [v / total for v in volumes]  # top-10 levels
entropy = -sum(p * math.log2(p) for p in probs if p > 0)
normalized = entropy / max_entropy  # 0.0=spoof, 1.0=natural
```

---

## APM: 4 Weapons of HFT Scalping (from `apm.py`)

Active Position Manager — monitors at 100ms. Does NOT decide entries, only manages exits.

### Weapon 1: VPIN
```python
VPIN_BUCKET_COUNT = 50
VPIN_TOXIC_THRESHOLD = 0.70       # probable informed trading
VPIN_CRITICAL_THRESHOLD = 0.85    # guaranteed dump
# BVC method: V_buy = V_total × Φ(ΔP / σ_ΔP)
```

### Weapon 2: Dynamic OBI Trailing
```python
OBI > 0.60  → 3.5× ATR (wide trail — room to pump)
OBI < -0.30 → 0.8× ATR (tight trail — snap)
Default     → 2.0× ATR
```

### Weapon 3: Ghost Liquidity Reaction
`GHOST_EXIT_CONFIDENCE = 0.60` — exit if SpoofHunter ghost wall confidence > 60%

### Weapon 4: Alpha Decay
```python
ALPHA_DECAY_S = 180       # 3 min max hold
ALPHA_MIN_MOVE_PCT = 0.5  # must move ≥0.5% or kill position
```

---

## EconoPredator: 6 Pollers (from `econopredator.py`)

FastAPI microservice — `GET /health`, `/market_data/{symbol}`, `/funding_heatmap`, `/macro_indicators`, `/atr/{symbol}`, `/onchain/{symbol}`

| Poller | Source | Data |
|--------|--------|------|
| `poll_funding` | Binance FAPI `/fapi/v1/premiumIndex` | mark_price, funding_rate, next_funding_time |
| `poll_oi` | Binance FAPI `/fapi/v1/openInterest` | open_interest × mark_price = OI value |
| `poll_ls_ratio` | Binance global L/S ratio | Account-level long/short balance |
| `poll_atr` | Kline-derived | Average True Range for volatility |
| `poll_macro` | Yahoo Finance, Alternative.me | DXY, VIX, Fear & Greed, CPI/FOMC |
| `poll_onchain` | Glassnode, Whale Alert | exchange_netflow, exchange_reserve, whale_tx |

---

## Distributed Execution

```
LOB Service (Curitiba)     --- WebSocket @depth@100ms + @aggTrade --> Binance
       | (shared memory, 0ms read)
       v
Scanner (Curitiba)         --- ConfluenceEngine (7 modules) + Dynamic Fees
       v Redis Pub/Sub (orjson + nanosecond timestamps)
       +--> Singapore Executor (AWS ap-southeast-1) → Binance API (<10ms)
       +--> Tokyo Executor (AWS ap-northeast-1)     → Binance API (<15ms)
                     |
              Atomic State Machine (rollback on partial fill)
                     |
              Robin Hood Risk → Auto-Earn Hook → Report to OpenClaw
```

Docker: redis (7.2-alpine, 512MB, hz=100), lob_service, scanner, singapore_executor, tokyo_executor.

---

## Robin Hood Risk Engine

4% max drawdown → 30-minute TOTAL freeze. $22 capital, $8 max/trade. Non-negotiable.

## Auto-Earn Hook (from `auto_earn_hook.py`)

Post-trade: if net_profit ≥ $0.10, query Simple Earn for best APR (cached 5min), subscribe, publish to Redis.

## BinanceConnector (from `binance_connector.py`)

CCXT async + aggressive caching: ticker cache (150ms), orderbook cache per symbol (15ms), auto-precision for minNotional, sandbox auto-detection, Simple Earn API.

---

## Tech Stack

Python 3.12, uvloop, CCXT Pro 4.4.61, Redis 7.2 (hiredis), orjson, websockets 12.0, aiohttp, FastAPI, Docker Swarm, Loguru, Pydantic v2, NumPy, Prometheus, optional Rust FFI (maturin).

---

## Quick Start

```bash
clawhub install apex-predator-neo
# Or paste GitHub URL in OpenClaw chat

export BINANCE_API_KEY="your_key"
export BINANCE_SECRET="your_secret"
export APEX_MODE="testnet"

docker compose build --no-cache
docker compose up -d redis lob_service scanner
docker compose logs -f scanner
```

Then: "Activate APEX PREDATOR NEO and start scanning Binance"

---

**Binance OpenClaw Challenge 2026** · #BinanceOpenClaw #CryptoAI
Built by @leoklein · Curitiba, BR 🇧🇷
