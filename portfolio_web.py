# portfolio_web.py – ULTIMATE: Stocks + Crypto + Dividend ETFs + Bond ETFs + AI Forecast
import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
from groq import Groq
import os

client = Groq(api_key=st.secrets.get("GROQ_API_KEY") or os.getenv("GROQ_API_KEY"))

st.set_page_config(page_title="Ultimate Portfolio Pro", layout="wide")

# Theme
theme = st.sidebar.radio("Theme", ["Dark", "Light"], horizontal=True)
template = "plotly_dark" if theme == "Dark" else "plotly_white"

st.title("Ultimate Portfolio: Stocks • Crypto • Dividend + Bond ETFs")
st.caption("JEPI • HMAX • ZAG.TO • BND • TLT • HYG • Live + AI + Yield")

PORTFOLIO_FILE = "my_portfolio.csv"
@st.cache_data(ttl=60)
def load_portfolio():
    return pd.read_csv(PORTFOLIO_FILE).to_dict('records') if os.path.exists(PORTFOLIO_FILE) else []

portfolio = load_portfolio()
def save_portfolio():
    pd.DataFrame(portfolio).to_csv(PORTFOLIO_FILE, index=False)

# Top Bond ETFs (2025)
BOND_ETFS = {
    "ZAG.TO": "BMO Aggregate Bond Index (Canada) – ~4.8%",
    "XBB.TO": "iShares Core Canadian Universe Bond – ~4.6%",
    "VAB.TO": "Vanguard Canadian Aggregate Bond – ~4.7%",
    "BND": "Vanguard Total Bond Market (US) – ~4.8%",
    "TLT": "iShares 20+ Year Treasury Bond – ~4.5% (long duration)",
    "IEF": "iShares 7-10 Year Treasury – ~4.3%",
    "LQD": "iShares Investment Grade Corporate – ~5.2%",
    "HYG": "iShares High Yield Corporate – ~7.8%",
    "EMB": "iShares Emerging Markets Bond – ~6.5%",
    "BKLN": "Invesco Senior Loan (Floating Rate) – ~8.5%"
}

def get_price_yield_duration(ticker):
    try:
        info = yf.Ticker(ticker).info
        price = info.get("regularMarketPrice") or info.get("currentPrice") or 0
        div_yield = info.get("trailingAnnualDividendYield")
        yield_pct = f"{div_yield*100:.2f}%" if div_yield else "N/A"
        duration = info.get("averageMaturity") or info.get("duration") or "N/A"
        return price, yield_pct, duration
    except:
        return 0, "N/A", "N/A"

def plot_chart(ticker, period="1y"):
    df = yf.Ticker(ticker).history(period=period)
    if df.empty: return None
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df.index, y=df.Close, mode='lines', name="Price", line=dict(width=3)))
    fig.update_layout(height=600, template=template, xaxis_rangeslider_visible=False,
                      title=f"{ticker.upper()} – Live Chart")
    return fig

def get_ai_forecast(ticker):
    try:
        info = yf.Ticker(ticker).info
        current = info.get("regularMarketPrice") or info.get("currentPrice") or 0
        yld = info.get("trailingAnnualDividendYield", 0)
        prompt = f"""Forecast {ticker.upper()} price in 3 months.
Current: ${current:,.2f} | Yield: {yld*100:.2f}% | Type: {'Bond ETF' if ticker in BOND_ETFS else 'Other'}
Return only: PRICE: $XX.XX | CONFIDENCE: High/Medium/Low | REASON: short sentence"""
        resp = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role":"user","content":prompt}],
            temperature=0.4, max_tokens=120
        ).choices[0].message.content.strip()
        return resp
    except:
        return "AI unavailable"

# TABS
tab1, tab2, tab3, tab4, tab5 = st.tabs(["AI + Forecast", "Bond ETFs", "Dividend ETFs", "Portfolio", "Add"])

with tab1:
    st.header("AI Analysis + 3-Month Forecast")
    ticker = st.text_input("Any ticker", "ZAG.TO").upper()
    if st.button("Analyze + Forecast", type="primary"):
        with st.spinner("Thinking..."):
            forecast = get_ai_forecast(ticker)
            price, yld, dur = get_price_yield_duration(ticker)
            st.success(f"**{ticker}** • ${price:,.2f} • Yield: {yld} • Duration: {dur}")
            st.markdown(f"### 3-Month AI Forecast\n{forecast}")
    chart = plot_chart(ticker)
    if chart: st.plotly_chart(chart, use_container_width=True)

with tab2:
    st.header("Top Bond ETFs (2025)")
    for etf, desc in BOND_ETFS.items():
        price, yld, dur = get_price_yield_duration(etf)
        col1, col2, col3, col4 = st.columns([2, 2, 2, 4])
        col1.write(f"**{etf}**")
        col2.write(f"${price:,.2f}")
        col3.write(f"**{yld}**")
        col4.caption(desc)
        st.divider()

with tab3:
    st.header("Top Dividend ETFs")
    div_etfs = ["HMAX.TO","JEPI","JEPQ","QYLD","XYLD","SCHD","DIV","SDIV"]
    for etf in div_etfs:
        price, yld, _ = get_price_yield_duration(etf)
        col1, col2, col3 = st.columns([2,2,4])
        col1.write(f"**{etf}**")
        col2.write(f"${price:,.2f}")
        col3.write(f"Yield: **{yld}**")
        st.divider()

with tab4:
    st.header("Live Portfolio (All Assets + Yields)")
    if not portfolio:
        st.info("Add positions →")
    else:
        rows = []; total_cost = total_value = 0; pie_l = []; pie_v = []
        for p in portfolio:
            price, yld, dur = get_price_yield_duration(p["ticker"])
            value = p["shares"] * price
            cost = p["shares"] * p["buy_price"]
            gain = value - cost
            gain_pct = (gain/cost)*100 if cost else 0
            total_cost += cost; total_value += value
            pie_l.append(f"{p['ticker']} (${value:,.0f})"); pie_v.append(value)
            rows.append({
                "Asset": p["ticker"], "Shares": p["shares"], "Buy $": f"${p['buy_price']:,.2f}",
                "Now $": f"${price:,.2f}", "Value": f"${value:,.0f}",
                "Yield": yld, "Duration": dur, "Gain": f"{gain:+,.0f} ({gain_pct:+.2f}%)"
            })
        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True)
        c1,c2,c3 = st.columns(3)
        total_gain = total_value - total_cost
        total_pct = (total_gain/total_cost)*100 if total_cost else 0
        c1.metric("Invested", f"${total_cost:,.0f}")
        c2.metric("Value", f"${total_value:,.0f}")
        c3.metric("Gain", f"${total_gain:+,.0f}", f"{total_pct:+.2f}%")
        fig = go.Figure(go.Pie(labels=pie_l, values=pie_v, hole=0.4, textinfo='label+percent'))
        fig.update_layout(template=template, title="Allocation")
        st.plotly_chart(fig, use_container_width=True)

with tab5:
    st.header("Add Any Asset")
    with st.form("add"):
        c1,c2,c3 = st.columns(3)
        with c1: t = st.text_input("Ticker", "TLT").upper()
        with c2: s = st.number_input("Shares", 0.01, value=100.0)
        with c3: p = st.number_input("Buy Price $", 0.01)
        if st.form_submit_button("Add"):
            portfolio.append({"ticker":t,"shares":s,"buy_price":p})
            save_portfolio()
            st.success("Added!")
            st.rerun()

st.sidebar.success("Bonds • Dividends • Stocks • Crypto • AI")
st.sidebar.caption(f"Live • {datetime.now().strftime('%H:%M')}")