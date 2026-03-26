#!/usr/bin/env python3
"""Generate a Meta Ads performance summary + optimization plan from an exported CSV.

Expected columns (case-insensitive):
- campaign_name (or campaign)
- spend
- impressions
- clicks
- purchases (optional)
- purchase_value (optional)
- leads (optional)

The script outputs:
1) account-level KPI summary
2) top/bottom campaign insights
3) practical optimization next steps
"""

from __future__ import annotations

import argparse
import csv
import math
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List


ALIAS_MAP = {
    "campaign": "campaign_name",
    "campaign name": "campaign_name",
    "amount spent (usd)": "spend",
    "amount spent": "spend",
    "link clicks": "clicks",
    "website purchases": "purchases",
    "purchases conversion value": "purchase_value",
    "results": "leads",
}


@dataclass
class CampaignMetrics:
    name: str
    spend: float = 0.0
    impressions: int = 0
    clicks: int = 0
    purchases: int = 0
    purchase_value: float = 0.0
    leads: int = 0

    @property
    def ctr(self) -> float:
        return (self.clicks / self.impressions) if self.impressions else 0.0

    @property
    def cpc(self) -> float:
        return (self.spend / self.clicks) if self.clicks else math.inf

    @property
    def cpm(self) -> float:
        return (self.spend / self.impressions * 1000) if self.impressions else math.inf

    @property
    def cpa(self) -> float:
        conv = self.conversions
        return (self.spend / conv) if conv else math.inf

    @property
    def roas(self) -> float:
        return (self.purchase_value / self.spend) if self.spend else 0.0

    @property
    def conversions(self) -> int:
        return self.purchases + self.leads


def _clean_header(header: str) -> str:
    normalized = header.strip().lower().replace("_", " ")
    normalized = " ".join(normalized.split())
    return ALIAS_MAP.get(normalized, normalized.replace(" ", "_"))


def _to_int(value: str) -> int:
    if not value:
        return 0
    return int(float(value.replace(",", "").strip()))


def _to_float(value: str) -> float:
    if not value:
        return 0.0
    return float(value.replace(",", "").replace("$", "").strip())


def load_campaigns(csv_path: Path) -> List[CampaignMetrics]:
    grouped: Dict[str, CampaignMetrics] = defaultdict(lambda: CampaignMetrics(name=""))

    with csv_path.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            raise ValueError("CSV appears to have no header row.")

        columns = {_clean_header(c): c for c in reader.fieldnames}

        campaign_col = columns.get("campaign_name")
        if not campaign_col:
            raise ValueError("CSV must include campaign_name (or campaign) column.")

        for row in reader:
            name = (row.get(campaign_col) or "Unknown Campaign").strip()
            item = grouped[name]
            item.name = name

            if "spend" in columns:
                item.spend += _to_float(row.get(columns["spend"], ""))
            if "impressions" in columns:
                item.impressions += _to_int(row.get(columns["impressions"], ""))
            if "clicks" in columns:
                item.clicks += _to_int(row.get(columns["clicks"], ""))
            if "purchases" in columns:
                item.purchases += _to_int(row.get(columns["purchases"], ""))
            if "purchase_value" in columns:
                item.purchase_value += _to_float(row.get(columns["purchase_value"], ""))
            if "leads" in columns:
                item.leads += _to_int(row.get(columns["leads"], ""))

    campaigns = list(grouped.values())
    if not campaigns:
        raise ValueError("CSV contains no campaign rows.")
    return campaigns


def summarize_account(campaigns: Iterable[CampaignMetrics]) -> CampaignMetrics:
    total = CampaignMetrics(name="ACCOUNT")
    for c in campaigns:
        total.spend += c.spend
        total.impressions += c.impressions
        total.clicks += c.clicks
        total.purchases += c.purchases
        total.purchase_value += c.purchase_value
        total.leads += c.leads
    return total


def _fmt_money(value: float) -> str:
    if math.isinf(value):
        return "n/a"
    return f"${value:,.2f}"


def _fmt_pct(value: float) -> str:
    return f"{value * 100:.2f}%"


def _fmt_num(value: float) -> str:
    if math.isinf(value):
        return "n/a"
    return f"{value:.2f}"


def generate_report(campaigns: List[CampaignMetrics]) -> str:
    account = summarize_account(campaigns)

    by_spend = sorted(campaigns, key=lambda c: c.spend, reverse=True)
    by_roas = sorted(campaigns, key=lambda c: c.roas, reverse=True)
    by_cpa = sorted(campaigns, key=lambda c: c.cpa)

    top_roas = [c for c in by_roas if c.spend > 0][:3]
    worst_roas = [c for c in reversed(by_roas) if c.spend > 0][:3]

    lines = []
    lines.append("# Meta Ads Performance Report")
    lines.append("")
    lines.append("## 1) Account Summary")
    lines.append(f"- Spend: {_fmt_money(account.spend)}")
    lines.append(f"- Impressions: {account.impressions:,}")
    lines.append(f"- Clicks: {account.clicks:,}")
    lines.append(f"- CTR: {_fmt_pct(account.ctr)}")
    lines.append(f"- CPC: {_fmt_money(account.cpc)}")
    lines.append(f"- CPM: {_fmt_money(account.cpm)}")
    lines.append(f"- Conversions (Purchases + Leads): {account.conversions:,}")
    lines.append(f"- CPA: {_fmt_money(account.cpa)}")
    lines.append(f"- Purchase Value: {_fmt_money(account.purchase_value)}")
    lines.append(f"- ROAS: {_fmt_num(account.roas)}")

    lines.append("")
    lines.append("## 2) Campaign Insights")
    lines.append("### Top campaigns by spend")
    for c in by_spend[:5]:
        lines.append(
            f"- **{c.name}** | Spend {_fmt_money(c.spend)} | CTR {_fmt_pct(c.ctr)} | CPA {_fmt_money(c.cpa)} | ROAS {_fmt_num(c.roas)}"
        )

    lines.append("")
    lines.append("### Best ROAS campaigns")
    for c in top_roas:
        lines.append(
            f"- **{c.name}**: ROAS {_fmt_num(c.roas)} with {_fmt_money(c.spend)} spend and {c.conversions} conversions."
        )

    lines.append("")
    lines.append("### Lowest ROAS campaigns")
    for c in worst_roas:
        lines.append(
            f"- **{c.name}**: ROAS {_fmt_num(c.roas)} with CPA {_fmt_money(c.cpa)}."
        )

    lines.append("")
    lines.append("## 3) Recommended Next Steps")

    median_roas = by_roas[len(by_roas) // 2].roas if by_roas else 0.0
    strong = [c for c in campaigns if c.roas >= max(1.5, median_roas)]
    weak = [c for c in campaigns if c.spend > 0 and c.roas < max(1.0, median_roas * 0.75)]

    if strong:
        names = ", ".join(c.name for c in strong[:3])
        lines.append(f"1. Scale budget +10-20% on strong ROAS campaigns: {names}.")
    else:
        lines.append("1. No clear winners yet; keep budgets stable and test new creatives before scaling.")

    if weak:
        names = ", ".join(c.name for c in weak[:3])
        lines.append(f"2. Reduce spend or pause weak campaigns: {names}.")
    else:
        lines.append("2. No obvious weak campaigns by ROAS; prioritize creative testing for further gains.")

    high_cpa = sorted(campaigns, key=lambda c: c.cpa, reverse=True)
    if high_cpa and not math.isinf(high_cpa[0].cpa):
        lines.append(
            f"3. Optimize conversion funnel for {high_cpa[0].name} (highest CPA: {_fmt_money(high_cpa[0].cpa)})."
        )
    else:
        lines.append("3. Ensure conversion tracking is complete (pixel + CAPI + event prioritization).")

    lines.append("4. Launch at least 2 fresh creatives this week to counter ad fatigue.")
    lines.append("5. Review audience overlap and exclude recent purchasers from prospecting ad sets.")

    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate Meta Ads insights + optimization plan from CSV export."
    )
    parser.add_argument("input_csv", type=Path, help="Path to Meta Ads export CSV")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("meta_ads_report.md"),
        help="Output markdown report path (default: meta_ads_report.md)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    campaigns = load_campaigns(args.input_csv)
    report = generate_report(campaigns)
    args.output.write_text(report, encoding="utf-8")
    print(f"Report generated: {args.output}")


if __name__ == "__main__":
    main()
