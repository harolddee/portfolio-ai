# portfolio_web.py – FINAL: Dividend ETFs + Stocks + Crypto + AI Forecast + Dark/Light
import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
from groq import Groq
import os

# Get API key (works locally and on Streamlit Cloud)
client = Groq(api_key=st.secrets.get("GROQ_API_KEY") or os.getenv("GROQ_API_KEY"))

st.set_page_config(page_title="Ultimate Portfolio Pro", layout="wide")

# Dark / Light Mode
theme = st.sidebar.radio("Theme", ["Dark", "Light"], horizontal=True)
template = "plotly_dark" if theme == "Dark" else "plotly_white"

st.title("Ultimate Portfolio: ETFs • Stocks • Crypto")
st.caption("JEPI • JEPQ • HMAX.TO • QYLD • SCHD • Live + AI + Dividends")

PORTFOLIO_FILE = "my_portfolio.csv"

@st.cache_data(ttl=60)
def load_portfolio():
    if os.path.exists(PORTFOLIO_FILE):
        return pd.read_csv(PORTFOLIO_FILE).to_dict('records')
    return []

portfolio = load_portfolio()
def save_portfolio():
    pd.DataFrame(portfolio).to_csv(PORTFOLIO_FILE, index=False)

# Top Dividend ETFs
HIGH_DIV_ETFS = [
    "HMAX.TO", "JEPI", "JEPQ", "QYLD", "XYLD", "RYLD",
    "SCHD", "DIV", "SDIV", "SPYD", "VYM", "DVY"
]

def get_price_and_yield(ticker):
    try:
        info = yf.Ticker(ticker).info
        price = info.get("regularMarketPrice") or info.get("currentPrice") or 0
        div_yield = info.get("trailingAnnualDividendYield")
        yield_pct = f"{div_yield*100:.2f}%" if div_yield else "N/A"
        return price, yield_pct
    except:
        return 0, "N/A"

def plot_chart(ticker, period="1y"):
    df = yf.Ticker(ticker).history(period=period)
    if df.empty: return None
    fig = go.Figure()
    fig.add_trace(go.Candlestick(x=df.index, open=df.Open, high=df.High,
                                 low=df.Low, close=df.Close, name="Price"))
    fig.update_layout(height=600, template=template, xaxis_rangeslider_visible=False,
                      title=f"{ticker.upper()} – Live Chart")
    return fig

def get_ai_forecast(ticker):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        current = info.get("regularMarketPrice") or info.get("currentPrice") or 0
        div_yield = info.get("trailingAnnualDividendYield", 0)
        prompt = f"""Forecast {ticker.upper()} price in 3 months.
Current: ${current:,.2f} | Yield: {div_yield*100:.2f}% | Market Cap: {info.get('marketCap','N/A'):,}
Give only: PRICE: $X,XXX | CONFIDENCE: High/Medium/Low | REASON: short sentence"""
        resp = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4,
            max_tokens=120
        ).choices[0].message.content.strip()
        return resp
    except:
        return "AI unavailable – check your key"

# TABS
tab1, tab2, tab3, tab4 = st.tabs(["AI + Forecast", "Dividend ETFs", "Portfolio", "Add"])

# TAB 1
with tab1:
    st.header("AI Analysis + 3-Month Forecast")
    ticker = st.text_input("Enter ticker", "JEPI").upper()
    if st.button("Get Forecast", type="primary"):
        with st.spinner("AI thinking..."):
            forecast = get_ai_forecast(ticker)
            price, yield_pct = get_price_and_yield(ticker)
            st.success(f"**{ticker}** • ${price:,.2f} • Yield: {yield_pct}")
            st.markdown(f"### 3-Month AI Forecast\n{forecast}")
    chart = plot_chart(ticker)
    if chart: st.plotly_chart(chart, use_container_width=True)

# TAB 2 – Dividend ETFs
with tab2:
    st.header("Top Dividend ETFs (2025)")
    for etf in HIGH_DIV_ETFS:
        price, yield_pct = get_price_and_yield(etf)
        col1, col2, col3 = st.columns([2, 2, 4])
        col1.write(f"**{etf}**")
        col2.write(f"**${price:,.2f}**" if price else "Loading...")
        col3.write(f"**Yield: {yield_pct}**")
        st.divider()

# TAB 3 – Portfolio
with tab3:
    st.header("Live Portfolio (with Dividend Yield)")
    if not portfolio:
        st.info("No holdings yet → Add in last tab")
    else:
        rows = []
        total_cost = total_value = 0
        pie_labels = []
        pie_values = []

        for p in portfolio:
            live_price, div_yield = get_price_and_yield(p["ticker"])
            value = p["shares"] * live_price
            cost = p["shares"] * p["buy_price"]
            gain = value - cost
            gain_pct = (gain / cost) * 100 if cost else 0

            total_cost += cost
            total_value += value
            pie_labels.append(f"{p['ticker']} (${value:,.0f})")
            pie_values.append(value)

            rows.append({
                "Asset": p["ticker"],
                "Shares": p["shares"],
                "Buy $": f"${p['buy_price']:,.2f}",
                "Now $": f"${live_price:,.2f}",
                "Value": f"${value:,.0f}",
                "Yield": div_yield,
                "Gain": f"{gain:+,.0f} ({gain_pct:+.2f}%)"
            })

        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True)

        col1, col2, col3 = st.columns(3)
        total_gain = total_value - total_cost
        total_pct = (total_gain / total_cost) * 100 if total_cost else 0
        col1.metric("Invested", f"${total_cost:,.0f}")
        col2.metric("Current Value", f"${total_value:,.0f}")
        col3.metric("Total Gain", f"${total_gain:+,.0f}", f"{total_pct:+.2f}%")

        fig = go.Figure(go.Pie(labels=pie_labels, values=pie_values, hole=0.4, textinfo='label+percent'))
        fig.update_layout(template=template, title="Portfolio Allocation")
        st.plotly_chart(fig, use_container_width=True)

# TAB 4 – Add
with tab4:
    st.header("Add Position")
    with st.form("add"):
        c1, c2, c3 = st.columns(3)
        with c1: ticker = st.text_input("Ticker", "HMAX.TO").upper()
        with c2: shares = st.number_input("Shares", 0.01, value=100.0)
        with c3: buy_price = st.number_input("Buy Price $", 0.01)
        if st.form_submit_button("Add to Portfolio"):
            portfolio.append({"ticker": ticker, "shares": shares, "buy_price": buy_price})
            save_portfolio()
            st.success(f"{ticker} × {shares} @ ${buy_price} added!")
            st.rerun()

st.sidebar.success("Dividend ETFs • AI Forecast • Dark/Light Mode")
st.sidebar.caption(f"Live • {datetime.now().strftime('%H:%M')}")