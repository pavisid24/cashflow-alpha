import pandas as pd
import numpy as np

def technical_snapshot(prices):
    p = prices.copy()
    p["Date"] = pd.to_datetime(p["Date"])
    p = p.sort_values("Date")
    close = pd.to_numeric(p["Close"], errors="coerce").dropna()
    if len(close) < 30:
        return {"last_close": float(close.iloc[-1]) if len(close) else 0,
                "rsi": float("nan"), "trend_50":"Insufficient data", "trend_200":"Insufficient data"}
    delta = close.diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = -delta.clip(upper=0).rolling(14).mean()
    rs = gain / loss.replace(0, np.nan)
    rsi = 100 - (100/(1+rs))
    ma50 = close.rolling(50).mean()
    ma200 = close.rolling(200).mean()
    last = close.iloc[-1]
    return {
        "last_close": float(last),
        "rsi": float(rsi.iloc[-1]) if pd.notna(rsi.iloc[-1]) else float("nan"),
        "trend_50": "Above 50DMA" if len(close)>=50 and last>ma50.iloc[-1] else "Below / insufficient",
        "trend_200": "Above 200DMA" if len(close)>=200 and last>ma200.iloc[-1] else "Below / insufficient",
    }

def long_term_signal(fundamental_score, pe, tech):
    if fundamental_score < 55:
        return {"signal":"SELL / AVOID REVIEW", "reason":"Fundamental quality is weak or incomplete. Recheck financial statements and the investment thesis."}
    if fundamental_score < 75:
        return {"signal":"WAIT", "reason":"The fundamental score is not yet strong enough for a high-conviction long-term research candidate."}
    if tech.get("trend_200") != "Above 200DMA":
        return {"signal":"WAIT", "reason":"Fundamentals look promising, but the long-term price trend is not confirmed or there is insufficient history."}
    if pd.notna(pe) and pe > 60:
        return {"signal":"WAIT", "reason":"Strong fundamentals may be offset by a demanding P/E. Compare sector peers, growth and historical valuation before entry."}
    return {"signal":"POTENTIAL BUY – REVIEW", "reason":"Fundamental quality and long-term trend are encouraging. Confirm valuation, governance, liquidity and a written investment thesis before acting."}
