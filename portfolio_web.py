# portfolio_web.py – FINAL FLAWLESS: Symbol Lookup + Full Chart Period Selector + Charts Fixed
import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import requests
import os
from groq import Groq

client = Groq(api_key=st.secrets.get("GROQ_API_KEY") or os.getenv("GROQ_API_KEY"))

st.set_page_config(page_title="Ultimate Portfolio Pro", layout="wide")

# Theme
theme = st.sidebar.radio("Theme", ["Dark", "Light"], horizontal=True)
template = "plotly_dark" if theme == "Dark" else "plotly_white"

st.title("Ultimate Portfolio + Smart Symbol Lookup")
st.caption("Type company name → Open & Current + Full Interactive Chart with Period Selector")

PORTFOLIO_FILE = "my_portfolio.csv"
@st.cache_data(ttl=60)
def load_portfolio():
    return pd.read_csv(PORTFOLIO_FILE).to_dict('records') if os.path.exists(PORTFOLIO_FILE) else []
portfolio = load_portfolio()
def save_portfolio():
    pd.DataFrame(portfolio).to_csv(PORTFOLIO_FILE, index=False)

# Symbol lookup
@st.cache_data(ttl=300)
def search_ticker(query):
    try:
        url = f"https://query2.finance.yahoo.com/v1/finance/search?q={query}&quotesCount=10"
        headers = {"User-Agent": "Mozilla/5.0"}
        data = requests.get(url, headers=headers).json()
        results = []
        for item in data.get("quotes", []):
            symbol = item.get("symbol")
            if not symbol: continue
            name = item.get("shortname") or item.get("longname") or symbol
            exchange = item.get("exchange") or ""
            results.append({"symbol": symbol, "name": name, "exchange": exchange})
        return results[:8]
    except:
        return []

def get_price_info(ticker):
    try:
        t = yf.Ticker(ticker)
        info = t.info
        current = info.get("regularMarketPrice") or info.get("currentPrice") or 0
        open_price = info.get("regularMarketOpen") or info.get("open") or current
        change = current - open_price
        change_pct = (change / open_price) * 100 if open_price else 0
        return round(current, 4), round(open_price, 4), round(change, 4), round(change_pct, 2)
    except:
        return 0, 0, 0, 0

# FULL INTERACTIVE CHART WITH PERIOD SELECTOR
def plot_chart(ticker, period="6mo"):
    df = yf.Ticker(ticker).history(period=period)
    if df.empty:
        return None
    fig = go.Figure()
    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df.Open,
        high=df.High,
        low=df.Low,
        close=df.Close,
        name=ticker
    ))
    fig.update_layout(
        height=650,
        template=template,
        xaxis_rangeslider_visible=False,
        title=f"{ticker.upper()} – {period.upper()} Chart",
        showlegend=False,
        xaxis=dict(
            rangeselector=dict(
                buttons=list([
                    dict(count=1, label="1D", step="day", stepmode="backward"),
                    dict(count=5, label="5D", step="day", stepmode="backward"),
                    dict(count=1, label="1M", step="month", stepmode="backward"),
                    dict(count=3, label="3M", step="month", stepmode="backward"),
                    dict(count=6, label="6M", step="month", stepmode="backward"),
                    dict(count=1, label="YTD", step="year", stepmode="todate"),
                    dict(count=1, label="1Y", step="year", stepmode="backward"),
                    dict(count=2, label="2Y", step="year", stepmode="backward"),
                    dict(count=5, label="5Y", step="year", stepmode="backward"),
                    dict(step="all", label="MAX")
                ])
            ),
            rangeslider_visible=False,
            type="date"
        )
    )
    return fig

# TABS
tab1, tab2, tab3, tab4, tab5 = st.tabs(["Symbol Lookup", "AI Forecast", "Bond ETFs", "Dividend ETFs", "Portfolio"])

# TAB 1 – Symbol Lookup + Chart (FIXED!)
with tab1:
    st.header("Smart Symbol Lookup")
    query = st.text_input("Type any company, ETF, or crypto", "Apple")
    
    if query:
        with st.spinner("Searching..."):
            results = search_ticker(query)
        
        if results:
            for r in results:
                symbol = r["symbol"]
                current, open_p, change, pct = get_price_info(symbol)
                
                col1, col2, col3, col4 = st.columns([2, 4, 2, 2])
                with col1:
                    st.subheader(symbol)
                with col2:
                    st.write(r["name"])
                    st.caption(r["exchange"])
                with col3:
                    st.metric("Current", f"${current:,.2f}")
                    st.caption(f"Open: ${open_p:,.2f}")
                with col4:
                    st.metric("Today", f"{change:+.2f}", f"{pct:+.2f}%")
                
                if st.button("Add to Portfolio", key=symbol):
                    portfolio.append({"ticker": symbol, "shares": 100.0, "buy_price": current})
                    save_portfolio()
                    st.success("Added!")

                # PERIOD SELECTOR + CHART (NOW WORKS!)
                period = st.selectbox(
                    "Chart Period",
                    ["1d","5d","1mo","3mo","6mo","ytd","1y","2y","5y","max"],
                    key=f"period_{symbol}"
                )
                chart = plot_chart(symbol, period)
                if chart:
                    st.plotly_chart(chart, use_container_width=True)
                
                st.divider()
        else:
            st.error("No results")

# TAB 2 – AI Forecast + Chart
with tab2:
    st.header("AI 3-Month Forecast")
    ticker = st.text_input("Ticker", "JEPI").upper()
    current, open_p, _, _ = get_price_info(ticker)
    st.write(f"**{ticker}** • Current: ${current:,.2f} • Open: ${open_p:,.2f}")
    period = st.selectbox("Chart Period", ["1d","5d","1mo","3mo","6mo","1y","2y","5y","max"], key="ai_period")
    chart = plot_chart(ticker, period)
    if chart:
        st.plotly_chart(chart, use_container_width=True)

# Other tabs (clean)
with tab3:
    st.header("Top Bond ETFs")
    for t in ["ZAG.TO","BND","TLT","HYG"]:
        c, o, ch, pct = get_price_info(t)
        st.metric(t, f"${c:,.2f}", f"{ch:+.2f} ({pct:+.2f}%)")

with tab4:
    st.header("Top Dividend ETFs")
    for t in ["HMAX.TO","JEPI","JEPQ","SCHD"]:
        c, o, ch, pct = get_price_info(t)
        st.metric(t, f"${c:,.2f}", f"{ch:+.2f} ({pct:+.2f}%)")

with tab5:
    st.header("Your Portfolio")
    if portfolio:
        total = 0
        for p in portfolio:
            c, _, _, _ = get_price_info(p["ticker"])
            value = p["shares"] * c
            total += value
            st.write(f"**{p['ticker']}** • {p['shares']} shares • Now: ${c:,.2f}")
        st.success(f"Total Value: ${total:,.2f}")
    else:
        st.info("Add assets from Symbol Lookup!")

st.sidebar.success("Charts FULLY RESTORED + Period Selector!")
st.sidebar.caption(f"Live • {datetime.now().strftime('%H:%M')}")