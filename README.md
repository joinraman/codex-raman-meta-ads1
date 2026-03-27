# Meta Ads Insights Tool

A lightweight Python CLI that turns a Meta Ads Manager CSV export into a clear performance report with:
- KPI summary
- campaign-level insights
- concrete optimization next steps

## Quick start

```bash
python3 ads_insights_tool.py sample_meta_ads.csv -o report.md
```

Then share `report.md` with your team/stakeholders.

## Input format

The script expects a CSV with a `campaign_name` (or `campaign`) column, and supports these metrics:
- `spend`
- `impressions`
- `clicks`
- `purchases` (optional)
- `purchase_value` (optional)
- `leads` (optional)

It also accepts common Meta column name variants like:
- `Campaign name`
- `Amount spent`
- `Link clicks`
- `Website purchases`

## Output

The report includes:
1. Account summary (spend, CTR, CPC, CPM, CPA, ROAS)
2. Top/bottom campaign insights
3. Recommended optimization actions (scale winners, trim weak campaigns, creative/funnel actions)

## Notes

- This starter focuses on campaign-level analysis from exported CSVs.
- Next upgrade ideas: ad set/ad-level breakdowns, time-series trend analysis, Slack/Email auto-share, and LLM narrative tuning.
