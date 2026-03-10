"""
core/confluence_engine.py
APEX PREDATOR NEO v666 – ConfluenceEngine Completo (7 Módulos)

Integra 100% dos módulos proprietários do starbot666:

 ┌─────────────────────────────────────────────────────────┐
 │ 1. Tire Pressure           Pressão direcional do book   │
 │ 2. Lead-Lag Gravitacional  Sincronia temporal de pernas │
 │ 3. Fake Momentum Filter    Detecta momentum artificial  │
 │ 4. Consistência OI Spike   Volume sustentado vs ruído   │
 │ 5. OI_delta/Volume Ratio   Equilíbrio bid/ask real      │
 │ 6. Reversão Pós-Spike      Risco de price reversal      │
 │ 7. Order Book Entropy      Anti-spoof via Shannon H     │
 └─────────────────────────────────────────────────────────┘

Score final: 0-100 (ponderado). Rejeita se < MIN_CONFLUENCE_SCORE
OU se houver red flag (fake momentum, spoof detectado, reversal alto).
"""
from __future__ import annotations

import math
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import numpy as np
from loguru import logger

from config.config import cfg
from core.chart_confluence_engine import chart_confluence


# ═══════════════════════════════════════════════════════════
# RESULTADO DA CONFLUÊNCIA
# ═══════════════════════════════════════════════════════════
@dataclass
class ConfluenceResult:
    """Resultado completo de análise dos 7 módulos + chart confluence opcional."""
    score: float = 0.0
    tire_pressure: float = 0.0          # -1 (contra) a +1 (a favor)
    lead_lag_signal: float = 0.0        # -1 (descorrelacionado) a +1 (síncrono)
    fake_momentum_flag: bool = False    # True = momentum artificial detectado
    oi_spike_consistency: float = 0.0   # 0 (ruído) a 1 (sustentado)
    oi_delta_vol_ratio: float = 0.0     # 0 (desbalanceado) a 1 (saudável)
    reversal_risk: float = 0.0          # 0 (seguro) a 1 (reversão iminente)
    book_entropy: float = 0.0           # 0 (spoof provável) a 1 (natural)
    chart_score: Optional[float] = None
    chart_confidence: Optional[float] = None
    chart_setup: Optional[str] = None
    chart_allow: Optional[bool] = None
    details: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_valid(self) -> bool:
        """Passa em todos os filtros locais de segurança?"""
        chart_ok = self.chart_allow is not False
        return (
            self.score >= cfg.MIN_CONFLUENCE_SCORE
            and not self.fake_momentum_flag
            and self.reversal_risk < 0.70
            and self.book_entropy > 0.20
            and chart_ok
        )


# ═══════════════════════════════════════════════════════════
# ENGINE PRINCIPAL
# ═══════════════════════════════════════════════════════════
class ConfluenceEngine:
    """Motor de confluência multi-fator para arbitragem triangular."""

    # Pesos calibrados dos 7 fatores (soma exata = 1.00)
    WEIGHTS = {
        "tire":     0.18,  # Pressão do book — sinal mais direto
        "leadlag":  0.12,  # Correlação entre pernas
        "fake":     0.18,  # Filtro de manipulação (peso alto = veto forte)
        "oi_cons":  0.10,  # Sustentabilidade do volume
        "oi_ratio": 0.10,  # Equilíbrio compra/venda
        "reversal": 0.16,  # Risco de reversão
        "entropy":  0.16,  # Anti-spoof
    }

    def __init__(self) -> None:
        # Buffer circular de volume por símbolo (até 200 amostras)
        self._vol_history: Dict[str, List[float]] = {}
        self._max_history: int = 200

    # ───────────────────────────────────────────────────────
    # ANÁLISE COMPLETA
    # ───────────────────────────────────────────────────────
    def analyze(
        self,
        triangle: Dict[str, Any],
        orderbooks: Dict[str, Dict],
        tickers: Dict[str, Dict],
        candles_by_symbol: Optional[Dict[str, Any]] = None,
    ) -> ConfluenceResult:
        """Roda os 7 módulos legacy e injeta chart confluence quando houver candles."""
        result = ConfluenceResult()
        legs = triangle.get("legs", [])

        if len(legs) < 3:
            result.details["error"] = "Triângulo incompleto (< 3 pernas)"
            return result

        try:
            # Módulo 1: Tire Pressure
            result.tire_pressure = self._mod_tire_pressure(legs, orderbooks)

            # Módulo 2: Lead-Lag Gravitacional
            result.lead_lag_signal = self._mod_lead_lag(legs, tickers)

            # Módulo 3: Fake Momentum Filter
            result.fake_momentum_flag = self._mod_fake_momentum(legs, orderbooks, tickers)

            # Módulo 4: Consistência Temporal de OI Spike
            result.oi_spike_consistency = self._mod_oi_consistency(legs, tickers)

            # Módulo 5: OI Delta / Volume Ratio
            result.oi_delta_vol_ratio = self._mod_oi_delta_ratio(legs, tickers)

            # Módulo 6: Reversão Pós-Spike
            result.reversal_risk = self._mod_reversal_risk(legs, tickers)

            # Módulo 7: Order Book Entropy (Anti-Spoof)
            result.book_entropy = self._mod_book_entropy(legs, orderbooks)

            legacy_score = self._calculate_final_score(result)
            chart_payload = self._evaluate_chart_signal(legs, tickers, orderbooks, candles_by_symbol or {})
            result.score = self._blend_scores(legacy_score, chart_payload)

            if chart_payload:
                decision = chart_payload.get("decision", {})
                result.chart_score = float(decision.get("final_score", 0.0) or 0.0)
                result.chart_confidence = float(decision.get("confidence", 0.0) or 0.0)
                result.chart_setup = str(decision.get("setup", "") or "")
                result.chart_allow = bool(decision.get("allow", False))
            else:
                result.chart_allow = None

            result.details = {
                "legs": [leg.get("symbol", "") for leg in legs],
                "weights": self.WEIGHTS,
                "legacy_score": round(legacy_score, 4),
                "score_blend": {
                    "legacy_weight": 0.78 if chart_payload else 1.0,
                    "chart_weight": 0.22 if chart_payload else 0.0,
                },
                "module_scores": {
                    "tire": round(result.tire_pressure, 4),
                    "leadlag": round(result.lead_lag_signal, 4),
                    "fake": result.fake_momentum_flag,
                    "oi_cons": round(result.oi_spike_consistency, 4),
                    "oi_ratio": round(result.oi_delta_vol_ratio, 4),
                    "reversal": round(result.reversal_risk, 4),
                    "entropy": round(result.book_entropy, 4),
                },
                "chart": chart_payload,
            }
        except Exception as exc:
            logger.error(f"Confluência erro interno: {exc}")
            result.details["error"] = str(exc)

        return result

    # ═══════════════════════════════════════════════════════
    # MÓDULO 1: TIRE PRESSURE
    # ═══════════════════════════════════════════════════════
    def _mod_tire_pressure(
        self, legs: List[Dict], orderbooks: Dict[str, Dict],
    ) -> float:
        """Mede pressão direcional do book (top-5 níveis).
        Compra → quer bids fortes | Venda → quer asks fortes.
        Retorna: -1.0 (contra) a +1.0 (a favor)."""
        values = []
        for leg in legs:
            sym = leg.get("symbol", "")
            ob = orderbooks.get(sym, {})
            bids = ob.get("bids", [])[:5]
            asks = ob.get("asks", [])[:5]

            if not bids or not asks:
                values.append(0.0)
                continue

            bid_vol = sum(qty for _, qty in bids)
            ask_vol = sum(qty for _, qty in asks)
            total = bid_vol + ask_vol

            if total <= 0:
                values.append(0.0)
                continue

            # Imbalance: positivo = mais bids que asks
            imbalance = (bid_vol - ask_vol) / total

            # Se estamos comprando, bids fortes = bom
            # Se estamos vendendo, asks fortes = bom
            side = leg.get("side", "buy")
            pressure = imbalance if side == "buy" else -imbalance
            values.append(pressure)

        return float(np.mean(values)) if values else 0.0

    # ═══════════════════════════════════════════════════════
    # MÓDULO 2: LEAD-LAG GRAVITACIONAL
    # ═══════════════════════════════════════════════════════
    def _mod_lead_lag(
        self, legs: List[Dict], tickers: Dict[str, Dict],
    ) -> float:
        """Verifica sincronia de preço entre as 3 pernas do triângulo.
        Spread baixo de %change entre elas = arbitragem mais segura.
        Retorna: -1.0 (totalmente descorrelacionado) a +1.0 (sincronizado)."""
        pct_changes = []
        for leg in legs:
            sym = leg.get("symbol", "")
            tk = tickers.get(sym, {})
            pct = tk.get("percentage", 0) or 0
            pct_changes.append(float(pct))

        if len(pct_changes) < 3:
            return 0.0

        spread = max(pct_changes) - min(pct_changes)

        # Spread > 5% = completamente descorrelacionado
        if spread > 5.0:
            return -1.0
        # Spread < 0.3% = altamente sincronizado
        if spread < 0.3:
            return 1.0
        # Linear entre os extremos
        return 1.0 - (spread / 5.0)

    # ═══════════════════════════════════════════════════════
    # MÓDULO 3: FAKE MOMENTUM FILTER
    # ═══════════════════════════════════════════════════════
    def _mod_fake_momentum(
        self,
        legs: List[Dict],
        orderbooks: Dict[str, Dict],
        tickers: Dict[str, Dict],
    ) -> bool:
        """Detecta sinais de momentum artificial em QUALQUER perna.
        Red flags que ativam o filtro:
         - Spread bid-ask anormal (> 0.5%)
         - Book muito fino (< 3 níveis em bid ou ask)
         - Volume 24h < US$ 10.000
        Retorna: True = SUSPEITO (não executar), False = limpo."""
        for leg in legs:
            sym = leg.get("symbol", "")
            ob = orderbooks.get(sym, {})
            tk = tickers.get(sym, {})
            bids = ob.get("bids", [])
            asks = ob.get("asks", [])

            # Red flag 1: spread anormal > 0.5%
            if bids and asks:
                best_bid = bids[0][0]
                best_ask = asks[0][0]
                if best_bid > 0:
                    spread_pct = ((best_ask - best_bid) / best_bid) * 100
                    if spread_pct > 0.5:
                        return True

            # Red flag 2: book fino (menos de 3 níveis)
            if len(bids) < 3 or len(asks) < 3:
                return True

            # Red flag 3: volume 24h insignificante
            quote_vol = float(tk.get("quoteVolume", 0) or 0)
            if quote_vol < 10_000:
                return True

        return False

    # ═══════════════════════════════════════════════════════
    # MÓDULO 4: CONSISTÊNCIA TEMPORAL DE OI SPIKE
    # ═══════════════════════════════════════════════════════
    def _mod_oi_consistency(
        self, legs: List[Dict], tickers: Dict[str, Dict],
    ) -> float:
        """Avalia se spikes de volume são sustentados (não ruído pontual).
        Em spot, usamos quoteVolume como proxy de Open Interest.
        Compara volume recente (10 amostras) vs histórico (30 amostras).
        Retorna: 0.0 (ruído / queda) a 1.0 (volume sustentado e estável)."""
        values = []
        for leg in legs:
            sym = leg.get("symbol", "")
            vol = float(tickers.get(sym, {}).get("quoteVolume", 0) or 0)

            # Alimentar buffer circular
            if sym not in self._vol_history:
                self._vol_history[sym] = []
            self._vol_history[sym].append(vol)
            # Manter apenas MAX_HISTORY amostras
            if len(self._vol_history[sym]) > self._max_history:
                self._vol_history[sym] = self._vol_history[sym][-self._max_history:]

            hist = self._vol_history[sym]

            # Precisa de pelo menos 10 amostras para análise
            if len(hist) < 10:
                values.append(0.50)
                continue

            recent_avg = float(np.mean(hist[-10:]))
            older_slice = hist[-30:-10] if len(hist) > 30 else hist[:-10]
            older_avg = float(np.mean(older_slice)) if older_slice else recent_avg

            if older_avg <= 0:
                values.append(0.50)
                continue

            ratio = recent_avg / older_avg

            # Volume estável (0.7x a 1.5x) = boa consistência
            if 0.7 <= ratio <= 1.5:
                values.append(0.85)
            # Spike recente (> 1.5x) = pode reverter, cautela
            elif ratio > 1.5:
                values.append(0.40)
            # Volume caindo (< 0.7x) = liquidez secando
            else:
                values.append(0.25)

        return float(np.mean(values)) if values else 0.50

    # ═══════════════════════════════════════════════════════
    # MÓDULO 5: OI DELTA / VOLUME RATIO
    # ═══════════════════════════════════════════════════════
    def _mod_oi_delta_ratio(
        self, legs: List[Dict], tickers: Dict[str, Dict],
    ) -> float:
        """Ratio entre imbalance de bid/ask volume e volume total.
        Mercado saudável: delta/volume entre 0.01 e 0.10.
        Retorna: 0.0 (desbalanceado) a 1.0 (equilibrado)."""
        values = []
        for leg in legs:
            tk = tickers.get(leg.get("symbol", ""), {})
            bid_vol = float(tk.get("bidVolume", 0) or 0)
            ask_vol = float(tk.get("askVolume", 0) or 0)
            total_vol = float(tk.get("baseVolume", 0) or 0)

            if total_vol <= 0:
                values.append(0.30)
                continue

            delta = abs(bid_vol - ask_vol)
            ratio = delta / total_vol

            # Faixa saudável: 1% a 10% de imbalance
            if 0.01 <= ratio <= 0.10:
                values.append(0.90)
            elif ratio < 0.01:
                # Muito equilibrado — pode ser ilusão
                values.append(0.55)
            elif ratio <= 0.30:
                # Imbalance moderado
                values.append(0.40)
            else:
                # Imbalance extremo — um lado dominando
                values.append(0.15)

        return float(np.mean(values)) if values else 0.50

    # ═══════════════════════════════════════════════════════
    # MÓDULO 6: REVERSÃO PÓS-SPIKE
    # ═══════════════════════════════════════════════════════
    def _mod_reversal_risk(
        self, legs: List[Dict], tickers: Dict[str, Dict],
    ) -> float:
        """Probabilidade de reversão baseada na posição no range 24h.
        Se preço está > 85% do range com range > 5%, risco alto.
        Retorna: 0.0 (sem risco) a 1.0 (reversão iminente)."""
        values = []
        for leg in legs:
            tk = tickers.get(leg.get("symbol", ""), {})
            high = float(tk.get("high", 0) or 0)
            low = float(tk.get("low", 0) or 0)
            last = float(tk.get("last", 0) or 0)

            if high <= low or last <= 0:
                values.append(0.50)
                continue

            # Range percentual das últimas 24h
            range_pct = ((high - low) / low) * 100
            # Posição do preço no range (0 = no low, 1 = no high)
            position = (last - low) / (high - low)

            # Range amplo + preço nos extremos = risco de reversão
            if range_pct > 5.0 and (position > 0.85 or position < 0.15):
                values.append(0.85)
            elif range_pct > 3.0 and (position > 0.80 or position < 0.20):
                values.append(0.55)
            elif range_pct > 3.0:
                values.append(0.35)
            else:
                values.append(0.12)

        return float(np.mean(values)) if values else 0.50

    # ═══════════════════════════════════════════════════════
    # MÓDULO 7: ORDER BOOK ENTROPY (ANTI-SPOOF)
    # ═══════════════════════════════════════════════════════
    def _mod_book_entropy(
        self, legs: List[Dict], orderbooks: Dict[str, Dict],
    ) -> float:
        """Shannon entropy normalizada do order book (top 10 níveis).
        Entropia alta = distribuição natural/saudável de ordens.
        Entropia baixa = poucas ordens gigantes (possível spoofing).
        Retorna: 0.0 (provável spoof) a 1.0 (book natural)."""
        values = []
        for leg in legs:
            sym = leg.get("symbol", "")
            ob = orderbooks.get(sym, {})

            for side_key in ("bids", "asks"):
                orders = ob.get(side_key, [])[:10]

                if len(orders) < 3:
                    values.append(0.0)
                    continue

                volumes = [qty for _, qty in orders if qty > 0]
                total = sum(volumes)

                if total <= 0 or len(volumes) < 2:
                    values.append(0.0)
                    continue

                # Calcular probabilidades e Shannon entropy
                probs = [v / total for v in volumes]
                entropy = -sum(p * math.log2(p) for p in probs if p > 0)
                max_entropy = math.log2(len(probs))

                # Normalizar para 0-1
                normalized = entropy / max_entropy if max_entropy > 0 else 0
                values.append(normalized)

        return float(np.mean(values)) if values else 0.50

    # ═══════════════════════════════════════════════════════
    # SCORE FINAL PONDERADO (0-100)
    # ═══════════════════════════════════════════════════════
    def _calculate_final_score(self, r: ConfluenceResult) -> float:
        """Combina os 7 módulos com pesos calibrados → score 0-100."""
        # Normalizar cada módulo para faixa 0-1
        scores = {
            "tire":     (r.tire_pressure + 1.0) / 2.0,     # -1..+1 → 0..1
            "leadlag":  (r.lead_lag_signal + 1.0) / 2.0,   # -1..+1 → 0..1
            "fake":     0.0 if r.fake_momentum_flag else 1.0,  # binário
            "oi_cons":  r.oi_spike_consistency,              # já 0..1
            "oi_ratio": r.oi_delta_vol_ratio,                # já 0..1
            "reversal": 1.0 - r.reversal_risk,               # inverter (menos risco = melhor)
            "entropy":  r.book_entropy,                      # já 0..1
        }

        # Média ponderada
        weighted_sum = sum(scores[k] * self.WEIGHTS[k] for k in self.WEIGHTS)

        # Escalar para 0-100 e clampar
        return max(0.0, min(100.0, weighted_sum * 100.0))

    def _evaluate_chart_signal(
        self,
        legs: List[Dict[str, Any]],
        tickers: Dict[str, Dict[str, Any]],
        orderbooks: Dict[str, Dict[str, Any]],
        candles_by_symbol: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        if not candles_by_symbol:
            return None

        symbol = self._select_primary_symbol(legs, candles_by_symbol)
        raw = candles_by_symbol.get(symbol)
        if raw is None:
            return None
        if hasattr(raw, "__len__") and len(raw) == 0:
            return None

        frame = self._candles_to_frame(raw, symbol, tickers, orderbooks)
        if frame is None:
            return None

        assessment = chart_confluence.assess(frame)
        payload = assessment.to_dict()
        payload["symbol"] = symbol
        return payload

    def _select_primary_symbol(self, legs: List[Dict[str, Any]], candles_by_symbol: Dict[str, Any]) -> str:
        available = set(candles_by_symbol.keys())
        for leg in legs:
            symbol = str(leg.get("symbol", "") or "")
            if symbol in available:
                return symbol
        return next(iter(available))

    def _candles_to_frame(
        self,
        raw: Any,
        symbol: str,
        tickers: Dict[str, Dict[str, Any]],
        orderbooks: Dict[str, Dict[str, Any]],
    ) -> Optional[Any]:
        try:
            import pandas as pd
        except Exception as exc:
            logger.debug(f"pandas unavailable for chart confluence: {exc}")
            return None

        try:
            if hasattr(raw, "columns"):
                frame = raw.copy()
            else:
                frame = pd.DataFrame(raw)

            if frame.empty:
                return None

            cols = list(frame.columns)
            if {"open", "high", "low", "close", "volume"}.issubset(cols):
                frame = frame[["open", "high", "low", "close", "volume"]].copy()
            elif frame.shape[1] >= 6:
                frame = frame.iloc[:, :6]
                frame.columns = ["timestamp", "open", "high", "low", "close", "volume"]
                frame = frame[["open", "high", "low", "close", "volume"]].copy()
            else:
                return None
            for col in frame.columns:
                frame[col] = pd.to_numeric(frame[col], errors="coerce")
            frame = frame.dropna().reset_index(drop=True)
            if len(frame) < 40:
                return None

            tk = tickers.get(symbol, {}) or tickers.get(symbol.replace("/", ""), {}) or {}
            ob = orderbooks.get(symbol, {}) or orderbooks.get(symbol.replace("/", ""), {}) or {}
            bids = ob.get("bids", [])[:5]
            asks = ob.get("asks", [])[:5]
            bid_vol = sum(float(level[1]) for level in bids) if bids else 0.0
            ask_vol = sum(float(level[1]) for level in asks) if asks else 0.0
            total = bid_vol + ask_vol
            obi = 0.0 if total <= 0 else (bid_vol - ask_vol) / total

            ghost_intensity = 0.0
            if bids and asks:
                best_bid = float(bids[0][0])
                best_ask = float(asks[0][0])
                spread_bps = 0.0 if best_bid <= 0 else ((best_ask - best_bid) / best_bid) * 10_000.0
                max_bid_share = max((float(level[1]) / max(bid_vol, 1e-9)) for level in bids) if bid_vol > 0 else 0.0
                max_ask_share = max((float(level[1]) / max(ask_vol, 1e-9)) for level in asks) if ask_vol > 0 else 0.0
                extreme_ratio = max(max_bid_share, max_ask_share)
                ghost_intensity = min(1.0, max(0.0, (spread_bps - 12.0) / 18.0) + max(0.0, extreme_ratio - 0.45))

            frame["obi"] = obi
            frame["oi_delta_pct"] = 0.0
            frame["funding_rate"] = 0.0
            frame["vpin"] = 0.0
            frame["ghost_intensity"] = ghost_intensity
            quote_volume = float(tk.get("quoteVolume", 0.0) or 0.0)
            if quote_volume > 0 and len(frame) > 0:
                frame.loc[frame.index[-1], "volume"] = max(float(frame["volume"].iloc[-1]), quote_volume / max(len(frame), 1))
            return frame
        except Exception as exc:
            logger.debug(f"chart frame build failed for {symbol}: {exc}")
            return None

    def _blend_scores(self, legacy_score: float, chart_payload: Optional[Dict[str, Any]]) -> float:
        if not chart_payload:
            return legacy_score
        decision = chart_payload.get("decision", {})
        chart_score = float(decision.get("final_score", 0.0) or 0.0)
        blended = (legacy_score * 0.78) + (chart_score * 0.22)
        return max(0.0, min(100.0, blended))



# Singleton global
confluence = ConfluenceEngine()
