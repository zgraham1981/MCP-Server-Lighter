"""Volume aggregation + points estimation + tier logic — pure, no MCP import."""

from __future__ import annotations

from datetime import date, timedelta

from mcp_lighter.core.models import LiquidityRecord, Tier, VolumeEntry, today_utc


class Analytics:
    def __init__(self, points_per_dollar: float = 2.0,
                 maker_bonus_pct: float = 0.20,
                 liquidity_multiplier: float = 1.25) -> None:
        self.points_per_dollar = points_per_dollar
        self.maker_bonus_pct = maker_bonus_pct
        self.liquidity_multiplier = liquidity_multiplier

    def aggregate(self, entries: list[VolumeEntry], *, today: date | None = None) -> dict:
        today = today or today_utc()
        by_day: dict[date, VolumeEntry] = {}
        for e in entries:
            prev = by_day.get(e.day)
            if prev is None:
                by_day[e.day] = e
            else:
                by_day[e.day] = VolumeEntry(e.day, prev.maker_usd + e.maker_usd,
                                            prev.taker_usd + e.taker_usd)

        def total(d: VolumeEntry) -> float:
            return d.total

        today_e = by_day.get(today)
        vol_7 = sum(total(by_day[d]) for d in by_day if today - timedelta(days=7) < d <= today)
        vol_30 = sum(total(by_day[d]) for d in by_day if today - timedelta(days=30) < d <= today)
        campaign = sum(total(e) for e in by_day.values())
        return {
            "today_total": today_e.total if today_e else 0.0,
            "today_maker_ratio": today_e.maker_ratio if today_e else 0.0,
            "vol_7d": vol_7, "vol_30d": vol_30, "campaign": campaign,
        }

    def estimate_points(self, entries: list[VolumeEntry],
                        liquidity: LiquidityRecord) -> dict:
        agg = self.aggregate(entries)
        total_vol = agg["campaign"]
        maker_vol = sum(e.maker_usd for e in entries)
        maker_ratio = (maker_vol / total_vol) if total_vol > 0 else 0.0
        base = total_vol * self.points_per_dollar
        maker_bonus = maker_ratio * self.maker_bonus_pct
        liq_mult = self.liquidity_multiplier if liquidity.days_provided > 0 else 1.0
        total_pts = base * (1.0 + maker_bonus) * liq_mult
        return {
            "total_points": total_pts, "base_points": base,
            "maker_ratio": maker_ratio, "maker_bonus_pct": maker_bonus,
            "liquidity_multiplier": liq_mult, "campaign_volume": total_vol,
        }

    @staticmethod
    def tier_for(volume: float, tiers: list[Tier]) -> dict:
        ordered = sorted(tiers, key=lambda t: t.volume)
        current: Tier | None = None
        nxt: Tier | None = None
        for t in ordered:
            if volume >= t.volume:
                current = t
            elif nxt is None:
                nxt = t
        if current is None and ordered:
            target = ordered[0].volume
            progress = (volume / target) if target else 0.0
        elif nxt is not None:
            base, target = current.volume, nxt.volume
            progress = (volume - base) / (target - base) if target > base else 1.0
        else:
            progress = 1.0
        return {
            "tier": current.name if current else None,
            "next_tier": nxt.name if nxt else None,
            "progress_pct": round(max(0.0, min(1.0, progress)) * 100, 1),
            "volume": volume,
        }

    @staticmethod
    def eligibility(volume: float, tiers: list[Tier],
                    tasks_done: list[str], criteria: list[str],
                    maker_ratio: float, liquidity_days: int) -> dict:
        tier_info = Analytics.tier_for(volume, tiers)
        satisfied: list[str] = []
        missing: list[str] = []
        for c in criteria:
            low = c.lower()
            auto = any(t.name.lower() in low and volume >= t.volume for t in tiers)
            if ("maker" in low and maker_ratio >= 0.5):
                auto = True
            if ("liquidity" in low and "30" in low and liquidity_days >= 30):
                auto = True
            if c in tasks_done or auto:
                satisfied.append(c)
            else:
                missing.append(c)
        return {**tier_info, "satisfied": satisfied, "missing": missing}
