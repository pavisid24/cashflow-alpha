# CashFlow Alpha V2

Automatic single-company research for Indian equities using Yahoo Finance data through yfinance.

## Deploy update
Replace the files in your existing GitHub repository with the contents of this folder, preserving the folder structure. Commit to the same branch connected to Streamlit Community Cloud. Streamlit will rebuild when requirements.txt changes.

## Run locally
```bash
pip install -r requirements.txt
streamlit run app.py
```

## How to use
1. Open Company research.
2. Enter a company name or ticker such as TCS, INFY, HDFCBANK, RELIANCE.
3. Select NSE or BSE.
4. Search company, select a match, then Analyse selected company.
5. Review coverage, missing fields, annual statements, price trend and research signal.

## Data and limitations
- Data source: Yahoo Finance accessed via yfinance. This is an unofficial interface, not an exchange-certified or guaranteed feed.
- Statement coverage varies by company, field and year. Missing values are shown as unavailable; they are not guessed.
- The app does not guarantee 10 years of financials.
- Cash tax paid and Cash ROCE may not be available in Yahoo data. Verify audited filings and calculate using a disclosed formula.
- Current scoring is a preliminary industrial-company screen, not suitable for banks/NBFCs/insurers. A separate financial-sector model is required.
- Valuation and governance are not fully automated; manual review is required.
- BUY–REVIEW / WAIT / SELL–THESIS REVIEW are research labels, not personalised financial advice or trade execution.
- Prices may be delayed, adjusted, incomplete or unavailable. Verify before acting.
