import math
import pandas as pd

def required_columns():
    return ["Symbol","Company","Year","PAT","Tax_Expense","Cash_Tax_Paid",
            "CFO","EBITDA","Cash_ROCE","Sales","Sales_Prior",
            "Debt","Cash","Receivables","Receivables_Prior",
            "Payables","Payables_Prior","Capital_Employed","PE"]

def num(row, key):
    try:
        x = float(row.get(key))
        return x if math.isfinite(x) else float("nan")
    except Exception:
        return float("nan")

def ratio(a,b):
    return a/b if pd.notna(a) and pd.notna(b) and b not in (0, 0.0) else float("nan")

def score_company(row):
    checks, flags = [], []
    score = 0
    cash_tax = ratio(num(row,"Cash_Tax_Paid"), num(row,"Tax_Expense"))
    cfo_ebitda = ratio(num(row,"CFO"), num(row,"EBITDA"))
    sales_growth = ratio(num(row,"Sales")-num(row,"Sales_Prior"), num(row,"Sales_Prior"))
    recv_growth = ratio(num(row,"Receivables")-num(row,"Receivables_Prior"), num(row,"Receivables_Prior"))
    net_debt = num(row,"Debt")-num(row,"Cash")
    cash_roce = num(row,"Cash_ROCE")

    def add(name, value, rule, points, passed, flag=None):
        nonlocal score
        checks.append({"Test":name, "Observed":value, "Rule of thumb":rule, "Points":points if passed else 0})
        if passed: score += points
        elif flag: flags.append(flag)

    add("Cash tax / tax expense", f"{cash_tax:.2f}" if pd.notna(cash_tax) else "N/A",
        "> 0.60", 8, pd.notna(cash_tax) and cash_tax > 0.60,
        "Cash tax paid is low versus tax expense; investigate timing differences and deferred tax.")
    add("CFO / EBITDA", f"{cfo_ebitda:.1%}" if pd.notna(cfo_ebitda) else "N/A",
        "> 50%", 15, pd.notna(cfo_ebitda) and cfo_ebitda > 0.50,
        "Operating cash conversion is weak; investigate working capital and earnings quality.")
    add("Cash ROCE", f"{cash_roce:.1f}%" if pd.notna(cash_roce) else "N/A",
        "> 15%", 15, pd.notna(cash_roce) and cash_roce > 15,
        "Cash ROCE is below the strategy's reference threshold.")
    add("Sales growth", f"{sales_growth:.1%}" if pd.notna(sales_growth) else "N/A",
        "Positive", 12, pd.notna(sales_growth) and sales_growth > 0,
        "Sales are not growing versus the prior year.")
    add("Receivables growth", f"{recv_growth:.1%}" if pd.notna(recv_growth) else "N/A",
        "Not materially faster than sales", 10,
        pd.notna(recv_growth) and pd.notna(sales_growth) and recv_growth <= sales_growth + 0.10,
        "Receivables are growing materially faster than sales; check collections.")
    add("Net debt", f"{net_debt:,.2f}" if pd.notna(net_debt) else "N/A",
        "Net debt not excessive", 10, pd.notna(net_debt) and net_debt <= max(num(row,"EBITDA")*2,0),
        "Net debt may be high relative to EBITDA; assess sector and debt maturity.")
    add("Positive PAT", f'{num(row,"PAT"):,.2f}' if pd.notna(num(row,"PAT")) else "N/A",
        "PAT > 0", 10, pd.notna(num(row,"PAT")) and num(row,"PAT") > 0,
        "Reported PAT is zero or negative.")
    # Remaining 20 points are reserved for multi-year consistency, governance and valuation review.
    # They are not awarded from a single-year CSV because doing so would imply unsupported confidence.
    checks.append({"Test":"Multi-year consistency / governance / valuation review",
                   "Observed":"Manual review required", "Rule of thumb":"5–10 years and peer context", "Points":0})
    score = min(100, score)
    label = "Strong research candidate" if score >= 75 else "Needs further research" if score >= 55 else "Weak / incomplete profile"
    if any("N/A" in str(c["Observed"]) for c in checks):
        flags.append("Some required data is missing; score is incomplete and should not be treated as a pass.")
    return {"score":score, "label":label, "checks":checks, "flags":flags}
