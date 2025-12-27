from __future__ import annotations
from dataclasses import dataclass
from typing import Literal, Optional, Dict, Any

Regime = Literal["expansion", "slowdown", "contraction", "recovery", "unknown"]
VolRegime = Literal["compressing", "expanding", "stable", "unknown"]
Decision = Literal["ALLOW", "BLOCK"]

@dataclass(frozen=True)
class MacroRegimeState:
    regime: Regime
    confidence: float
    details: Dict[str, Any]

@dataclass(frozen=True)
class ValuationState:
    # FX anchor: gap is % misvaluation vs fair value (positive = undervalued vs USD if defined that way in your data)
    gap_pct: Optional[float]
    reliability: Literal["high", "anchor", "low", "unknown"]
    dominant_driver: Optional[Literal["inflation", "tot", "productivity", "mixed"]]
    details: Dict[str, Any]

@dataclass(frozen=True)
class TrendState:
    direction: Literal["up", "down", "flat"]
    strength: float
    persistence: float
    vol_regime: VolRegime
    allowed: bool
    details: Dict[str, Any]

@dataclass(frozen=True)
class TradeDecision:
    asset: str
    decision: Decision
    score: float
    bias: Literal["long", "short", "flat"]
    rationale: str
    invalidation: str

