import math
import pandas as pd

def _ratio(a,b):
    try:
        if a is None or b is None or pd.isna(a) or pd.isna(b) or float(b)==0:
            return None
        return float(a)/float(b)
    except Exception:
        return None

def build_research_report(data):
    latest = data.get("latest", {})
    previous = data.get("previous", {})
    checks, flags, limitations = [], [], []
    score = 0
    coverage = 0

    def check(name, value, rule, points, passed, missing_note=None, flag=None):
        nonlocal score, coverage
        if value is not None and not pd.isna(value):
            coverage += 1
            if passed:
                score += points
        else:
            limitations.append(missing_note or f"{name} is unavailable from the current data provider.")
        checks.append({"Metric":name, "Observed":value if value is not None else "Unavailable",
                       "Reference":rule, "Points earned":points if passed else 0})
        if flag and value is not None and not passed:
            flags.append(flag)

    cash_tax = _ratio(latest.get("Cash tax paid"), latest.get("Tax expense"))
    cfo_ebitda = _ratio(latest.get("Operating cash flow"), latest.get("EBITDA"))
    sales_growth = _ratio((latest.get("Revenue") - previous.get("Revenue"))
                          if latest.get("Revenue") is not None and previous.get("Revenue") not in (None,0) else None,
                          previous.get("Revenue"))
    receivables_growth = _ratio((latest.get("Receivables") - previous.get("Receivables"))
                                if latest.get("Receivables") is not None and previous.get("Receivables") not in (None,0) else None,
                                previous.get("Receivables"))
    net_debt = (latest.get("Debt") - latest.get("Cash")) if latest.get("Debt") is not None and latest.get("Cash") is not None else None

    check("Cash tax / tax expense", round(cash_tax,2) if cash_tax is not None else None, "> 0.60", 10,
          cash_tax is not None and cash_tax > .60,
          "Cash tax paid is not separately available; verify tax paid in the annual report.",
          "Cash tax paid is low relative to tax expense; investigate deferred tax and timing.")
    check("Operating cash flow / EBITDA", f"{cfo_ebitda:.1%}" if cfo_ebitda is not None else None,
          "> 50%", 20, cfo_ebitda is not None and cfo_ebitda > .5,
          "CFO/EBITDA could not be calculated because CFO or EBITDA is unavailable.",
          "Operating cash conversion is below the reference threshold; inspect working capital.")
    check("Cash ROCE", None, "Investor reference > 15%", 15, False,
          "Cash ROCE is not consistently available in the provider data; calculate from audited statements using a disclosed formula.")
    check("Revenue growth", f"{sales_growth:.1%}" if sales_growth is not None else None,
          "Positive year-on-year", 15, sales_growth is not None and sales_growth > 0,
          "Two comparable annual revenue observations are required.",
          "Revenue declined year-on-year; investigate the reason.")
    check("Receivables growth", f"{receivables_growth:.1%}" if receivables_growth is not None else None,
          "Not materially faster than revenue", 10,
          receivables_growth is not None and sales_growth is not None and receivables_growth <= sales_growth + .10,
          "Comparable receivables data is unavailable.",
          "Receivables growth is materially faster than revenue; review collection quality.")
    check("Net debt", f"{net_debt:,.2f}" if net_debt is not None else None,
          "Sector-adjusted leverage", 10, net_debt is not None and net_debt <= 0,
          "Debt or cash balance is unavailable.",
          "Company has net debt; assess leverage, maturity and interest coverage.")
    check("PAT positive", latest.get("PAT"), "Positive", 10,
          latest.get("PAT") is not None and latest.get("PAT") > 0,
          "PAT is unavailable from the current data provider.",
          "Latest reported PAT is negative.")
    # Reserved points are not automatically awarded without multi-year governance and valuation review.
    checks.append({"Metric":"Governance / multi-year consistency / valuation", "Observed":"Manual review required",
                   "Reference":"5–10 years, peer and auditor review", "Points earned":0})
    if len(data.get("annual", [])) < 5:
        limitations.append("Fewer than five annual periods were returned; long-term trend confidence is limited.")
    if data.get("info", {}).get("quoteType") == "EQUITY" and data.get("info", {}).get("industry", "").lower().find("bank") >= 0:
        limitations.append("Banking-sector model is required. Industrial-company CFO/EBITDA and cash-ROCE heuristics are not appropriate.")
    pct = round(coverage / 7 * 100)
    label = "Strong research candidate" if score >= 65 else "Needs further research" if score >= 35 else "Weak or incomplete profile"
    return {"score":min(score,100), "label":label, "coverage":f"{coverage}/7 checks populated ({pct}%)",
            "checks":checks, "flags":flags, "limitations":list(dict.fromkeys(limitations)),
            "cash_tax":cash_tax, "cfo_ebitda":cfo_ebitda, "sales_growth":sales_growth,
            "receivables_growth":receivables_growth, "net_debt":net_debt}

def make_signal(report, data):
    checks = [
        {"item":"Fundamental screen score is at least 65/100", "pass":report["score"] >= 65},
        {"item":"At least 5 of 7 core checks have usable data", "pass":int(report["coverage"].split("/")[0]) >= 5},
        {"item":"Price is above its 200-day moving average", "pass":data.get("trend_200") == "Above 200DMA"},
        {"item":"Latest RSI is between 40 and 70", "pass":data.get("rsi") is not None and 40 <= data["rsi"] <= 70},
        {"item":"Valuation has been checked against sector peers and history", "pass":False},
        {"item":"Governance and latest annual report have been reviewed", "pass":False}
    ]
    if report["score"] < 35:
        signal = "SELL / THESIS REVIEW"
        reason = "The available fundamental data is weak or materially incomplete. Do not interpret this as an automatic sell order; investigate the business and data first."
    elif all(x["pass"] for x in checks):
        signal = "BUY – REVIEW"
        reason = "Several research conditions are positive, but this remains a candidate for manual valuation, governance and thesis review—not an automatic buy instruction."
    else:
        signal = "WAIT"
        reason = "The company may merit further research, but one or more data, trend, valuation or governance confirmations are missing."
    return {"signal":signal, "reason":reason, "entry_checklist":checks}
