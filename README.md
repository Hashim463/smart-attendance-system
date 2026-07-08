# Stock Market Portfolio Analyzer

A Python tool that tracks a stock portfolio, fetches price data, computes
performance and risk metrics, and generates a formatted Excel report —
combining SQL, financial analysis, and automated reporting in one project.

## What it does
1. **Stores holdings in a SQL database** (SQLite — schema ports directly
   to MySQL/PostgreSQL) — symbol, company, sector, quantity, buy price/date
2. **Fetches price history** — live data via the `yfinance` API (Yahoo
   Finance) when internet is available; falls back to a seeded random-walk
   simulator otherwise, so the project always runs and demos cleanly
3. **Computes metrics per holding and for the whole portfolio**:
   - Invested amount, current value, gain/loss, gain/loss %
   - Portfolio weight (% allocation) per stock
   - Daily volatility (a basic risk measure, standard deviation of returns)
   - Best / worst performer, sector-wise allocation
4. **Generates a 3-sheet Excel report** (openpyxl):
   - **Holdings** — every stock with live formulas (`=Qty*Price` etc.),
     conditional formatting (green = gain, red = loss)
   - **Summary** — KPI cards, sector allocation table
   - **Charts** — bar chart (gain/loss by stock), pie chart (sector allocation)

## How to run it
\`\`\`bash
pip install pandas openpyxl yfinance

python main.py              # first run seeds a sample portfolio and reports
python main.py --refresh    # force re-fetch of price data
python main.py --output MyReport.xlsx
\`\`\`

## Project structure
\`\`\`
db.py                # SQLite schema + CRUD (holdings, price_history)
price_fetcher.py     # yfinance live data, with offline simulator fallback
analyzer.py          # portfolio/holding metrics (returns, volatility, allocation)
report_generator.py  # openpyxl Excel report builder
main.py               # CLI entry point, orchestrates the pipeline
\`\`\`

## Tech used
- **SQLite/SQL** — persistent storage for holdings and historical prices
- **yfinance** — real market data API
- **openpyxl** — formatted Excel report with live formulas, conditional
  formatting, and native charts

## Ideas to extend it
- Add Sharpe ratio / beta calculation against a market index (e.g., NIFTY 50)
- Swap SQLite for MySQL and add a Flask dashboard on top
- Add alerts (email/SMS) when a stock crosses a gain/loss threshold
