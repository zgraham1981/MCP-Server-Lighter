"""Configuration loader."""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path

if sys.version_info >= (3, 11):
    import tomllib
    _LOAD = tomllib.loads
else:  # pragma: no cover
    import tomli as _tomli
    _LOAD = _tomli.loads


def default_config_path() -> Path:
    from platformdirs import user_config_dir
    return Path(user_config_dir("lighter-mcp", appauthor=False)) / "config.toml"


DEFAULT_TOML = """\
[network]
rpc = "https://mainnet.optimism.io"
timeout_seconds = 10

[campaign]
points_per_dollar    = 2.0
maker_bonus_pct      = 0.20
liquidity_multiplier = 1.25
campaign_days        = 90
tiers = [
    { name = "BRONZE",   volume = 50000 },
    { name = "SILVER",   volume = 150000 },
    { name = "GOLD",     volume = 300000 },
    { name = "PLATINUM", volume = 600000 },
]

[default_wallet]
address = ""
"""


@dataclass(frozen=True)
class TierSpec:
    name: str
    volume: float


@dataclass(frozen=True)
class NetworkConfig:
    rpc: str = "https://mainnet.optimism.io"
    timeout_seconds: int = 10


@dataclass(frozen=True)
class CampaignConfig:
    points_per_dollar: float = 2.0
    maker_bonus_pct: float = 0.20
    liquidity_multiplier: float = 1.25
    campaign_days: int = 90
    tiers: tuple[TierSpec, ...] = (
        TierSpec("BRONZE", 50_000), TierSpec("SILVER", 150_000),
        TierSpec("GOLD", 300_000), TierSpec("PLATINUM", 600_000),
    )


@dataclass(frozen=True)
class DefaultWallet:
    address: str = ""


@dataclass(frozen=True)
class Config:
    network: NetworkConfig = field(default_factory=NetworkConfig)
    campaign: CampaignConfig = field(default_factory=CampaignConfig)
    default_wallet: DefaultWallet = field(default_factory=DefaultWallet)
    demo: bool = False

    @classmethod
    def load(cls, path: Path, *, demo: bool = False) -> Config:
        path = Path(path)
        if not path.exists():
            try:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(DEFAULT_TOML, encoding="utf-8")
            except OSError:
                pass
        raw = _LOAD(path.read_text(encoding="utf-8")) if path.exists() else {}
        camp_raw = raw.get("campaign", {})
        tiers = tuple(TierSpec(t["name"], float(t["volume"])) for t in camp_raw.get("tiers", ()))
        return cls(
            network=NetworkConfig(**raw.get("network", {})),
            campaign=CampaignConfig(
                points_per_dollar=camp_raw.get("points_per_dollar", 2.0),
                maker_bonus_pct=camp_raw.get("maker_bonus_pct", 0.20),
                liquidity_multiplier=camp_raw.get("liquidity_multiplier", 1.25),
                campaign_days=camp_raw.get("campaign_days", 90),
                tiers=tiers or CampaignConfig().tiers,
            ),
            default_wallet=DefaultWallet(**raw.get("default_wallet", {})),
            demo=demo,
        )
