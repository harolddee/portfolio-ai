# portfolio_web.py – ULTIMATE 2025: + High Interest Bonds/ETFs + Top Movers + News Grid
import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import requests
import os
from groq import Groq

client = Groq(api_key=st.secrets.get("GROQ_API_KEY") or os.getenv("GROQ_API_KEY"))

st.set_page_config(page_title="Ultimate Portfolio Pro 2025", layout="wide")

# Theme
theme = st.sidebar.radio("Theme", ["Dark", "Light"], horizontal=True)
template = "plotly_dark" if theme == "Dark" else "plotly_white"

st.title("Ultimate Portfolio Dashboard – Nov 2025 Edition")
st.caption("High Yield Bonds/ETFs • Top Movers • Stock News Grid • Symbol Lookup + Charts")

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

# Interactive chart with period selector
def plot_chart(ticker, period="6mo"):
    df = yf.Ticker(ticker).history(period=period)
    if df.empty: return None
    fig = go.Figure()
    fig.add_trace(go.Candlestick(x=df.index, open=df.Open, high=df.High, low=df.Low, close=df.Close, name=ticker))
    fig.update_layout(
        height=650, template=template, xaxis_rangeslider_visible=False, title=f"{ticker.upper()} – {period.upper()} Chart",
        showlegend=False, xaxis=dict(rangeselector=dict(buttons=[
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
        ]), rangeslider_visible=False, type="date")
    )
    return fig

# Top 10 High Interest Bonds & ETFs (2025 data)
HIGH_INTEREST_ASSETS = {
    # High Yield Bond ETFs
    "HYG": "iShares iBoxx $ High Yield Corporate Bond ETF (~7.8% yield)",
    "JNK": "SPDR Bloomberg High Yield Bond ETF (~7.5%)",
    "USHY": "iShares Broad USD High Yield Corporate Bond ETF (~7.6%)",
    "BKLN": "Invesco Senior Loan ETF (~8.5%)",
    "SJNK": "SPDR Bloomberg Short Term High Yield Bond ETF (~7.9%)",
    "FALN": "iShares Fallen Angels USD Bond ETF (~7.2%)",
    "ANGL": "VanEck Fallen Angel High Yield Bond ETF (~7.0%)",
    # High Dividend ETFs
    "SDIV": "Global X SuperDividend ETF (~9.7%)",
    "QYLD": "Global X NASDAQ 100 Covered Call ETF (~11.5%)",
    "JEPI": "JPMorgan Equity Premium Income ETF (~8.5%)"
}

# Top 20 Movers (Gainers/Losers)
@st.cache_data(ttl=300)
def get_top_movers():
    try:
        # Fetch S&P 500 for movers
        sp500 = yf.Ticker("^GSPC").history(period="2d")
        movers = []
        for ticker in ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA', 'BRK-B', 'LLY', 'AVGO', 'JPM', 'JNJ', 'V', 'PG', 'UNH', 'MA', 'HD', 'XOM', 'CVX', 'BAC']:  # Sample top stocks
            t = yf.Ticker(ticker)
            info = t.info
            hist = t.history(period="2d")
            if not hist.empty:
                prev_close = hist['Close'].iloc[-2]
                current = info.get('regularMarketPrice') or hist['Close'].iloc[-1]
                pct = ((current - prev_close) / prev_close) * 100
                movers.append({'ticker': ticker, 'current': current, 'pct': pct, 'volume': info.get('volume', 0)})
        movers.sort(key=lambda x: x['pct'], reverse=True)
        return movers[:20]
    except:
        return []

# Stock News Grid
@st.cache_data(ttl=1800)
def get_stock_news():
    try:
        # Sample from major tickers
        news = []
        for ticker in ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA']:
            t = yf.Ticker(ticker)
            for item in t.news[:2]:  # Top 2 per ticker
                news.append({
                    'title': item.get('title', 'No title'),
                    'publisher': item.get('publisher', 'Unknown'),
                    'link': item.get('link', ''),
                    'uuid': item.get('uuid', '')
                })
        return news[:10]  # Top 10 total
    except:
        return []

# TABS (Now 8 tabs)
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
    "Symbol Lookup", "AI Forecast", "High Interest Bonds/ETFs", "Top 20 Movers", "Stock News Grid",
    "Bond ETFs", "Dividend ETFs", "Portfolio"
])

# TAB 1: Symbol Lookup
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
                with col1: st.subheader(symbol)
                with col2: st.write(r["name"]); st.caption(r["exchange"])
                with col3: st.metric("Current", f"${current:,.2f}"); st.caption(f"Open: ${open_p:,.2f}")
                with col4: st.metric("Today", f"{change:+.2f}", f"{pct:+.2f}%")
                if st.button("Add to Portfolio", key=symbol): portfolio.append({"ticker": symbol, "shares": 100.0, "buy_price": current}); save_portfolio(); st.success("Added!")
                period = st.selectbox("Chart Period", ["1d","5d","1mo","3mo","6mo","ytd","1y","2y","5y","max"], key=f"period_{symbol}")
                chart = plot_chart(symbol, period)
                if chart: st.plotly_chart(chart, use_container_width=True)
                st.divider()
        else:
            st.error("No results")

# TAB 2: AI Forecast
with tab2:
    st.header("AI 3-Month Forecast")
    ticker = st.text_input("Ticker", "JEPI").upper()
    current, open_p, _, _ = get_price_info(ticker)
    st.write(f"**{ticker}** • Current: ${current:,.2f} • Open: ${open_p:,.2f}")
    period = st.selectbox("Chart Period", ["1d","5d","1mo","3mo","6mo","ytd","1y","2y","5y","max"], key="ai_period")
    chart = plot_chart(ticker, period)
    if chart: st.plotly_chart(chart, use_container_width=True)

# TAB 3: High Interest Bonds & ETFs (NEW!)
with tab3:
    st.header("Top 10 High Interest Bonds & ETFs (2025)")
    for symbol, desc in HIGH_INTEREST_ASSETS.items():
        current, _, _, pct = get_price_info(symbol)
        col1, col2, col3 = st.columns([2, 2, 6])
        with col1: st.subheader(symbol)
        with col2: st.metric("Price", f"${current:,.2f}", f"{pct:+.2f}%")
        with col3: st.caption(desc)
        if st.button(f"Add {symbol}", key=f"add_{symbol}"): portfolio.append({"ticker": symbol, "shares": 100.0, "buy_price": current}); save_portfolio(); st.success("Added!")
        st.divider()

# TAB 4: Top 20 Movers (NEW!)
with tab4:
    st.header("Top 20 Movers by % Today")
    movers = get_top_movers()
    if movers:
        df = pd.DataFrame(movers)
        st.dataframe(df.sort_values('pct', ascending=False).head(10), use_container_width=True)  # Top 10 gainers
        st.dataframe(df.sort_values('pct').head(10), use_container_width=True)  # Top 10 losers
    else:
        st.error("No data – try later")

# TAB 5: Stock News Grid (NEW!)
with tab5:
    st.header("Top Stock News (Grid View)")
    news_items = get_stock_news()
    if news_items:
        cols = st.columns(5)  # 5-column grid
        for i, item in enumerate(news_items):
            with cols[i % 5]:
                st.markdown(f"**{item['title'][:50]}...**")
                st.caption(item['publisher'])
                if st.button("Read Full", key=item['uuid']):
                    st.markdown(f"[Open Article]({item['link']})")
    else:
        st.error("No news – try later")

# TAB 6: Bond ETFs
with tab6:
    st.header("Top Bond ETFs")
    for t in ["ZAG.TO","BND","TLT","HYG"]:
        c, o, ch, pct = get_price_info(t)
        st.metric(t, f"${c:,.2f}", f"{ch:+.2f} ({pct:+.2f}%)")

# TAB 7: Dividend ETFs
with tab7:
    st.header("Top Dividend ETFs")
    for t in ["HMAX.TO","JEPI","JEPQ","SCHD"]:
        c, o, ch, pct = get_price_info(t)
        st.metric(t, f"${c:,.2f}", f"{ch:+.2f} ({pct:+.2f}%)")

# TAB 8: Portfolio
with tab8:
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
        st.info("Add from other tabs!")

st.sidebar.success("New: High Yield Tab + Movers + News Grid!")
st.sidebar.caption(f"Live • {datetime.now().strftime('%H:%M:%S')}")