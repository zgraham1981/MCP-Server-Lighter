"""MCP tool definitions for the Lighter server.

Tool functions are plain, MCP-free Python functions returning JSON-friendly dicts so they
can be unit-tested headlessly. :func:`build_server` registers them on a ``FastMCP`` instance
at runtime (the ``mcp`` SDK is imported lazily there).
"""

from __future__ import annotations

from mcp_lighter.config import Config
from mcp_lighter.core import Analytics
from mcp_lighter.core.mock_data import (
    demo_criteria, demo_entries, demo_liquidity, demo_markets, demo_rank,
    demo_tasks, demo_wallet,
)

# Module-level state. In demo mode the server answers from the bundled dataset; in live
# mode a future build would fetch public on-chain data for the given wallet.
_state: dict = {"config": None}


def _config() -> Config:
    return _state["config"] or Config(demo=True)


def _analytics() -> Analytics:
    c = _config().campaign
    return Analytics(points_per_dollar=c.points_per_dollar,
                     maker_bonus_pct=c.maker_bonus_pct,
                     liquidity_multiplier=c.liquidity_multiplier)


def _resolve_wallet(wallet: str | None) -> str:
    if wallet:
        return wallet
    cfg = _config()
    return cfg.default_wallet.address or demo_wallet()


def _tier_specs():
    # TierSpec already exposes .name/.volume, which Analytics duck-types as a Tier.
    return list(_config().campaign.tiers) or demo_tiers()


# --------------------------------------------------------------------- tools

def get_volume(wallet: str | None = None) -> dict:
    """Today / 7-day / 30-day / campaign volume with maker/taker split."""
    w = _resolve_wallet(wallet)
    agg = _analytics().aggregate(demo_entries())
    return {"wallet": w, **agg,
            "maker_pct": round(agg["today_maker_ratio"] * 100, 1)}


def get_points(wallet: str | None = None) -> dict:
    """Estimated campaign points with maker-bonus & liquidity multiplier breakdown."""
    w = _resolve_wallet(wallet)
    return {"wallet": w, **_analytics().estimate_points(demo_entries(), demo_liquidity())}


def get_rank(wallet: str | None = None) -> dict:
    """Leaderboard position with 24h delta."""
    return demo_rank(_resolve_wallet(wallet))


def get_markets() -> dict:
    """Available Lighter orderbook markets."""
    return {"markets": demo_markets(), "count": len(demo_markets())}


def get_liquidity(wallet: str | None = None) -> dict:
    """Liquidity provided: days + tier."""
    liq = demo_liquidity()
    return {"wallet": _resolve_wallet(wallet), "days_provided": liq.days_provided,
            "tier": liq.tier}


def get_eligibility(wallet: str | None = None) -> dict:
    """Airdrop tier + satisfied/missing criteria."""
    w = _resolve_wallet(wallet)
    agg = _analytics().aggregate(demo_entries())
    pts = _analytics().estimate_points(demo_entries(), demo_liquidity())
    tiers = _tier_specs()
    tasks_done = [t.label for t in demo_tasks() if t.done]
    return {"wallet": w, **_analytics().eligibility(
        agg["campaign"], tiers, tasks_done, demo_criteria(),
        pts["maker_ratio"], demo_liquidity().days_provided,
    )}


def list_tasks(wallet: str | None = None) -> dict:
    """Farming task checklist with completion state."""
    tasks = demo_tasks()
    return {"wallet": _resolve_wallet(wallet), "tasks": [
        {"label": t.label, "category": t.category, "done": t.done, "hint": t.hint}
        for t in tasks
    ], "done": sum(1 for t in tasks if t.done), "total": len(tasks)}


# Available tool registry (name -> callable), used by the CLI headless mode and tests.
TOOLS = {
    "get_volume": get_volume,
    "get_points": get_points,
    "get_rank": get_rank,
    "get_markets": get_markets,
    "get_liquidity": get_liquidity,
    "get_eligibility": get_eligibility,
    "list_tasks": list_tasks,
}


def build_server(config: Config):  # pragma: no cover - requires the mcp SDK
    """Build and return a FastMCP server with all tools registered."""
    from mcp.server.fastmcp import FastMCP  # local import: keeps the SDK optional

    _state["config"] = config
    mcp = FastMCP("lighter")
    for name, fn in TOOLS.items():
        mcp.tool(name=name)(fn)
    return mcp
