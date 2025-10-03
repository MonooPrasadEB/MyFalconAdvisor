# Compliance Policies
- **Version**: v1
- **Checksum**: `574581893ffb58ccd4ad501a6b8cb85c88ac86a2250e61585463665e4260e9cb`
- **Generated**: 2025-10-03T03:53:49.007054

## CONC-001 — Position Concentration Limit
- Source: **SEC**
- Severity: **warning**
- Applies To: individual, institutional
- Effective: 2000-01-01 00:00:00+00:00 | Last Updated: 2025-10-03 03:44:08.024780
- Params: `{"max_position": 0.25}`

Individual position should not exceed threshold of portfolio value

## CONC-002 — Sector Concentration Limit
- Source: **SEC**
- Severity: **warning**
- Applies To: individual, institutional
- Effective: 2000-01-01 00:00:00+00:00 | Last Updated: 2025-10-03 03:44:08.024780
- Params: `{"max_sector": 0.4}`

Single sector allocation should not exceed threshold of portfolio

## CONC-003 — Concentrated Position Disclosure
- Source: **FINRA**
- Severity: **major**
- Applies To: advisor
- Effective: 2012-07-09 00:00:00+00:00 | Last Updated: 2025-10-03 03:44:08.024780
- Params: `{}`

Must disclose risks for concentrated positions

## PENNY-001 — Penny Stock Disclosure
- Source: **SEC**
- Severity: **advisory**
- Applies To: individual, advisor
- Effective: 2001-07-09 00:00:00+00:00 | Last Updated: 2025-10-03 03:44:08.024780
- Params: `{"min_price": 5.0}`

Trades in penny stocks (< $5) require heightened suitability and disclosure

## SUIT-001 — Suitability Rule 2111
- Source: **FINRA**
- Severity: **critical**
- Applies To: advisor
- Effective: 2010-07-09 00:00:00+00:00 | Last Updated: 2025-10-03 03:44:08.024780
- Params: `{}`

Recommendations must be suitable for client based on profile

## SUIT-002 — Quantitative Suitability
- Source: **FINRA**
- Severity: **critical**
- Applies To: advisor
- Effective: 2010-07-09 00:00:00+00:00 | Last Updated: 2025-10-03 03:44:08.024780
- Params: `{}`

Series of transactions must be suitable in aggregate

## SUIT-003 — Reasonable Basis
- Source: **FINRA**
- Severity: **warning**
- Applies To: advisor
- Effective: 2010-07-09 00:00:00+00:00 | Last Updated: 2025-10-03 03:44:08.024780
- Params: `{}`

Advisors must have reasonable basis for recommendations

## TAX-001 — Wash Sale Rule Section 1091
- Source: **IRS**
- Severity: **warning**
- Applies To: individual, institutional
- Effective: 1921-01-01 00:00:00+00:00 | Last Updated: 2025-10-03 03:44:08.024780
- Params: `{}`

Cannot claim loss if repurchasing substantially identical security within 30 days

## TRAD-001 — Pattern Day Trader Rule
- Source: **FINRA**
- Severity: **warning**
- Applies To: individual
- Effective: 2001-02-27 00:00:00+00:00 | Last Updated: 2025-10-03 03:44:08.024780
- Params: `{"min_equity": 25000}`

Accounts under $25K limited to 3 day trades per 5-day period

## TRAD-002 — Market Manipulation Prevention
- Source: **SEC**
- Severity: **critical**
- Applies To: individual, advisor
- Effective: 1934-06-06 00:00:00+00:00 | Last Updated: 2025-10-03 03:44:08.024780
- Params: `{}`

Cannot engage in manipulative or deceptive trading practices
