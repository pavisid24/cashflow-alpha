import pandas as pd
import yfinance as yf

POPULAR = {
    "TCS":"TCS.NS", "INFY":"INFY.NS", "HDFCBANK":"HDFCBANK.NS",
    "RELIANCE":"RELIANCE.NS", "ICICIBANK":"ICICIBANK.NS",
    "ITC":"ITC.NS", "LT":"LT.NS", "WIPRO":"WIPRO.NS",
    "SBIN":"SBIN.NS", "BHARTIARTL":"BHARTIARTL.NS"
}

def search_companies(query, exchange="NSE"):
    q = query.strip()
    suffix = ".NS" if exchange == "NSE" else ".BO"
    results = []
    # Direct ticker shortcut first.
    symbol = POPULAR.get(q.upper(), q.upper() + suffix)
    try:
        t = yf.Ticker(symbol)
        hist = t.history(period="5d")
        if not hist.empty:
            info = {}
            try:
                info = t.get_info()
            except Exception:
                pass
            results.append({
                "symbol": symbol,
                "name": info.get("longName") or info.get("shortName") or q.upper(),
                "exchange": exchange
            })
    except Exception:
        pass
    # Search by company name/ticker through Yahoo quote search.
    try:
        search = yf.Search(q, max_results=12)
        for quote in getattr(search, "quotes", []) or []:
            sym = quote.get("symbol", "")
            exch = quote.get("exchange", "")
            if not sym:
                continue
            if exchange == "NSE" and not sym.endswith(".NS"):
                continue
            if exchange == "BSE" and not sym.endswith(".BO"):
                continue
            if not any(x["symbol"] == sym for x in results):
                results.append({
                    "symbol": sym,
                    "name": quote.get("longname") or quote.get("shortname") or sym,
                    "exchange": quote.get("exchDisp") or exchange
                })
    except Exception:
        pass
    if not results:
        raise ValueError("No matching ticker was returned. Try the exact Yahoo Finance symbol (for example TCS.NS) or verify the ticker.")
    return results[:12]

def _find_row(frame, terms):
    if frame is None or frame.empty:
        return None
    names = [str(x).lower().replace("_"," ").strip() for x in frame.index]
    for term in terms:
        term = term.lower()
        for original, norm in zip(frame.index, names):
            if norm == term or term in norm:
                return original
    return None

def _series(frame, terms):
    row = _find_row(frame, terms)
    if row is None:
        return pd.Series(dtype="float64")
    s = frame.loc[row]
    if isinstance(s, pd.DataFrame):
        s = s.iloc[0]
    return pd.to_numeric(s, errors="coerce")

def fetch_company(symbol, price_period="5y"):
    ticker = yf.Ticker(symbol)
    history = ticker.history(period=price_period, auto_adjust=True)
    if history is None or history.empty:
        raise ValueError("No historical prices returned for this ticker.")
    history = history.copy()
    history["Close"] = pd.to_numeric(history["Close"], errors="coerce")
    history["MA50"] = history["Close"].rolling(50).mean()
    history["MA200"] = history["Close"].rolling(200).mean()
    delta = history["Close"].diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = -delta.clip(upper=0).rolling(14).mean()
    rs = gain / loss.replace(0, float("nan"))
    rsi = 100 - 100/(1+rs)

    income = ticker.get_income_stmt(freq="yearly")
    cashflow = ticker.get_cashflow(freq="yearly")
    balance = ticker.get_balance_sheet(freq="yearly")
    info = {}
    try:
        info = ticker.get_info()
    except Exception:
        pass

    # Pull key annual series, preserving the source's fiscal-year columns.
    revenue = _series(income, ["Total Revenue", "Operating Revenue"])
    pat = _series(income, ["Net Income", "Net Income Common Stockholders"])
    ebitda = _series(income, ["EBITDA"])
    tax_expense = _series(income, ["Tax Provision", "Income Tax Expense"])
    cfo = _series(cashflow, ["Operating Cash Flow", "Cash Flow From Continuing Operating Activities"])
    capex = _series(cashflow, ["Capital Expenditure", "Capital Expenditures"])
    cash_tax = _series(cashflow, ["Taxes Paid", "Income Tax Paid", "Cash Taxes Paid"])
    debt = _series(balance, ["Total Debt", "Long Term Debt And Capital Lease Obligation"])
    cash = _series(balance, ["Cash And Cash Equivalents", "Cash Cash Equivalents And Short Term Investments"])
    receivables = _series(balance, ["Accounts Receivable", "Receivables"])
    payables = _series(balance, ["Accounts Payable", "Payables"])
    equity = _series(balance, ["Stockholders Equity", "Total Equity Gross Minority Interest"])
    total_debt = debt

    # Combine fiscal years using statement column labels; no synthetic data is inserted.
    years = sorted(set(revenue.index) | set(pat.index) | set(cfo.index), reverse=True)
    annual = []
    for i, period in enumerate(years):
        def val(s):
            try:
                x = s.get(period)
                return float(x) if pd.notna(x) else None
            except Exception:
                return None
        annual.append({
            "Fiscal period": str(getattr(period, "date", lambda: period)()),
            "Revenue": val(revenue), "PAT": val(pat), "EBITDA": val(ebitda),
            "Tax expense": val(tax_expense), "Cash tax paid": val(cash_tax),
            "Operating cash flow": val(cfo), "Capital expenditure": val(capex),
            "Debt": val(total_debt), "Cash & equivalents": val(cash),
            "Receivables": val(receivables), "Payables": val(payables),
            "Equity": val(equity)
        })
    annual_df = pd.DataFrame(annual)
    latest = annual_df.iloc[0].to_dict() if len(annual_df) else {}
    previous = annual_df.iloc[1].to_dict() if len(annual_df)>1 else {}
    # Capital employed / cash ROCE is not consistently exposed in provider data.
    # Do not invent it; report unavailable until a transparent calculation can be supported.
    return {
        "symbol": symbol, "history": history, "income": income, "cashflow": cashflow,
        "balance": balance, "annual": annual_df, "latest": latest, "previous": previous,
        "last_close": float(history["Close"].dropna().iloc[-1]),
        "rsi": round(float(rsi.dropna().iloc[-1]), 1) if not rsi.dropna().empty else None,
        "trend_50": "Above 50DMA" if pd.notna(history["MA50"].iloc[-1]) and history["Close"].iloc[-1] > history["MA50"].iloc[-1] else "Below / insufficient",
        "trend_200": "Above 200DMA" if pd.notna(history["MA200"].iloc[-1]) and history["Close"].iloc[-1] > history["MA200"].iloc[-1] else "Below / insufficient",
        "info": info
    }
