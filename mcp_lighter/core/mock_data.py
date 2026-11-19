"""Deterministic demo dataset for ``--demo`` mode."""

from __future__ import annotations

from datetime import date, timedelta

from mcp_lighter.core.models import LiquidityRecord, Task, Tier, VolumeEntry, today_utc

_WALLET = "0x9fa1b2c3d4e5f60718293a4b5c6d7e8f9000c310"

_TIERS = [
    Tier("BRONZE", 50_000), Tier("SILVER", 150_000),
    Tier("GOLD", 300_000), Tier("PLATINUM", 600_000),
]

_TASKS = [
    Task("connect_wallet", "Wallet connected", "social", True),
    Task("follow_socials", "Follow @lighter_xyz", "social", True),
    Task("maker_ratio_50", "Maker ratio ≥ 50%", "volume", True),
    Task("volume_bronze", "Reach BRONZE volume tier", "volume", True),
    Task("liquidity_30d", "Provide liquidity 30 days", "liquidity", False),
    Task("refer_3", "Refer 3 friends", "referral", False),
]

_CRITERIA = [
    "Volume ≥ $50k", "Volume ≥ $250k", "Maker ratio ≥ 50%",
    "7-day activity streak", "Liquidity ≥ 30d", "Refer 3 friends",
]

_MARKETS = [
    {"symbol": "ETH-USDC", "side": "both", "tier": "2", "book_depth_usd": 1_240_000},
    {"symbol": "WBTC-USDC", "side": "both", "tier": "2", "book_depth_usd": 880_000},
    {"symbol": "ARB-USDC", "side": "both", "tier": "3", "book_depth_usd": 320_000},
    {"symbol": "OP-USDC", "side": "both", "tier": "3", "book_depth_usd": 290_000},
]


def demo_wallet() -> str:
    return _WALLET


def demo_tiers() -> list[Tier]:
    return list(_TIERS)


def demo_tasks() -> list[Task]:
    return list(_TASKS)


def demo_criteria() -> list[str]:
    return list(_CRITERIA)


def demo_markets() -> list[dict]:
    return [dict(m) for m in _MARKETS]


def demo_liquidity() -> LiquidityRecord:
    return LiquidityRecord(days_provided=21, tier=2)


def demo_entries(days: int = 38) -> list[VolumeEntry]:
    today = today_utc()
    out: list[VolumeEntry] = []
    state = 2024
    for i in range(days):
        state = (1664525 * state + 1013904223) & 0x7FFFFFFF
        rnd = state / 0x7FFFFFFF
        day = today - timedelta(days=days - 1 - i)
        total = 1500 + rnd * 3500
        if rnd > 0.85:
            total += 2500
        maker_ratio = 0.55 + rnd * 0.15
        maker = total * maker_ratio
        taker = total - maker
        out.append(VolumeEntry(day=day, maker_usd=round(maker, 2), taker_usd=round(taker, 2)))
    return out


def demo_rank(wallet: str) -> dict:
    return {"wallet": wallet, "rank": 2041, "rank_delta_24h": 51, "direction": "up"}
