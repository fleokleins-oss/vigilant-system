from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, Literal, Optional

import numpy as np
import pandas as pd

Trend = Literal["bullish", "bearish", "neutral"]
Setup = Literal["continuation", "reversal", "breakdown", "mean_revert", "neutral"]


@dataclass
class TrendState:
    label: Trend
    ema_fast: float
    ema_slow: float
    ema_spread_pct: float
    slope_fast_pct: float
    slope_slow_pct: float
    swing_bias: float


@dataclass
class ImpulseState:
    detected: bool
    direction: Trend
    candle_index: Optional[int]
    body: float
    range_size: float
    atr_multiple: float
    body_zscore: float
    close_location_value: float
    volume_ratio: float


@dataclass
class RetracementState:
    ratio: Optional[float]
    quality: str
    held_50pct: bool
    held_618: bool


@dataclass
class CompressionState:
    detected: bool
    width_atr: Optional[float]
    realized_vol_ratio: Optional[float]
    note: str


@dataclass
class BreakoutState:
    active: bool
    direction: Trend
    swing_level: Optional[float]
    distance_from_level_pct: Optional[float]
    confirmed_by_volume: bool


@dataclass
class MicrostructureState:
    obi_bias: float = 0.0
    funding_bias: float = 0.0
    oi_bias: float = 0.0
    vpin_risk: float = 0.0
    ghost_risk: float = 0.0


@dataclass
class ConfluenceDecision:
    allow: bool
    setup: Setup
    trend: Trend
    confidence: float
    base_score: float
    final_score: float
    score_delta: float
    invalid_if_below: Optional[float]
    confirm_if_above: Optional[float]
    warnings: list[str] = field(default_factory=list)
    boosts: list[str] = field(default_factory=list)
    trace: list[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Assessment:
    trend: TrendState
    impulse: ImpulseState
    retracement: RetracementState
    compression: CompressionState
    breakout: BreakoutState
    microstructure: MicrostructureState
    decision: ConfluenceDecision
    levels: Dict[str, Optional[float]]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "trend": asdict(self.trend),
            "impulse": asdict(self.impulse),
            "retracement": asdict(self.retracement),
            "compression": asdict(self.compression),
            "breakout": asdict(self.breakout),
            "microstructure": asdict(self.microstructure),
            "decision": self.decision.to_dict(),
            "levels": self.levels,
        }


class ChartConfluenceEngine:
    """
    Candle-aware confluence engine meant to sit beside the existing local
    triangular-arbitrage confluence engine.

    Required columns:
        open, high, low, close

    Optional columns:
        volume, obi, funding_rate, oi_delta_pct, vpin, ghost_intensity
    """

    def __init__(
        self,
        *,
        ema_fast: int = 9,
        ema_slow: int = 21,
        atr_period: int = 14,
        vol_period: int = 20,
        impulse_atr_multiple: float = 1.2,
        impulse_body_zscore_min: float = 1.25,
        breakout_volume_ratio_min: float = 1.15,
        compression_window: int = 5,
        compression_atr_max: float = 2.2,
        swing_lookback: int = 5,
    ) -> None:
        self.ema_fast = ema_fast
        self.ema_slow = ema_slow
        self.atr_period = atr_period
        self.vol_period = vol_period
        self.impulse_atr_multiple = impulse_atr_multiple
        self.impulse_body_zscore_min = impulse_body_zscore_min
        self.breakout_volume_ratio_min = breakout_volume_ratio_min
        self.compression_window = compression_window
        self.compression_atr_max = compression_atr_max
        self.swing_lookback = swing_lookback

    def assess(self, df: pd.DataFrame) -> Assessment:
        d = self._prepare(df)

        trend = self._detect_trend(d)
        impulse = self._detect_impulse(d)
        retracement = self._evaluate_retracement(d, impulse)
        compression = self._detect_compression(d, impulse)
        breakout = self._detect_breakout(d, trend)
        micro = self._read_microstructure(d)
        levels = self._map_levels(d, impulse)
        decision = self._make_decision(
            d=d,
            trend=trend,
            impulse=impulse,
            retracement=retracement,
            compression=compression,
            breakout=breakout,
            micro=micro,
            levels=levels,
        )

        return Assessment(
            trend=trend,
            impulse=impulse,
            retracement=retracement,
            compression=compression,
            breakout=breakout,
            microstructure=micro,
            decision=decision,
            levels=levels,
        )

    def _prepare(self, df: pd.DataFrame) -> pd.DataFrame:
        required = {"open", "high", "low", "close"}
        missing = required - set(df.columns)
        if missing:
            raise ValueError(f"Missing required columns: {sorted(missing)}")
        if len(df) < max(self.ema_slow + 5, self.atr_period + 5, 40):
            raise ValueError("Not enough rows for stable assessment.")

        d = df.copy().reset_index(drop=True)
        for col in [
            "open",
            "high",
            "low",
            "close",
            "volume",
            "obi",
            "funding_rate",
            "oi_delta_pct",
            "vpin",
            "ghost_intensity",
        ]:
            if col in d.columns:
                d[col] = pd.to_numeric(d[col], errors="coerce")

        d["range"] = (d["high"] - d["low"]).clip(lower=0)
        d["body"] = (d["close"] - d["open"]).abs()
        d["direction"] = np.sign(d["close"] - d["open"]).fillna(0)
        d["close_loc"] = np.where(
            d["range"] > 0,
            ((d["close"] - d["low"]) / d["range"]).clip(0, 1),
            0.5,
        )

        prev_close = d["close"].shift(1)
        tr = pd.concat(
            [
                d["high"] - d["low"],
                (d["high"] - prev_close).abs(),
                (d["low"] - prev_close).abs(),
            ],
            axis=1,
        ).max(axis=1)
        d["atr"] = tr.rolling(self.atr_period, min_periods=2).mean().bfill()
        d["atr_pct"] = np.where(d["close"] > 0, d["atr"] / d["close"] * 100.0, 0.0)

        d["ema_fast"] = d["close"].ewm(span=self.ema_fast, adjust=False).mean()
        d["ema_slow"] = d["close"].ewm(span=self.ema_slow, adjust=False).mean()
        d["ret_1"] = np.log(d["close"] / d["close"].shift(1)).replace([np.inf, -np.inf], np.nan).fillna(0.0)
        d["realized_vol"] = d["ret_1"].rolling(self.vol_period, min_periods=5).std().fillna(0.0)

        if "volume" in d.columns:
            d["volume"] = d["volume"].fillna(0.0)
            vol_ma = d["volume"].rolling(self.vol_period, min_periods=3).mean().replace(0, np.nan)
            d["volume_ratio"] = (d["volume"] / vol_ma).replace([np.inf, -np.inf], np.nan).fillna(1.0)
        else:
            d["volume_ratio"] = 1.0

        body_mean = d["body"].rolling(self.vol_period, min_periods=5).mean()
        body_std = d["body"].rolling(self.vol_period, min_periods=5).std().replace(0, np.nan)
        d["body_zscore"] = ((d["body"] - body_mean) / body_std).replace([np.inf, -np.inf], np.nan).fillna(0.0)

        d["swing_high"] = d["high"].rolling(self.swing_lookback, min_periods=2).max().shift(1)
        d["swing_low"] = d["low"].rolling(self.swing_lookback, min_periods=2).min().shift(1)

        return d

    def _detect_trend(self, d: pd.DataFrame) -> TrendState:
        last = d.iloc[-1]
        ema_fast = float(last["ema_fast"])
        ema_slow = float(last["ema_slow"])
        close = float(last["close"])

        fast_prev = float(d["ema_fast"].iloc[-4])
        slow_prev = float(d["ema_slow"].iloc[-4])
        slope_fast_pct = ((ema_fast / max(fast_prev, 1e-12)) - 1.0) * 100.0
        slope_slow_pct = ((ema_slow / max(slow_prev, 1e-12)) - 1.0) * 100.0
        ema_spread_pct = ((ema_fast - ema_slow) / max(close, 1e-12)) * 100.0

        recent = d.tail(max(self.swing_lookback + 2, 7))
        hh = float(recent["high"].iloc[-1] > recent["high"].median())
        hl = float(recent["low"].iloc[-1] > recent["low"].median())
        lh = float(recent["high"].iloc[-1] < recent["high"].median())
        ll = float(recent["low"].iloc[-1] < recent["low"].median())
        swing_bias = (hh + hl) - (lh + ll)

        if ema_fast > ema_slow and slope_fast_pct > 0 and slope_slow_pct >= 0 and swing_bias > 0:
            label: Trend = "bullish"
        elif ema_fast < ema_slow and slope_fast_pct < 0 and slope_slow_pct <= 0 and swing_bias < 0:
            label = "bearish"
        else:
            label = "neutral"

        return TrendState(
            label=label,
            ema_fast=ema_fast,
            ema_slow=ema_slow,
            ema_spread_pct=ema_spread_pct,
            slope_fast_pct=slope_fast_pct,
            slope_slow_pct=slope_slow_pct,
            swing_bias=swing_bias,
        )

    def _detect_impulse(self, d: pd.DataFrame) -> ImpulseState:
        candidates = d.tail(max(self.vol_period, 25)).copy()
        candidates["atr_multiple"] = np.where(candidates["atr"] > 0, candidates["body"] / candidates["atr"], 0.0)
        candidates["impulse_strength"] = (
            candidates["atr_multiple"].clip(lower=0)
            + candidates["body_zscore"].clip(lower=0)
            + (candidates["volume_ratio"] - 1.0).clip(lower=0)
        )

        row = candidates.iloc[int(candidates["impulse_strength"].argmax())]
        idx = int(row.name)
        if row["close"] > row["open"]:
            direction: Trend = "bullish"
        elif row["close"] < row["open"]:
            direction = "bearish"
        else:
            direction = "neutral"

        clv = float(row["close_loc"])
        clv_dir = clv >= 0.65 if direction == "bullish" else clv <= 0.35
        detected = bool(
            direction != "neutral"
            and float(row["atr_multiple"]) >= self.impulse_atr_multiple
            and float(row["body_zscore"]) >= self.impulse_body_zscore_min
            and clv_dir
        )

        return ImpulseState(
            detected=detected,
            direction=direction if detected else "neutral",
            candle_index=idx if detected else None,
            body=float(row["body"]) if detected else 0.0,
            range_size=float(row["range"]) if detected else 0.0,
            atr_multiple=float(row["atr_multiple"]) if detected else 0.0,
            body_zscore=float(row["body_zscore"]) if detected else 0.0,
            close_location_value=clv if detected else 0.5,
            volume_ratio=float(row["volume_ratio"]) if detected else 1.0,
        )

    def _evaluate_retracement(self, d: pd.DataFrame, impulse: ImpulseState) -> RetracementState:
        if not impulse.detected or impulse.candle_index is None:
            return RetracementState(ratio=None, quality="unknown", held_50pct=False, held_618=False)

        row = d.iloc[impulse.candle_index]
        last_close = float(d["close"].iloc[-1])
        impulse_high = float(row["high"])
        impulse_low = float(row["low"])
        impulse_range = max(impulse_high - impulse_low, 1e-12)

        if impulse.direction == "bullish":
            ratio = max(0.0, (impulse_high - last_close) / impulse_range)
        else:
            ratio = max(0.0, (last_close - impulse_low) / impulse_range)

        if ratio < 0.33:
            quality = "shallow"
        elif ratio < 0.66:
            quality = "moderate"
        else:
            quality = "deep"

        return RetracementState(
            ratio=ratio,
            quality=quality,
            held_50pct=ratio <= 0.50,
            held_618=ratio <= 0.618,
        )

    def _detect_compression(self, d: pd.DataFrame, impulse: ImpulseState) -> CompressionState:
        if not impulse.detected or impulse.candle_index is None:
            return CompressionState(detected=False, width_atr=None, realized_vol_ratio=None, note="no impulse")

        post = d.iloc[impulse.candle_index + 1 :].tail(self.compression_window)
        if len(post) < 3:
            return CompressionState(detected=False, width_atr=None, realized_vol_ratio=None, note="not enough post-impulse bars")

        width = float(post["high"].max() - post["low"].min())
        atr = float(d["atr"].iloc[-1])
        width_atr = width / max(atr, 1e-12)

        rv_now = float(post["realized_vol"].mean())
        prev_start = max(0, len(d) - self.compression_window * 2)
        prev_end = max(prev_start + 1, len(d) - self.compression_window)
        rv_prev = float(d["realized_vol"].iloc[prev_start:prev_end].mean() or 0.0)
        rv_ratio = 1.0 if rv_prev <= 0 else rv_now / rv_prev

        detected = width_atr <= self.compression_atr_max and rv_ratio <= 0.95
        note = "range + realized vol contracted" if detected else "post-impulse range still loose"
        return CompressionState(detected=detected, width_atr=width_atr, realized_vol_ratio=rv_ratio, note=note)

    def _detect_breakout(self, d: pd.DataFrame, trend: TrendState) -> BreakoutState:
        last = d.iloc[-1]
        close = float(last["close"])
        volume_ok = float(last["volume_ratio"]) >= self.breakout_volume_ratio_min

        swing_high = float(last["swing_high"]) if not pd.isna(last["swing_high"]) else None
        swing_low = float(last["swing_low"]) if not pd.isna(last["swing_low"]) else None

        if swing_high is not None and close > swing_high:
            return BreakoutState(
                active=True,
                direction="bullish",
                swing_level=swing_high,
                distance_from_level_pct=((close - swing_high) / max(close, 1e-12)) * 100.0,
                confirmed_by_volume=volume_ok,
            )
        if swing_low is not None and close < swing_low:
            return BreakoutState(
                active=True,
                direction="bearish",
                swing_level=swing_low,
                distance_from_level_pct=((swing_low - close) / max(close, 1e-12)) * 100.0,
                confirmed_by_volume=volume_ok,
            )

        return BreakoutState(
            active=False,
            direction=trend.label,
            swing_level=swing_high if trend.label == "bullish" else swing_low,
            distance_from_level_pct=0.0,
            confirmed_by_volume=volume_ok,
        )

    def _read_microstructure(self, d: pd.DataFrame) -> MicrostructureState:
        last = d.iloc[-1]

        obi = float(last["obi"]) if "obi" in d.columns and not pd.isna(last["obi"]) else 0.0
        funding = float(last["funding_rate"]) if "funding_rate" in d.columns and not pd.isna(last["funding_rate"]) else 0.0
        oi_delta = float(last["oi_delta_pct"]) if "oi_delta_pct" in d.columns and not pd.isna(last["oi_delta_pct"]) else 0.0
        vpin = float(last["vpin"]) if "vpin" in d.columns and not pd.isna(last["vpin"]) else 0.0
        ghost = float(last["ghost_intensity"]) if "ghost_intensity" in d.columns and not pd.isna(last["ghost_intensity"]) else 0.0

        return MicrostructureState(
            obi_bias=float(np.clip(obi, -1.0, 1.0)),
            funding_bias=float(np.clip(-funding * 20.0, -1.0, 1.0)),
            oi_bias=float(np.clip(oi_delta / 5.0, -1.0, 1.0)),
            vpin_risk=float(np.clip(vpin, 0.0, 1.0)),
            ghost_risk=float(np.clip(ghost / 2.0, 0.0, 1.0)),
        )

    def _map_levels(self, d: pd.DataFrame, impulse: ImpulseState) -> Dict[str, Optional[float]]:
        recent = d.tail(max(self.swing_lookback + 2, 8))
        levels: Dict[str, Optional[float]] = {
            "local_support": float(recent["low"].min()),
            "local_resistance": float(recent["high"].max()),
            "last_close": float(d["close"].iloc[-1]),
            "atr": float(d["atr"].iloc[-1]),
        }
        if impulse.detected and impulse.candle_index is not None:
            levels["impulse_high"] = float(d["high"].iloc[impulse.candle_index])
            levels["impulse_low"] = float(d["low"].iloc[impulse.candle_index])
        else:
            levels["impulse_high"] = None
            levels["impulse_low"] = None
        return levels

    def _make_decision(
        self,
        *,
        d: pd.DataFrame,
        trend: TrendState,
        impulse: ImpulseState,
        retracement: RetracementState,
        compression: CompressionState,
        breakout: BreakoutState,
        micro: MicrostructureState,
        levels: Dict[str, Optional[float]],
    ) -> ConfluenceDecision:
        base_score = 50.0
        boosts: list[str] = []
        warnings: list[str] = []
        trace: list[str] = []
        setup: Setup = "neutral"
        last_close = float(d["close"].iloc[-1])

        if trend.label == "bullish":
            base_score += 8.0
            boosts.append("trend_bullish")
        elif trend.label == "bearish":
            base_score += 8.0
            boosts.append("trend_bearish")
        else:
            warnings.append("trend_neutral")

        if impulse.detected:
            base_score += min(12.0, 4.0 * impulse.atr_multiple)
            trace.append(f"impulse={impulse.direction}:{impulse.atr_multiple:.2f}atr")
            if impulse.volume_ratio >= 1.2:
                base_score += 4.0
                boosts.append("impulse_volume_confirmed")
        else:
            base_score -= 8.0
            warnings.append("no_clean_impulse")

        if retracement.quality == "shallow":
            base_score += 10.0
            boosts.append("retracement_shallow")
        elif retracement.quality == "moderate":
            base_score += 4.0
            boosts.append("retracement_moderate")
        elif retracement.quality == "deep":
            base_score -= 9.0
            warnings.append("retracement_deep")

        if compression.detected:
            base_score += 8.0
            boosts.append("compression_detected")
        else:
            base_score -= 4.0
            warnings.append("no_compression")

        if breakout.active and breakout.confirmed_by_volume:
            base_score += 10.0
            boosts.append("breakout_confirmed")
        elif breakout.active:
            base_score += 3.0
            warnings.append("breakout_unconfirmed_volume")

        micro_delta = 0.0
        if trend.label != "neutral":
            aligned_sign = 1 if trend.label == "bullish" else -1
            if np.sign(micro.obi_bias) == aligned_sign:
                micro_delta += 6.0 * abs(micro.obi_bias)
            else:
                micro_delta -= 3.0 * abs(micro.obi_bias)
        micro_delta += 3.0 * max(micro.oi_bias, 0.0)
        micro_delta += 2.0 * max(micro.funding_bias, 0.0)
        micro_delta -= 8.0 * micro.vpin_risk
        micro_delta -= 10.0 * micro.ghost_risk

        if micro.vpin_risk >= 0.7:
            warnings.append("toxic_flow_vpin")
        if micro.ghost_risk >= 0.5:
            warnings.append("ghost_liquidity_risk")

        final_score = float(np.clip(base_score + micro_delta, 0.0, 100.0))
        score_delta = final_score - base_score

        if trend.label == "bullish" and impulse.direction == "bullish":
            if retracement.quality in {"shallow", "moderate"} and compression.detected:
                setup = "continuation"
            elif levels.get("impulse_low") is not None and last_close < float(levels["impulse_low"]):
                setup = "breakdown"
        elif trend.label == "bearish" and impulse.direction == "bearish":
            if retracement.quality in {"shallow", "moderate"} and compression.detected:
                setup = "continuation"
            elif levels.get("impulse_high") is not None and last_close > float(levels["impulse_high"]):
                setup = "reversal"
        elif compression.detected and abs(trend.ema_spread_pct) < 0.15:
            setup = "mean_revert"

        invalid_if_below: Optional[float] = None
        confirm_if_above: Optional[float] = None
        if impulse.direction == "bullish":
            invalid_if_below = levels.get("impulse_low") or levels.get("local_support")
            confirm_if_above = levels.get("local_resistance")
        elif impulse.direction == "bearish":
            invalid_if_below = levels.get("local_support")
            confirm_if_above = levels.get("impulse_high") or levels.get("local_resistance")

        allow = bool(
            final_score >= 62.0
            and setup in {"continuation", "mean_revert"}
            and "ghost_liquidity_risk" not in warnings
        )

        confidence = float(np.clip(final_score / 100.0, 0.0, 1.0))
        trace.append(f"setup={setup}")
        trace.append(f"trend={trend.label}")
        trace.append(f"score={final_score:.2f}")

        return ConfluenceDecision(
            allow=allow,
            setup=setup,
            trend=trend.label,
            confidence=confidence,
            base_score=round(base_score, 2),
            final_score=round(final_score, 2),
            score_delta=round(score_delta, 2),
            invalid_if_below=invalid_if_below,
            confirm_if_above=confirm_if_above,
            warnings=warnings,
            boosts=boosts,
            trace=trace,
        )


chart_confluence = ChartConfluenceEngine()
