"""Typed models for Lighter MCP payloads (plain, JSON-serialisable)."""

from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import date, datetime, timezone


@dataclass(frozen=True)
class VolumeEntry:
    day: date
    maker_usd: float
    taker_usd: float

    @property
    def total(self) -> float:
        return self.maker_usd + self.taker_usd

    @property
    def maker_ratio(self) -> float:
        return (self.maker_usd / self.total) if self.total > 0 else 0.0


@dataclass(frozen=True)
class LiquidityRecord:
    days_provided: int
    tier: int


@dataclass(frozen=True)
class Tier:
    name: str
    volume: float


@dataclass(frozen=True)
class Task:
    key: str
    label: str
    category: str
    done: bool = False
    hint: str = ""


def today_utc() -> date:
    return datetime.now(tz=timezone.utc).date()


def as_dict(obj: object) -> dict:
    """Best-effort JSON-friendly dict conversion (handles date → isoformat)."""
    d = asdict(obj) if hasattr(obj, "__dataclass_fields__") else dict(obj)
    out: dict = {}
    for k, v in d.items():
        if isinstance(v, date):
            out[k] = v.isoformat()
        elif hasattr(v, "__dataclass_fields__"):
            out[k] = as_dict(v)
        elif isinstance(v, (list, tuple)):
            out[k] = [as_dict(i) if hasattr(i, "__dataclass_fields__")
                      else (i.isoformat() if isinstance(i, date) else i) for i in v]
        else:
            out[k] = v
    return out
