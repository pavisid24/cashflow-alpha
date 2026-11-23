import streamlit as st
import pandas as pd
from pathlib import Path
from cashflow_alpha.scoring import score_company, required_columns
from cashflow_alpha.signals import technical_snapshot, long_term_signal
from cashflow_alpha.storage import init_db, save_watchlist, load_watchlist, remove_watchlist

st.set_page_config(page_title="CashFlow Alpha", page_icon="📈", layout="wide")
init_db()

st.title("📈 CashFlow Alpha")
st.caption("Long-term Indian equity research • Cash-flow quality • Valuation • Entry & exit discipline")

with st.sidebar:
    st.header("Research workspace")
    page = st.radio("Navigate", ["Dashboard", "Company analysis", "Stock screener", "Watchlist", "Data guide"])
    st.divider()
    st.caption("MVP: upload your own financial statements and price history. Signals are research aids, not trade instructions.")

def load_financials():
    uploaded = st.session_state.get("financial_upload")
    if uploaded is not None:
        try:
            return pd.read_csv(uploaded)
        except Exception as e:
            st.error(f"Could not read financial CSV: {e}")
    sample = Path("data/sample_financials.csv")
    if sample.exists():
        return pd.read_csv(sample)
    return pd.DataFrame()

def load_prices():
    uploaded = st.session_state.get("price_upload")
    if uploaded is not None:
        try:
            return pd.read_csv(uploaded, parse_dates=["Date"])
        except Exception as e:
            st.error(f"Could not read price CSV: {e}")
    sample = Path("data/sample_prices.csv")
    if sample.exists():
        return pd.read_csv(sample, parse_dates=["Date"])
    return pd.DataFrame()

fin = load_financials()
prices = load_prices()

if page == "Dashboard":
    st.subheader("Research dashboard")
    c1,c2,c3 = st.columns(3)
    c1.metric("Companies loaded", int(fin["Symbol"].nunique()) if "Symbol" in fin else 0)
    c2.metric("Financial records", len(fin))
    c3.metric("Price observations", len(prices))
    st.info("Start with the sample dataset to explore the workflow. Replace it with verified company financials before making any investment decision.")
    if not fin.empty and "Symbol" in fin:
        latest = fin.sort_values("Year").groupby("Symbol", as_index=False).tail(1)
        rows = []
        for _, r in latest.iterrows():
            result = score_company(r)
            rows.append({"Symbol": r["Symbol"], "Company": r.get("Company", r["Symbol"]),
                         "Fundamental score": result["score"], "Quality": result["label"],
                         "Key flags": "; ".join(result["flags"][:2])})
        st.dataframe(pd.DataFrame(rows).sort_values("Fundamental score", ascending=False), use_container_width=True, hide_index=True)

elif page == "Company analysis":
    st.subheader("Company-level research")
    if fin.empty or "Symbol" not in fin:
        st.warning("Upload financial data in the Data guide section or add a CSV using the template.")
    else:
        symbols = sorted(fin["Symbol"].dropna().unique().tolist())
        symbol = st.selectbox("Select company", symbols)
        company_df = fin[fin["Symbol"] == symbol].sort_values("Year")
        row = company_df.iloc[-1]
        result = score_company(row)
        p1,p2,p3 = st.columns(3)
        p1.metric("Fundamental score", f'{result["score"]}/100')
        p2.metric("Quality assessment", result["label"])
        p3.metric("Financial year", str(row["Year"]))
        st.progress(result["score"]/100)
        st.markdown("#### Financial quality checks")
        st.dataframe(pd.DataFrame(result["checks"]), use_container_width=True, hide_index=True)
        st.markdown("#### Research flags")
        if result["flags"]:
            for flag in result["flags"]:
                st.warning(flag)
        else:
            st.success("No automated flags from the available fields. This is not a clean audit opinion.")
        st.markdown("#### Long-term entry / exit assessment")
        p = prices[prices["Symbol"] == symbol].sort_values("Date") if not prices.empty and "Symbol" in prices else pd.DataFrame()
        if not p.empty:
            tech = technical_snapshot(p)
            signal = long_term_signal(result["score"], float(row.get("PE", float("nan"))), tech)
            a,b,c,d = st.columns(4)
            a.metric("Last close", f'₹{tech.get("last_close", 0):,.2f}')
            b.metric("RSI (14)", f'{tech.get("rsi", float("nan")):.1f}' if pd.notna(tech.get("rsi")) else "N/A")
            c.metric("50-day trend", tech.get("trend_50", "N/A"))
            d.metric("200-day trend", tech.get("trend_200", "N/A"))
            st.subheader(f"Research signal: {signal['signal']}")
            st.write(signal["reason"])
            st.caption("A technical signal is meaningful only with sufficient, correctly adjusted daily price history. Valuation requires sector and historical context.")
            st.line_chart(p.set_index("Date")["Close"])
        else:
            st.info("No price history loaded for this symbol. Upload daily prices to calculate technical entry conditions.")
        st.markdown("#### Historical financials")
        st.dataframe(company_df, use_container_width=True, hide_index=True)
        if st.button("Add to watchlist"):
            save_watchlist(symbol, str(row.get("Company", symbol)), result["score"], result["label"])
            st.success("Added to watchlist.")

elif page == "Stock screener":
    st.subheader("Fundamental stock screener")
    if fin.empty or "Symbol" not in fin:
        st.warning("Upload financial data first.")
    else:
        latest = fin.sort_values("Year").groupby("Symbol", as_index=False).tail(1)
        results = []
        for _, r in latest.iterrows():
            s = score_company(r)
            results.append({"Symbol":r["Symbol"], "Company":r.get("Company",r["Symbol"]),
                            "Year":r["Year"], "Score":s["score"], "Classification":s["label"],
                            "Flags":" | ".join(s["flags"])})
        out = pd.DataFrame(results).sort_values("Score", ascending=False)
        min_score = st.slider("Minimum fundamental score", 0, 100, 60)
        st.dataframe(out[out["Score"] >= min_score], use_container_width=True, hide_index=True)
        st.download_button("Download screener CSV", out.to_csv(index=False), "cashflow_alpha_screener.csv", "text/csv")

elif page == "Watchlist":
    st.subheader("Saved research watchlist")
    watch = load_watchlist()
    if watch.empty:
        st.info("No companies saved yet. Add companies from Company analysis.")
    else:
        st.dataframe(watch, use_container_width=True, hide_index=True)
        symbol_to_remove = st.selectbox("Remove a symbol", watch["symbol"].tolist())
        if st.button("Remove selected"):
            remove_watchlist(symbol_to_remove)
            st.rerun()

elif page == "Data guide":
    st.subheader("Bring your own verified data")
    st.markdown("""
    The first version deliberately uses CSV imports rather than unreliable scraping or invented live data.
    Upload annual financial statements and daily adjusted prices from a source you trust.
    """)
    st.markdown("#### Financial CSV")
    st.code(", ".join(required_columns()))
    st.download_button("Download financial CSV template",
        pd.DataFrame(columns=required_columns()).to_csv(index=False),
        "financial_template.csv", "text/csv")
    st.file_uploader("Upload annual financials CSV", type=["csv"], key="financial_upload")
    st.markdown("#### Daily price CSV")
    st.code("Symbol,Date,Close,Volume")
    st.download_button("Download price CSV template",
        pd.DataFrame(columns=["Symbol","Date","Close","Volume"]).to_csv(index=False),
        "price_template.csv", "text/csv")
    st.file_uploader("Upload daily price history CSV", type=["csv"], key="price_upload")
    st.caption("Financial units must be consistent within each company and year (for example, all values in ₹ crore). Use consolidated statements consistently where available.")
    st.markdown("#### Data quality checklist")
    st.write("- Prefer 5–10 years of audited annual data.")
    st.write("- Use consolidated statements consistently.")
    st.write("- Ensure cash flow, PAT, EBITDA, tax, debt and capital employed use matching periods.")
    st.write("- Adjust price data for splits and bonuses.")
    st.write("- Do not compare banks and financial companies using industrial-company EBITDA/ROCE rules.")
