# CashFlow Alpha – MVP

A local Streamlit research application for long-term Indian equity research.

## Features
- Fundamental quality scoring from annual financial statement CSVs
- Cash tax / tax expense, CFO / EBITDA, Cash ROCE, sales growth, receivables growth and net-debt checks
- Daily price CSV import and basic 50DMA / 200DMA / RSI analysis
- Research signal: BUY-review / WAIT / SELL-review
- Stock screener, SQLite watchlist and CSV export

## Run on Windows
1. Install Python 3.10 or newer.
2. Extract this ZIP into a separate folder, for example `C:\CashFlowAlpha`.
3. Open Command Prompt in that folder.
4. Run:

```bat
py -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

The app opens in your browser at the local address shown by Streamlit.

## Data format
Financial data: one row per company per financial year. Required columns are listed in the app's Data guide. Use consistent units (for example, ₹ crore) and consistent consolidated or standalone reporting.
Daily prices: `Symbol,Date,Close,Volume`. Dates should be YYYY-MM-DD and prices should be adjusted for splits and bonus issues.

## Important limitations
- Sample data is illustrative only, not real market data.
- The current MVP does not fetch live NSE/BSE financial statements.
- Annual financial ratios require correctly sourced and comparable statements.
- A single-year score is incomplete; multi-year trend, peer comparisons, management quality, auditor notes, contingent liabilities and valuation history still need review.
- Banks, NBFCs, insurers and other financial businesses need a separate scoring model. Do not apply industrial-company EBITDA/ROCE thresholds to them.
- Signals are decision-support research, not personalised financial advice or automatic orders.
