
"""
core/confluence_god.py
ConfluenceGod — 8 advanced confluence filters + ML sweep predict 
"""
import asyncio
from typing import Dict
import numpy as np
from loguru import logger

from core.ml import SweepPredictor
from core.filters import (
    TirePressure,
    LeadLag,
    FakeMomentum,
    OIConsistency,
    OIDeltaRatio,
    ReversalRisk,
    BookEntropy,
    VolatilitySurge
)

class ConfluenceGod:
    def __init__(self):
        self.sweep_predictor = SweepPredictor()
        self.filters = [
            TirePressure(),
            LeadLag(),
            FakeMomentum(),
            OIConsistency(),
            OIDeltaRatio(),
            ReversalRisk(),
            BookEntropy(), 
            VolatilitySurge()
        ]
        
    async def start(self):
        self.sweep_predictor.start_training()
        
    async def analyze(self) -> Dict:
        symbols = ["BTCUSDT", "ETHUSDT"]  # Example
        
        scores = {}
        for symbol in symbols:
            filter_scores = await asyncio.gather(*[
                f.score(symbol) for f in self.filters
            ])
            weights = [f.weight for f in self.filters]
            scores[symbol] = np.average(filter_scores, weights=weights)
        
        best_symbol = max(scores, key=scores.get)
        sweep_prob = self.sweep_predictor.predict(best_symbol) 
        
        return {
            "best_symbol": best_symbol,
            "confluence_score": scores[best_symbol],
            "sweep_probability": sweep_prob
        }
