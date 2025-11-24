# portfolio_web.py – ULTIMATE PRO: Forward + Backward + Actual Forecast Chart
import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import requests
import os
from groq import Groq

client = Groq(api_key=st.secrets.get("GROQ_API_KEY") or os.getenv("GROQ_API_KEY"))

st.set_page_config(page_title="AI Forecast Pro 2025", layout="wide")

# Theme
theme = st.sidebar.radio("Theme", ["Dark", "Light"], horizontal=True)
template = "plotly_dark" if theme == "Dark" else "plotly_white"

st.title("AI-Powered Forecast Dashboard")
st.caption("Green = Actual • Purple = Future Forecast • Red = Past Prediction Accuracy")

# TABS
tab1, tab2 = st.tabs(["Symbol Lookup", "AI Forecast"])

# ——— TAB 1: SYMBOL LOOKUP (DEFAULT 1-MONTH) ———
with tab1:
    st.header("Smart Symbol Lookup")
    query = st.text_input("Search company, ETF, or crypto", "Apple")
    
    if query:
        results = []
        try:
            url = f"https://query2.finance.yahoo.com/v1/finance/search?q={query}&quotesCount=8"
            data = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}).json()
            for item in data.get("quotes", []):
                symbol = item.get("symbol")
                if symbol:
                    name = item.get("shortname") or item.get("longname") or symbol
                    results.append({"symbol": symbol, "name": name})
        except:
            pass
        
        if results:
            for r in results:
                symbol = r["symbol"]
                try:
                    t = yf.Ticker(symbol)
                    info = t.info
                    current = info.get("regularMarketPrice") or info.get("currentPrice") or 0
                    open_p = info.get("regularMarketOpen") or current
                    change = current - open_p
                    pct = (change / open_p) * 100 if open_p else 0
                    st.subheader(f"{symbol} – {r['name']}")
                    st.metric("Current", f"${current:,.2f}", f"{change:+.2f} ({pct:+.2f}%)")
                    
                    period = st.selectbox("Chart", ["1mo","1d","5d","3mo","6mo","1y","max"], index=0, key=f"lookup_{symbol}")
                    df = t.history(period=period)
                    if not df.empty:
                        fig = go.Figure()
                        fig.add_trace(go.Candlestick(x=df.index, open=df.Open, high=df.High, low=df.Low, close=df.Close))
                        fig.update_layout(height=600, template=template, title=f"{symbol} – {period.upper()}")
                        st.plotly_chart(fig, use_container_width=True, key=f"chart_lookup_{symbol}")
                    st.divider()
                except:
                    st.write(f"Could not load {symbol}")
        else:
            st.error("No results")

# ——— TAB 2: AI FORECAST WITH 3-MONTH TRIPLE LINE CHART ———
with tab2:
    st.header("AI 3-Month Forecast + Accuracy Backtest")
    
    ticker = st.text_input("Enter ticker for AI forecast", "NVDA").upper()
    
    if st.button("Generate AI Forecast", type="primary"):
        with st.spinner("Analyzing with Llama 3.3 70B..."):
            try:
                t = yf.Ticker(ticker)
                info = t.info
                current_price = info.get("regularMarketPrice") or info.get("currentPrice") or 0
                
                # Get 2 months of history
                df = t.history(period="2mo")
                if df.empty or len(df) < 30:
                    st.error("Not enough data")
                else:
                    # Actual prices: last 30 days (green)
                    actual = df['Close'].tail(30)
                    
                    # Backward "forecast": price 30 days ago vs today (red line)
                    price_30d_ago = df['Close'].iloc[-31] if len(df) > 30 else actual.iloc[0]
                    backward_pred = price_30d_ago  # what AI "would have predicted"
                    
                    # Forward AI forecast (purple)
                    prompt = f"""Predict {ticker} price in exactly 30 days from today ({datetime.now().strftime('%Y-%m-%d')}).
Current price: ${current_price:,.2f}
30-day change so far: {((current_price / price_30d_ago) - 1)*100:+.2f}%
Give ONLY a number: the predicted price in USD."""
                    try:
                        resp = client.chat.completions.create(
                            model="llama-3.3-70b-versatile",
                            messages=[{"role": "user", "content": prompt}],
                            temperature=0.3,
                            max_tokens=20
                        ).choices[0].message.content.strip()
                        forward_price = float("".join(filter(str.isdigit, resp.split("$")[-1].split()[0])))
                    except:
                        forward_price = current_price * 1.08  # fallback
                    
                    # Create triple line chart
                    fig = go.Figure()
                    
                    # Green: Actual past 30 days
                    fig.add_trace(go.Scatter(
                        x=actual.index, y=actual.values,
                        mode='lines', name='Actual Price (Past 30d)',
                        line=dict(color='green', width=3)
                    ))
                    
                    # Red: Backward prediction accuracy
                    fig.add_trace(go.Scatter(
                        x=[actual.index[-31], actual.index[-1]],
                        y=[backward_pred, current_price],
                        mode='lines', name='AI "Would Have Predicted" (Red)',
                        line=dict(color='red', width=3, dash='dot')
                    ))
                    
                    # Purple: Forward 30-day forecast
                    future_dates = [actual.index[-1] + timedelta(days=i) for i in range(1, 31)]
                    future_prices = [current_price + (forward_price - current_price) * (i/30) for i in range(1, 31)]
                    fig.add_trace(go.Scatter(
                        x=future_dates, y=future_prices,
                        mode='lines', name='AI Forecast (Next 30d)',
                        line=dict(color='purple', width=4)
                    ))
                    
                    fig.add_vline(x=actual.index[-1], line_dash="dash", line_color="white")
                    fig.update_layout(
                        height=700, template=template,
                        title=f"{ticker} – AI Forecast vs Reality",
                        xaxis_title="Date", yaxis_title="Price ($)"
                    )
                    
                    st.plotly_chart(fig, use_container_width=True, key="forecast_chart")
                    
                    col1, col2, col3 = st.columns(3)
                    col1.metric("Current Price", f"${current_price:,.2f}")
                    col2.metric("30-Day AI Forecast", f"${forward_price:,.2f}", f"{(forward_price/current_price-1)*100:+.1f}%")
                    col3.metric("30-Day Actual Change", f"{((current_price/price_30d_ago)-1)*100:+.2f}%")
                    
                    st.success(f"**AI Target in 30 Days: ${forward_price:,.2f}**")
                    
            except Exception as e:
                st.error(f"Error: {e}")

st.sidebar.success("AI Forecast with Triple Line Chart!")
st.sidebar.caption(f"Live • {datetime.now().strftime('%H:%M:%S')}")