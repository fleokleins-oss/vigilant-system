"""
APEX CITADEL V3.2 - MASTER ORCHESTRATOR v3
9-Node Hub & Signal Aggregation Engine
Port: 8007
"""

import os
import asyncio
import logging
from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator
from dotenv import load_dotenv
import redis
import httpx

load_dotenv()

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)

app = FastAPI(title="Master Orchestrator v3", version="3.2.0")
Instrumentator().instrument(app).expose(app)

redis_url = os.getenv("REDIS_URL", "redis://127.0.0.1:6379/0")
redis_client = redis.from_url(redis_url, decode_responses=True)

# 9-NODE TOPOLOGY
NODES = {
    # DIRECTION TIER (P1)
    "newtonian": os.getenv("MAESTRO_NEWTONIAN_URL", "http://127.0.0.1:8011"),
    "spoofhunter": os.getenv("MAESTRO_SPOOFHUNTER_URL", "http://127.0.0.1:8012"),
    "dreamer": os.getenv("MAESTRO_DREAMER_URL", "http://127.0.0.1:8006"),
    
    # DATA FEED (P2)
    "econopredator": os.getenv("MAESTRO_ECONOPREDATOR_URL", "http://127.0.0.1:8000"),
    
    # SURVIVAL (P2)
    "antirug": os.getenv("MAESTRO_ANTIRUG_URL", "http://127.0.0.1:8003"),
    "narrative": os.getenv("MAESTRO_NARRATIVE_URL", "http://127.0.0.1:8004"),
    
    # EXECUTION (P2)
    "jito": os.getenv("MAESTRO_JITO_URL", "http://127.0.0.1:8005"),
    
    # EXIT ENGINE (P3)
    "apm_exit": os.getenv("APM_EXIT_ENGINE_URL", "http://127.0.0.1:8008"),
}

NODE_TIERS = {
    "P1_Direction": ["newtonian", "spoofhunter", "dreamer"],
    "P2_Data": ["econopredator"],
    "P2_Survival": ["antirug", "narrative"],
    "P2_Execution": ["jito"],
    "P3_Exit": ["apm_exit"],
}

@app.on_event("startup")
async def startup():
    logger.info("🎼 Master Orchestrator v3 starting. Checking 9-node topology...")
    for node_name, node_url in NODES.items():
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{node_url}/health", timeout=2)
                if response.status_code == 200:
                    logger.info(f"✅ {node_name}: ONLINE")
                else:
                    logger.warning(f"⚠️  {node_name}: DEGRADED")
        except Exception as e:
            logger.error(f"❌ {node_name}: OFFLINE - {e}")

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "master_orchestrator_v3", "nodes": 9}

@app.get("/status")
async def status():
    """Full 9-node topology status"""
    node_status = {}
    
    for node_name, node_url in NODES.items():
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{node_url}/health", timeout=2)
                node_status[node_name] = "online" if response.status_code == 200 else "degraded"
        except:
            node_status[node_name] = "offline"
    
    return {
        "service": "master_orchestrator_v3",
        "topology": "9-node_full_ensemble",
        "nodes": node_status,
        "redis": "connected" if redis_client.ping() else "disconnected",
        "node_count": len(node_status),
        "online_count": sum(1 for s in node_status.values() if s == "online")
    }

@app.get("/topology")
async def topology():
    """Get 9-node topology structure"""
    return {
        "P1_Direction": {
            "newtonian": "Physics-based momentum analysis",
            "spoofhunter": "Whale detection & order book",
            "dreamer": "Imagination & risk modeling"
        },
        "P2_Data": {
            "econopredator": "Market data feed & analysis"
        },
        "P2_Survival": {
            "antirug": "Risk assessment (XGBoost)",
            "narrative": "Narrative divergence detection"
        },
        "P2_Execution": {
            "jito": "Jito spoof & memecoin handling"
        },
        "P3_Exit": {
            "apm_exit": "4-weapon exit engine"
        }
    }

@app.post("/signal/aggregate")
async def aggregate_signals(symbol: str = "BTCUSDT"):
    """Aggregate signals from all 9 nodes"""
    logger.info(f"📡 Aggregating signals from 9 nodes for {symbol}...")
    
    signals = {}
    confidence_threshold = float(os.getenv("MAESTRO_V3_MIN_CONFIDENCE", "0.55"))
    
    async with httpx.AsyncClient() as client:
        tasks = []
        for node_name, node_url in NODES.items():
            tasks.append(fetch_signal(client, node_name, node_url, symbol))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for node_name, result in zip(NODES.keys(), results):
            if isinstance(result, Exception):
                signals[node_name] = {"status": "error", "error": str(result)}
            else:
                signals[node_name] = result
    
    consensus = calculate_consensus(signals, confidence_threshold)
    
    logger.info(f"🎯 Consensus: {consensus['action']} @ {consensus['confidence']:.2%}")
    
    return {
        "symbol": symbol,
        "signals": signals,
        "consensus": consensus
    }

async def fetch_signal(client: httpx.AsyncClient, node_name: str, node_url: str, symbol: str):
    """Fetch signal from a node"""
    try:
        response = await client.get(f"{node_url}/signal/{symbol}", timeout=5)
        if response.status_code == 200:
            return response.json()
        else:
            return {"status": "error", "code": response.status_code}
    except Exception as e:
        return {"status": "error", "error": str(e)}

def calculate_consensus(signals: dict, threshold: float) -> dict:
    """Calculate consensus from 9 nodes"""
    buy_votes = 0
    sell_votes = 0
    total_votes = 0
    
    for node_name, signal in signals.items():
        if isinstance(signal, dict) and "action" in signal:
            if signal.get("action") == "BUY":
                buy_votes += 1
            elif signal.get("action") == "SELL":
                sell_votes += 1
            total_votes += 1
    
    if total_votes == 0:
        return {"action": "HOLD", "confidence": 0.0}
    
    buy_confidence = buy_votes / total_votes
    sell_confidence = sell_votes / total_votes
    
    if buy_confidence >= threshold:
        action = "BUY"
        confidence = buy_confidence
    elif sell_confidence >= threshold:
        action = "SELL"
        confidence = sell_confidence
    else:
        action = "HOLD"
        confidence = max(buy_confidence, sell_confidence)
    
    return {
        "action": action,
        "confidence": confidence,
        "votes": {"buy": buy_votes, "sell": sell_votes, "total": total_votes}
    }

@app.post("/execute/trade")
async def execute_trade(symbol: str, action: str, size: float):
    """Execute via Jito node"""
    logger.info(f"💰 Executing {action} {size} {symbol}...")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{NODES['jito']}/execute",
                json={"symbol": symbol, "action": action, "size": size}
            )
            return response.json()
    except Exception as e:
        logger.error(f"Execution failed: {e}")
        return {"status": "error", "error": str(e)}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("MAESTRO_PORT", "8007"))
    uvicorn.run(app, host="0.0.0.0", port=port)
