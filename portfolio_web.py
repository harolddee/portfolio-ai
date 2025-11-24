# portfolio_web.py – FINAL FIXED: Symbol Lookup + Open/Current + Charts + Clean ETF Tabs
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
st.caption("Type company name → Open & Current price + Chart • Bonds • Dividends • Crypto")

PORTFOLIO_FILE = "my_portfolio.csv"
@st.cache_data(ttl=60)
def load_portfolio():
    return pd.read_csv(PORTFOLIO_FILE).to_dict('records') if os.path.exists(PORTFOLIO_FILE) else []
portfolio = load_portfolio()
def save_portfolio():
    pd.DataFrame(portfolio).to_csv(PORTFOLIO_FILE, index=False)

# SYMBOL LOOKUP
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
        hist = t.history(period="2d", interval="1m")
        current = info.get("regularMarketPrice") or info.get("currentPrice") or 0
        open_price = info.get("regularMarketOpen") or (hist["Open"].iloc[-1] if not hist.empty else 0)
        change = current - open_price
        change_pct = (change / open_price) * 100 if open_price else 0
        return round(current, 4), round(open_price, 4), round(change, 4), round(change_pct, 2)
    except:
        return 0, 0, 0, 0

def plot_chart(ticker):
    df = yf.Ticker(ticker).history(period="6mo")
    if df.empty: return None
    fig = go.Figure()
    fig.add_trace(go.Candlestick(x=df.index, open=df.Open, high=df.High, low=df.Low, close=df.Close, name=ticker))
    fig.update_layout(height=600, template=template, xaxis_rangeslider_visible=False,
                      title=f"{ticker.upper()} – 6-Month Chart", showlegend=False)
    return fig

# TABS
tab1, tab2, tab3, tab4, tab5 = st.tabs(["Symbol Lookup", "AI Forecast", "Bond ETFs", "Dividend ETFs", "Portfolio"])

# TAB 1 – SYMBOL LOOKUP + OPEN/CURRENT + CHART
with tab1:
    st.header("Smart Symbol Lookup")
    query = st.text_input("Type any company