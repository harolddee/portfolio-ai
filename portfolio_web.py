# portfolio_web.py – ULTIMATE: Stocks + Crypto + Dividend ETFs + 3-Month Forecast + Dark/Light
import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
from datetime import datetime
from groq import Groq
import os

client = Groq(api_key=st.secrets.get("GROQ_API_KEY"))

st.set_page_config(page_title="Ultimate Portfolio Pro", layout="wide")

# Dark / Light Mode
theme = st.sidebar.radio("Theme", ["Dark", "Light"], horizontal=True)
template = "plotly_dark" if theme == "Dark" else "plotly_white"

st.title("Ultimate Portfolio: Stocks • Crypto • Dividend ETFs")
st.caption("JEPI • JEPQ • QYLD • SCHD • HMAX • Real-time + AI + 3-month forecast")

PORTFOLIO_FILE = "my_portfolio.csv"
@st.cache_data(ttl=60)
def load_portfolio():
    return pd.read_csv(PORTFOLIO_FILE).to_dict('records') if os.path.exists(PORTFOLIO_FILE) else []
portfolio = load_portfolio()
def save_portfolio(): pd.DataFrame(portfolio).to_csv(PORTFOLIO_FILE, index=False)

# High-dividend ETF list (auto-shows yield)
HIGH_DIV_ETFS = {
    "HMAX.TO": "Hamilton Canadian Financials Yield Maximizer (~16-19% monthly)",
    "JEPI": "JPMorgan Equity Premium Income (8-11% monthly)",
    "JEPQ": "JPMorgan Nasdaq Equity Premium (9-13% monthly)",
    "QYLD": "Global X Nasdaq 100 Covered Call (11-13% monthly)",
    "XYLD": "Global X S&P 500 Covered Call (10-12% monthly)",
    "SCHD": "Schwab US Dividend Equity (3.7% quarterly – stable)",
    "DIV": "Global X SuperDividend (8-9% monthly)",
    "SDIV": "Global X SuperDividend (10-12% monthly)"
}

def fmt(num): return f"${num:,.0f}" if isinstance(num, (int,float)) and num else "N/A"

def plot_chart(ticker, period="1y"):
    df = yf.Ticker(ticker).history(period=period)
    if df.empty: return None
    fig = go.Figure()
    fig.add_trace(go.Candlestick(x=df.index, open=df.Open, high=df.High, low=df.Low, close=df.Close))
    fig.update_layout(height=600, template=template, xaxis_rangeslider_visible=False,
                      title=f"{ticker.upper()} – Live Chart")
    return fig

def get_forecast(ticker):
    stock = yf.Ticker(ticker)
    info = stock.info
    hist = stock.history(period="2y")
    if hist.empty: return "No data", "N/A"
    current = hist['Close'].iloc[-1]
    div_yield = info.get("trailingAnnualDividendYield")
    yield_pct = f"{div_yield*100:.2f}%" if div_yield else "N/A"

    prompt = f"""Forecast {ticker.upper()} in 3 months.
Current price: ${current:,.2f}
Trailing dividend yield: {yield_pct}
Market cap: {fmt(info.get('marketCap'))}
92-day performance: {((current/hist['Close'].iloc[-92])-1)*100:+.2f}% if enough data

Return ONLY:
PRICE: $X,XXX | CONFIDENCE: High/Medium/Low | REASON: short sentence
"""
    try:
        resp = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role":"user","content":prompt}],
            temperature=0.4, max_tokens=120
        ).choices[0].message.content.strip()
    except:
        resp = "PRICE: N/A | CONFIDENCE: N/A | REASON: AI unavailable"
    return resp, yield_pct

tab1, tab2, tab3, tab4 = st.tabs(["AI + Forecast", "Dividend ETFs", "Portfolio", "Add"])

# TAB 1 – Any asset
with tab1:
    st.header("AI Analysis + 3-Month Forecast")
    ticker = st.text_input("Any ticker", "JEPI").upper()
    if st.button("Analyze + Forecast", type="primary"):
        forecast, div_yield = get_forecast(ticker)
        st.success(f"**{ticker}** • Yield: {div_yield}")
        st.markdown(f"### 3-Month AI Forecast\n{forecast}")
    chart = plot_chart(ticker)
    if chart: st.plotly_chart(chart, use_container_width=True)

# TAB 2 – High Dividend ETFs
with tab2:
    st.header("Top Dividend ETFs (2025)")
    for etf, desc in HIGH_DIV_ETFS.items():
        col1, col2, col3 = st.columns([1,2,2])
        with col1:
            st.write(f"**{etf}**")
        with col2:
            price =  # live price
            price = yf.Ticker(etf).info.get("regularMarketPrice") or yf.Ticker(etf).info.get("currentPrice")
            if price: st.write(f"**${price:.2f}**")
        with col3:
            st.caption(desc)
        st.divider()

# TAB 3 – Portfolio (now shows dividend yield too)
with tab3:
    st.header("Live Portfolio")
    if not portfolio:
        st.info("Add positions →")
    else:
        rows = []; total_cost = total_value = 0; pie_l = []; pie_v = []
        for p in portfolio:
            live = yf.Ticker(p["ticker"]).info.get("regularMarketPrice")  # supports HMAX.TO, JEPI, etc.
            live = live or yf.Ticker(p["ticker"]).info.get("currentPrice") or 0
            value = p["shares"] * live
            cost = p["shares"] * p["buy_price"]
            gain = value - cost
            gain_pct = (gain/cost)*100 if cost else 0
            div_yield = yf.Ticker(p["ticker"]).info.get("trailingAnnualDividendYield")
            yield_str = f"{div_yield*100:.2f}%" if div_yield else "N/A"
            total_cost += cost; total_value += value
            pie_l.append(f"{p['ticker']} (${value:,.0f})"); pie_v.append(value)
            rows.append({"Asset":p["ticker"],"Shares":p["shares"],"Buy":p["buy_price"],
                         "Now":f"${live:,.2f}","Value":f"${value:,.0f}",
                         "Yield":yield_str,"Gain":f"{gain:+,.0f} ({gain_pct:+.2f}%)"})
        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True)
        c1,c2,c3 = st.columns(3)
        c1.metric("Invested", f"${total_cost:,.0f}")
        c2.metric("Value", f"${total_value:,.0f}")
        c3.metric("Gain", f"${total_value-total_cost:+,.0f}", f"{(total_value/total_cost-1)*100:+.2f}%")
        fig = go.Figure(go.Pie(labels=pie_l, values=pie_v, hole=0.4, textinfo='label+percent'))
        fig.update_layout(template=template, title="Allocation")
        st.plotly_chart(fig, use_container_width=True)

# TAB 4 – Add
with tab4:
    st.header("Add Position")
    with st.form("add"):
        c1,c2,c3 = st.columns(3)
        with c1: t = st.text_input("Ticker", "HMAX.TO").upper()
        with c2: s = st.number_input("Shares", 0.01, value=100.0)
        with c3: p = st.number_input("Buy Price $", 0.01)
        if st.form_submit_button("Add"):
            portfolio.append({"ticker":t,"shares":s,"buy_price":p})
            save_portfolio()
            st.success("Added!")
            st.rerun()

st.sidebar.success("Stocks • Crypto • Dividend ETFs • AI Forecast")
st.sidebar.caption(f"Live • {datetime.now().strftime('%H:%M')}")