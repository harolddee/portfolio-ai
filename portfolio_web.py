# portfolio_web.py – FINAL: 100% Crypto + Stock Compatible (Nov 2025)
import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
from datetime import datetime
from groq import Groq
from dotenv import load_dotenv
import os

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

st.set_page_config(page_title="Crypto & Stocks AI Pro", layout="wide")
st.title("Crypto + Stocks Portfolio + AI Analyst")
st.caption("BTC • ETH • SOL • DOGE • NVDA • All in one • Live charts • Llama 3.3 70B")

PORTFOLIO_FILE = "my_portfolio.csv"

@st.cache_data(ttl=60)
def load_portfolio():
    return pd.read_csv(PORTFOLIO_FILE).to_dict('records') if os.path.exists(PORTFOLIO_FILE) else []

portfolio = load_portfolio()

def save_portfolio():
    pd.DataFrame(portfolio).to_csv(PORTFOLIO_FILE, index=False)

# Safe number formatting
def fmt(num):
    return f"${num:,.0f}" if isinstance(num, (int, float)) and num else "N/A"

# Interactive chart
def plot_chart(ticker, period="6mo"):
    df = yf.Ticker(ticker).history(period=period)
    if df.empty:
        return None
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.7, 0.3])
    fig.add_trace(go.Candlestick(x=df.index, open=df.Open, high=df.High, low=df.Low, close=df.Close, name="Price"), row=1, col=1)
    fig.add_trace(go.Bar(x=df.index, y=df.Volume, name="Volume", marker_color='rgba(100,200,255,0.4)'), row=2, col=1)
    fig.update_layout(height=700, xaxis_rangeslider_visible=False, template="plotly_dark", showlegend=False)
    fig.update_yaxes(title_text="Price", row=1, col=1)
    fig.update_yaxes(title_text="Volume", row=2, col=1)
    fig.update_layout(title=f"{ticker.upper()} – Live Chart")
    return fig

# Tabs
tab1, tab2, tab3 = st.tabs(["AI + Chart", "Portfolio", "Add Position"])

# TAB 1
with tab1:
    st.header("Analyze Any Asset")
    col1, col2 = st.columns([1, 3])
    with col1:
        ticker = st.text_input("Ticker", value="BTC-USD").upper()
        period = st.selectbox("Chart Period", ["1d","5d","1mo","3mo","6mo","1y","2y","5y"], index=4)
    
    if st.button("Analyze + Load Chart", type="primary"):
        with st.spinner("Analyzing..."):
            stock = yf.Ticker(ticker)
            info = stock.info
            hist = stock.history(period="1mo")
            current = info.get("currentPrice") or info.get("regularMarketPrice") or 0
            prev = info.get("regularMarketPreviousClose") or current
            change = round(((current-prev)/prev)*100, 2) if prev else 0

            market_cap = info.get("marketCap")
            volume_24h = info.get("volume") or info.get("regularMarketVolume")

            news_raw = stock.news[:6] if hasattr(stock, 'news') else []
            news = [{"title": n.get("title","News"), "publisher": n.get("publisher","Source")} for n in news_raw]

            recent_prices = "\n".join([f"{d.strftime('%m-%d %H:%M') if 'USD' in ticker else d.date()}: ${c:.2f}" 
                                      for d, c in hist["Close"].tail(10).items()])

            prompt = f"""Analyze {ticker.upper()} now:
Price: ${current:,.2f} ({change:+.2f}%)
Market Cap: {fmt(market_cap)}
24h Volume: {fmt(volume_24h)}

Recent prices:
{recent_prices}

Latest news:
{json.dumps(news[:4], indent=2)}

Give a sharp 250–350 word analysis:
• Technicals & momentum
• Key levels
• Risks / catalysts
• Final call: Strong Buy | Buy | Hold | Sell | Strong Sell
"""
            response = client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama-3.3-70b-versatile",
                temperature=0.5,
                max_tokens=1000
            ).choices[0].message.content

            st.success(f"{ticker} • ${current:,.2f} ({change:+.2f}%)")
            st.markdown("### AI Analysis")
            st.markdown(response)

    if 'ticker' in locals():
        chart = plot_chart(ticker, period)
        if chart:
            st.plotly_chart(chart, use_container_width=True)

# TAB 2 – PORTFOLIO
with tab2:
    st.header("Live Portfolio")
    if not portfolio:
        st.info("Add your first position!")
    else:
        rows = []
        total_cost = total_value = 0
        pie_labels = []
        pie_values = []

        for p in portfolio:
            live = yf.Ticker(p["ticker"]).info.get("regularMarketPrice") or \
                   yf.Ticker(p["ticker"]).info.get("currentPrice") or 0
            value = p["shares"] * live
            cost = p["shares"] * p["buy_price"]
            gain = value - cost
            gain_pct = (gain/cost)*100 if cost else 0

            total_cost += cost
            total_value += value
            pie_labels.append(f"{p['ticker']} (${value:,.0f})")
            pie_values.append(value)

            rows.append({
                "Asset": p["ticker"],
                "Amount": f"{p['shares']:,.6f}".rstrip('0').rstrip('.'),
                "Buy $": f"${p['buy_price']:,.2f}",
                "Now $": f"${live:,.4f}",
                "Value": f"${value:,.0f}",
                "Gain": f"{gain:+,.0f} ({gain_pct:+.2f}%)"
            })

        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True)

        total_gain = total_value - total_cost
        total_pct = (total_gain/total_cost)*100 if total_cost else 0
        c1, c2, c3 = st.columns(3)
        c1.metric("Invested", f"${total_cost:,.0f}")
        c2.metric("Current Value", f"${total_value:,.0f}")
        c3.metric("Total Gain", f"${total_gain:+,.0f}", f"{total_pct:+.2f}%")

        fig = go.Figure(go.Pie(labels=pie_labels, values=pie_values, hole=0.5, textinfo='label+percent'))
        fig.update_layout(title="Portfolio Allocation", template="plotly_dark")
        st.plotly_chart(fig, use_container_width=True)

# TAB 3
with tab3:
    st.header("Add Position")
    with st.form("add"):
        c1, c2, c3 = st.columns(3)
        with c1: t = st.text_input("Ticker", "ETH-USD").upper()
        with c2: s = st.number_input("Amount", 0.000001, value=1.0)
        with c3: p = st.number_input("Avg Buy $", 0.01)
        if st.form_submit_button("Add"):
            portfolio.append({"ticker": t, "shares": s, "buy_price": p})
            save_portfolio()
            st.success(f"{t} × {s} @ ${p} added!")
            st.rerun()

st.sidebar.success("Crypto + Stocks • Zero Errors • Pro Dashboard")
st.sidebar.caption(f"Live • {datetime.now().strftime('%H:%M:%S')}")