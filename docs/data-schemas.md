# Canonical data schemas

MarketLab uses three canonical record types at the boundary between data sources
and research code. Downloaders and loaders must emit these names and types; they
must not leak provider-specific columns into downstream modules.

## Daily prices

| Column | Python type | Notes |
| --- | --- | --- |
| `date` | `datetime` | Daily observation timestamp |
| `symbol` | `str` | Security identifier |
| `open` | `float` | Unadjusted opening price |
| `high` | `float` | Unadjusted high price |
| `low` | `float` | Unadjusted low price |
| `close` | `float` | Unadjusted closing price |
| `adjusted_close` | `float` | Split- and distribution-adjusted close |
| `volume` | `int` or `float` | Reported daily volume |

Primary key: `(date, symbol)`.

## Security metadata

| Column | Python type |
| --- | --- |
| `symbol` | `str` |
| `company_name` | `str` |
| `sector` | `str` |
| `industry` | `str` |
| `exchange` | `str` |

Primary key: `(symbol)`.

## Fundamentals

| Column | Python type | Notes |
| --- | --- | --- |
| `symbol` | `str` | Security identifier |
| `fiscal_period` | `str` | Provider-normalized fiscal period |
| `report_date` | `datetime` | Fiscal period end or statement date |
| `available_date` | `datetime` | Earliest date usable by a simulation |
| `market_cap` | numeric or `None` | Market capitalization |
| `book_value` | numeric or `None` | Shareholders' book value |
| `net_income` | numeric or `None` | Net income |
| `revenue` | numeric or `None` | Revenue |
| `gross_profit` | numeric or `None` | Gross profit |
| `assets` | numeric or `None` | Total assets |
| `debt` | numeric or `None` | Total debt |
| `free_cash_flow` | numeric or `None` | Free cash flow |
| `shares_outstanding` | numeric or `None` | Shares outstanding |

Primary key: `(symbol, fiscal_period, available_date)`. Including
`available_date` preserves statement revisions or restatements that become known
at different times.

At research date `t`, downstream code may only use a fundamental record when
`available_date <= t`. Enforcement of that temporal rule belongs to the
data-validation layer.
