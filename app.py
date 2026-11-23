import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from cashflow_alpha.market_data import search_companies, fetch_company
from cashflow_alpha.research import build_research_report, make_signal

st.set_page_config(page_title="CashFlow Alpha", page_icon="📈", layout="wide")
st.title("📈 CashFlow Alpha")
st.caption("Long-term Indian equity research | Cash-flow quality • Business growth • Valuation • Entry discipline")

with st.sidebar:
    st.header("Research workspace")
    page = st.radio("Navigate", ["Company research", "Stock screener (manual CSV)", "Watchlist", "Methodology & data"])
    st.divider()
    st.caption("Market data is retrieved through Yahoo Finance via yfinance. It is an unofficial source; verify figures against company filings before investing.")

if "watchlist" not in st.session_state:
    st.session_state.watchlist = []

if page == "Company research":
    st.subheader("Search an Indian listed company")
    st.write("Search by company name or Yahoo Finance ticker. Examples: TCS, INFY, HDFCBANK, RELIANCE.")
    query = st.text_input("Company name or ticker", placeholder="e.g. TCS")
    col1, col2 = st.columns([1, 3])
    with col1:
        exchange = st.selectbox("Exchange", ["NSE", "BSE"], index=0)
    with col2:
        years = st.select_slider("Price history", options=["1y", "2y", "5y", "10y"], value="5y")
    if st.button("Search company", type="primary", disabled=not query.strip()):
        with st.spinner("Searching listed companies..."):
            try:
                matches = search_companies(query.strip(), exchange)
                st.session_state.search_matches = matches
                st.session_state.last_query = query.strip()
                st.session_state.last_exchange = exchange
            except Exception as e:
                st.error(f"Search failed: {e}")
                st.session_state.search_matches = []

    matches = st.session_state.get("search_matches", [])
    if matches:
        labels = [f'{m["name"]} — {m["symbol"]} ({m.get("exchange","")})' for m in matches]
        chosen_label = st.selectbox("Select company", labels)
        chosen = matches[labels.index(chosen_label)]
        if st.button("Analyse selected company", type="primary"):
            with st.spinner(f"Fetching available financial statements and {years} price history for {chosen['symbol']}..."):
                try:
                    data = fetch_company(chosen["symbol"], years)
                    st.session_state.company_data = data
                    st.session_state.company_symbol = chosen["symbol"]
                    st.session_state.company_name = chosen["name"]
                except Exception as e:
                    st.error(f"Could not retrieve data for {chosen['symbol']}: {e}")

    data = st.session_state.get("company_data")
    if data:
        st.divider()
        st.header(f'{st.session_state.company_name} ({st.session_state.company_symbol})')
        report = build_research_report(data)
        signal = make_signal(report, data)
        a,b,c,d = st.columns(4)
        a.metric("Fundamental score", f'{report["score"]}/100', help="Indicative score based only on available fields.")
        b.metric("Data coverage", report["coverage"])
        c.metric("Latest close", f'₹{data["last_close"]:,.2f}' if data.get("last_close") else "N/A")
        d.metric("Research signal", signal["signal"])
        st.progress(report["score"]/100)
        st.info(signal["reason"])
        if report["limitations"]:
            with st.expander("Data limitations and items to verify", expanded=True):
                for item in report["limitations"]:
                    st.warning(item)

        tab1, tab2, tab3, tab4 = st.tabs(["Financial quality", "Price & entry", "Financial statements", "Research notes"])
        with tab1:
            st.subheader("Cash-flow and business-quality checks")
            st.dataframe(pd.DataFrame(report["checks"]), use_container_width=True, hide_index=True)
            if report["flags"]:
                st.subheader("Potential red flags")
                for f in report["flags"]:
                    st.warning(f)
            st.caption("Thresholds are screening heuristics, not accounting standards or proof of fraud.")
        with tab2:
            hist = data.get("history", pd.DataFrame())
            if not hist.empty:
                chart = go.Figure()
                chart.add_trace(go.Scatter(x=hist.index, y=hist["Close"], name="Close", mode="lines"))
                if "MA50" in hist:
                    chart.add_trace(go.Scatter(x=hist.index, y=hist["MA50"], name="50-day average"))
                if "MA200" in hist:
                    chart.add_trace(go.Scatter(x=hist.index, y=hist["MA200"], name="200-day average"))
                chart.update_layout(height=430, xaxis_title="Date", yaxis_title="Price (₹)", legend_orientation="h")
                st.plotly_chart(chart, use_container_width=True)
                st.write(f'RSI (14): **{data.get("rsi", "N/A")}**')
                st.write(f'50-day trend: **{data.get("trend_50", "N/A")}** | 200-day trend: **{data.get("trend_200", "N/A")}**')
                st.subheader("Long-term entry checklist")
                for item in signal["entry_checklist"]:
                    st.write(("✅ " if item["pass"] else "⬜ ") + item["item"])
                st.caption("The app provides research conditions, not a precise guaranteed entry price. Use a valuation margin of safety and review the chart before acting.")
            else:
                st.warning("No price history was returned.")
        with tab3:
            for title, frame in [("Income statement", data.get("income", pd.DataFrame())),
                                 ("Cash flow statement", data.get("cashflow", pd.DataFrame())),
                                 ("Balance sheet", data.get("balance", pd.DataFrame()))]:
                st.subheader(title)
                if frame is not None and not frame.empty:
                    st.dataframe(frame, use_container_width=True)
                else:
                    st.info("This statement was not available from the selected data source.")
        with tab4:
            st.subheader("Investment research summary")
            st.write(f'**Business:** {st.session_state.company_name}')
            st.write(f'**Fundamental assessment:** {report["label"]}')
            st.write(f'**Signal:** {signal["signal"]}')
            st.write("**Next research actions**")
            for item in [
                "Read the latest annual report and auditor notes.",
                "Compare 5–10 years of consolidated financials.",
                "Check contingent liabilities, related-party transactions and promoter pledging.",
                "Compare valuation with sector peers and the company's own history.",
                "Write down the investment thesis and what would invalidate it."
            ]:
                st.write("- " + item)
            if st.button("Add to watchlist"):
                symbol = st.session_state.company_symbol
                if symbol not in st.session_state.watchlist:
                    st.session_state.watchlist.append(symbol)
                st.success(f"{symbol} added to this session's watchlist.")

elif page == "Stock screener (manual CSV)":
    st.subheader("Bulk screening using your own verified data")
    st.write("Upload a CSV with one row per company and financial year. Automatic bulk-market scanning will be added after the single-company data flow is validated.")
    uploaded = st.file_uploader("Upload financial CSV", type=["csv"])
    if uploaded:
        df = pd.read_csv(uploaded)
        st.dataframe(df, use_container_width=True)
        st.download_button("Download uploaded data", df.to_csv(index=False), "financial_data_copy.csv")

elif page == "Watchlist":
    st.subheader("Session watchlist")
    if st.session_state.watchlist:
        st.write(", ".join(st.session_state.watchlist))
        st.caption("This first V2 build keeps the watchlist in the current browser session. Persistent multi-user storage is a later upgrade.")
    else:
        st.info("Search and analyse a company, then use Add to watchlist.")

elif page == "Methodology & data":
    st.subheader("Data source and important limitations")
    st.markdown("""
    **Automatic data source:** Yahoo Finance accessed through the `yfinance` Python package.

    - NSE tickers use the `.NS` suffix; BSE tickers use `.BO`.
    - Annual statements and daily prices may be incomplete, delayed, revised or unavailable.
    - yfinance is an unofficial interface, not an exchange-certified financial data feed.
    - The app never fills missing financial values with guesses.
    - Cash tax paid and cash ROCE may be unavailable or require a documented calculation; unavailable values are marked accordingly.
    - Industrial-company screening rules must not be applied to banks, NBFCs, insurers or other financial businesses.
    - Verify every material number against audited annual reports, exchange filings and company disclosures.
    """)
    st.markdown("**Research scoring:** Cash flow quality, profit quality, capital efficiency, growth, balance-sheet risk, governance review and valuation. Missing data reduces coverage and confidence.")
    st.markdown("**Signals:** BUY – REVIEW, WAIT, or SELL / THESIS REVIEW. These are decision-support labels, not automatic orders or guaranteed forecasts.")
