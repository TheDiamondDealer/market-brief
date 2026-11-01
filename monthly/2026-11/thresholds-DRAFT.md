# Trigger Thresholds — November 2026 (DRAFT)

> **AWAITING HUMAN APPROVAL.** Proposed replacement for `thresholds.md`. The live thresholds remain unchanged.

**Calibration date:** 2 November 2026  
**Protocol:** A close through a level is an alert. A trigger becomes actionable only when the stated confirmation cluster is present. Intraday moves alone do not qualify.

## Headline triggers

| Variable | Warning zone | Trigger | Confirmation / invalidation |
|---|---:|---:|---|
| Gold | $3,850–3,950/oz | Downside < $3,850; repair > $4,000 | Confirm downside with DXY ≥101.5, real yield ≥2.65% or liquidation evidence; invalidate below-$3,850 signal on recovery >$3,950 |
| Brent | $108–115/bbl | >$118; acute override >$120 | Confirm with impaired flows/freight/inventory; invalidate on < $105 plus verified repair |
| ASX 200 | 8,800–8,950 | <8,780 or >9,000 | Confirm downside with weak breadth/AUD/credit; confirm upside with materials plus domestic breadth |
| Fed Dec hike probability | 70–85% | ≥90% or +15ppt in five sessions | Confirm with inflation or Fed guidance; invalidate <60% |
| RBA Nov hike probability | 75–90% | ≥90% or +15ppt | Event-specific; invalidate <50% or dovish no-hike |
| USDJPY | 155–160 | >160.5 stress; <154 unwind | Confirm upside with intervention rhetoric/volatility; downside with rising JGB yields and carry weakness |
| US 10-year nominal | 4.85–5.05% | Two closes >5.10%; acute >5.25% | Confirm with real yields/DXY/inflation; relief <4.75% without credit shock |

## Precious metals

| Asset | Warning zone | Trigger | Notes |
|---|---:|---:|---|
| Silver | $48–51/oz | <48 downside; >52 repair | Require gold and industrial confirmation |
| Platinum | $1,400–1,500/oz | <1,400 or >1,550 | Supply event can override auto-cycle weakness |
| Palladium | $950–1,025/oz | <950 or >1,075 | Treat as thin/liquidity-sensitive |

## Battery and transition commodities

| Asset | Warning zone | Trigger | Notes |
|---|---:|---:|---|
| Copper | $6.35–6.55/lb | <6.30 or >6.65 | Upside needs China orders, premiums or inventory draw |
| Lithium carbonate | CNY 90–100k/t | <90k or >105k | Upside needs realised supply discipline |
| Nickel | $15.0–15.7k/t | <15.0k or >16.2k | Upside needs verified Indonesian output reduction |
| Uranium | $90–94/lb | >95 or <88 | Contracting and term premiums are primary confirmation |

## Bulk commodities

| Asset | Warning zone | Trigger | Notes |
|---|---:|---:|---|
| Dalian iron ore | CNY 660–690/t | <660 or >710 | Require steel margins, inventories and property/activity confirmation |
| Thermal coal | $148–155/t | >158 or <145 | Gas substitution and logistics are primary drivers |
| Coking coal | N/V | No hard trigger | Benchmark continuity is insufficient; use physical assessments and steel margins |

## Energy

| Asset | Warning zone | Trigger | Notes |
|---|---:|---:|---|
| WTI | $98–104/bbl | >106 or <95 | Cross-check Brent spread and US inventory |
| European TTF | €95–105/MWh | >110 or <90 | €85 is stronger relief; physical LNG and storage confirmation required |
| Henry Hub | $2.75–3.10/mmBtu | >3.20 or <2.65 | Distinguishes US domestic gas from global scarcity |

## Equities, rates and FX

| Variable | Warning zone | Trigger | Confirmation / invalidation |
|---|---:|---:|---|
| S&P 500 | 7,500–7,650 | <7,480 or >7,750 | Downside requires breadth/credit; upside requires equal-weight participation |
| Nasdaq Composite | 25,200–25,800 | <25,200; repair >26,000 | Full disorder also needs DXY >102.2 plus breadth/credit/carry; >26,400 invalidates immediate disorder |
| DXY | 101.5–102.2 | >102.2; relief <101.0 | Pair with yields, commodities and funding stress |
| US 10-year real yield | 2.55–2.70% | >2.75% or <2.45% | Interpret lower yield with credit/growth context |
| AUDUSD | 0.695–0.705 | <0.695 or >0.710 | Cross-check RBA pricing, China and commodities |
| AUDJPY | 109–112 | <109 | Carry/risk signal; validate with USDJPY and ASX breadth |
| USDCNY | 6.62–6.70 | >6.72 or <6.60 | Policy or fixing intervention can dominate spot |

## Policy-specific boundaries

| Policy | Watch | Trigger | Invalidation |
|---|---|---|---|
| Federal Reserve | December hike pricing and 18 Nov minutes | ≥90% hike probability or +15ppt in five sessions | <60% without a credit accident |
| RBA | 3 Nov decision; 17 Nov minutes; 25 Nov CPI | Hike or ≥90% next-meeting hike probability | Dovish hold plus inflation downside |
| BOJ | 10 Nov summary; 18 Dec meeting | Market majority for December hike plus rising JGB yields/JPY response | USDJPY orderly below160.5 and delayed normalisation guidance |
| PBOC/China | Credit, fiscal and property support | Broad easing plus improved orders, housing activity and commodity imports | Announcements without transmission |

## Relationship overrides

### Precious-metals haven relationship

Gold above $4,100 while real yields rise and energy worsens restores haven leadership. Gold below $3,850 despite falling real yields confirms a positioning/liquidity fracture until $4,000 is reclaimed.

### Yen carry relationship

USDJPY above 160.5 is imported-inflation/intervention stress. USDJPY below 154 with rising JGB yields and weak global breadth is a carry-unwind signal.

### China transmission

Copper or iron ore upside does not count as China recovery without improved new orders, steel margins, property activity or physical imports. Lithium/nickel rallies need realised supply discipline.

### Product/LNG-led inflation

TTF above €110 or refined-product freight stress can escalate the inflation regime even if crude stalls. Relief requires both lower prices and verified logistics normalisation.

### AI concentration

Nasdaq weakness counts as systemic only when capex/free-cash-flow deterioration spreads into broad breadth, credit or funding. Strong equal-weight performance invalidates an index-only disorder call.

## Physical confirmation checklist

- Gulf crude, product and LPG export volumes
- Tanker freight, insurance and voyage duration
- OECD/commercial inventories and refinery/product margins
- China steel margins, port stocks and commodity premiums
- Indonesian realised nickel output and approvals
- Uranium term-contract volumes and premiums

## Data caveats

- Month-end commodity closes can vary by venue and contract; use the same benchmark before testing a threshold.
- Credit widening, breadth or physical-flow evidence that cannot be verified is **N/V**, not assumed.
- Policy probabilities are snapshots and should be time-stamped in every brief.

## Sources

- [IEA Oil Market Report](https://www.iea.org/reports/oil-market-report-october-2026)
- [EIA Short-Term Energy Outlook](https://www.eia.gov/outlooks/steo/)
- [Federal Reserve calendar](https://www.federalreserve.gov/newsevents/2026-november.htm)
- [RBA calendar](https://www.rba.gov.au/schedules-events/calendar/)
- [ABS November release calendar](https://www.abs.gov.au/release-calendar/future-releases/202611)
- [China NBS 2026 release calendar](https://www.stats.gov.cn/english/PressRelease/ReleaseCalendar/)

