import os
import json
import requests
import pandas as pd
import yfinance as yf
import streamlit as st
import plotly.graph_objects as go
from dotenv import load_dotenv

load_dotenv()
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1:8b")

st.set_page_config(page_title="Local AI Stock Analyzer Compare", page_icon="📈", layout="wide")

DISCLAIMER = """
This application is for educational and research purposes only. It is not financial advice.
Market data may be delayed, incomplete, or inaccurate. Please consult a qualified financial advisor before making investment decisions.
"""

DEFAULT_STATE = {
    "primary_snapshot": None,
    "compare_snapshot": None,
    "analysis": None,
    "comparison_analysis": None,
    "messages": [],
    "primary_tail": None,
    "compare_tail": None,
    "primary_data": None,
    "compare_data": None,
}
for key, value in DEFAULT_STATE.items():
    if key not in st.session_state:
        st.session_state[key] = value


def fetch_stock_data(symbol: str, period: str, interval: str):
    ticker = yf.Ticker(symbol)
    hist = ticker.history(period=period, interval=interval, auto_adjust=False)
    info = ticker.info or {}
    return hist, info


def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    data = df.copy()
    data["SMA_20"] = data["Close"].rolling(window=20).mean()
    data["SMA_50"] = data["Close"].rolling(window=50).mean()
    data["EMA_12"] = data["Close"].ewm(span=12, adjust=False).mean()
    data["EMA_26"] = data["Close"].ewm(span=26, adjust=False).mean()
    data["MACD"] = data["EMA_12"] - data["EMA_26"]
    data["MACD_SIGNAL"] = data["MACD"].ewm(span=9, adjust=False).mean()
    delta = data["Close"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(window=14).mean()
    avg_loss = loss.rolling(window=14).mean()
    rs = avg_gain / avg_loss
    data["RSI_14"] = 100 - (100 / (1 + rs))
    return data


def safe_value(info: dict, key: str, default="N/A"):
    value = info.get(key, default)
    return default if value is None else value


def fmt_number(value):
    if value in [None, "N/A"]:
        return "N/A"
    try:
        value = float(value)
        if abs(value) >= 1_000_000_000_000:
            return f"{value/1_000_000_000_000:.2f}T"
        if abs(value) >= 1_000_000_000:
            return f"{value/1_000_000_000:.2f}B"
        if abs(value) >= 1_000_000:
            return f"{value/1_000_000:.2f}M"
        return round(value, 2)
    except Exception:
        return value


def create_snapshot(symbol: str, data: pd.DataFrame, info: dict) -> dict:
    latest = data.dropna().iloc[-1]
    first_close = data["Close"].dropna().iloc[0]
    latest_close = latest["Close"]
    period_return = ((latest_close - first_close) / first_close) * 100 if first_close else 0
    return {
        "symbol": symbol,
        "company_name": safe_value(info, "longName"),
        "sector": safe_value(info, "sector"),
        "industry": safe_value(info, "industry"),
        "currency": safe_value(info, "currency"),
        "latest_close": round(float(latest_close), 2),
        "period_return_percent": round(float(period_return), 2),
        "sma_20": round(float(latest.get("SMA_20", 0)), 2) if pd.notna(latest.get("SMA_20")) else "N/A",
        "sma_50": round(float(latest.get("SMA_50", 0)), 2) if pd.notna(latest.get("SMA_50")) else "N/A",
        "rsi_14": round(float(latest.get("RSI_14", 0)), 2) if pd.notna(latest.get("RSI_14")) else "N/A",
        "macd": round(float(latest.get("MACD", 0)), 4) if pd.notna(latest.get("MACD")) else "N/A",
        "macd_signal": round(float(latest.get("MACD_SIGNAL", 0)), 4) if pd.notna(latest.get("MACD_SIGNAL")) else "N/A",
        "market_cap": safe_value(info, "marketCap"),
        "trailing_pe": safe_value(info, "trailingPE"),
        "forward_pe": safe_value(info, "forwardPE"),
        "price_to_book": safe_value(info, "priceToBook"),
        "dividend_yield": safe_value(info, "dividendYield"),
        "fifty_two_week_high": safe_value(info, "fiftyTwoWeekHigh"),
        "fifty_two_week_low": safe_value(info, "fiftyTwoWeekLow"),
    }


def build_price_chart(data: pd.DataFrame, symbol: str):
    fig = go.Figure()
    fig.add_trace(go.Candlestick(x=data.index, open=data["Open"], high=data["High"], low=data["Low"], close=data["Close"], name="Price"))
    fig.add_trace(go.Scatter(x=data.index, y=data["SMA_20"], mode="lines", name="SMA 20"))
    fig.add_trace(go.Scatter(x=data.index, y=data["SMA_50"], mode="lines", name="SMA 50"))
    fig.update_layout(title=f"{symbol} Price Chart", xaxis_title="Date", yaxis_title="Price", xaxis_rangeslider_visible=False, height=500)
    return fig


def build_compare_normalized_chart(primary_data, primary_symbol, compare_data, compare_symbol):
    p = primary_data["Close"].dropna()
    c = compare_data["Close"].dropna()
    common = pd.concat([p, c], axis=1, join="inner")
    common.columns = [primary_symbol, compare_symbol]
    normalized = common / common.iloc[0] * 100
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=normalized.index, y=normalized[primary_symbol], mode="lines", name=primary_symbol))
    fig.add_trace(go.Scatter(x=normalized.index, y=normalized[compare_symbol], mode="lines", name=compare_symbol))
    fig.update_layout(title="Normalized Performance Comparison", xaxis_title="Date", yaxis_title="Indexed to 100", height=430)
    return fig


def build_comparison_table(primary_snapshot, compare_snapshot):
    rows = [
        ("Company", "company_name"),
        ("Sector", "sector"),
        ("Industry", "industry"),
        ("Currency", "currency"),
        ("Latest Close", "latest_close"),
        ("Period Return %", "period_return_percent"),
        ("SMA 20", "sma_20"),
        ("SMA 50", "sma_50"),
        ("RSI 14", "rsi_14"),
        ("MACD", "macd"),
        ("MACD Signal", "macd_signal"),
        ("Market Cap", "market_cap"),
        ("Trailing P/E", "trailing_pe"),
        ("Forward P/E", "forward_pe"),
        ("Price to Book", "price_to_book"),
        ("Dividend Yield", "dividend_yield"),
        ("52W High", "fifty_two_week_high"),
        ("52W Low", "fifty_two_week_low"),
    ]
    return pd.DataFrame({
        "Metric": [r[0] for r in rows],
        primary_snapshot["symbol"]: [fmt_number(primary_snapshot.get(r[1])) for r in rows],
        compare_snapshot["symbol"]: [fmt_number(compare_snapshot.get(r[1])) for r in rows],
    })


def call_ollama(prompt: str, model: str):
    url = f"{OLLAMA_BASE_URL.rstrip('/')}/api/generate"
    payload = {"model": model, "prompt": prompt, "stream": False, "options": {"temperature": 0.2, "top_p": 0.9}}
    response = requests.post(url, json=payload, timeout=180)
    response.raise_for_status()
    return response.json().get("response", "")


def build_analysis_prompt(snapshot, risk_profile, horizon, extra_context):
    return f"""
You are a cautious equity research assistant. Analyze this stock using only the provided data.
Do not invent facts. If data is missing, say so clearly. This is not financial advice.

User risk profile: {risk_profile}
Investment horizon: {horizon}
Additional user context: {extra_context or 'None'}

Stock data snapshot JSON:
{json.dumps(snapshot, indent=2)}

Return:
1. Executive summary
2. Price trend and momentum
3. Technical indicator interpretation
4. Valuation snapshot
5. Key risks and unknowns
6. Bull case
7. Bear case
8. Watchlist triggers
9. Final educational view: avoid direct buy/sell commands.
"""


def build_compare_prompt(primary_snapshot, compare_snapshot, risk_profile, horizon, extra_context):
    return f"""
You are a cautious equity research assistant. Compare these two stocks using only the provided snapshots.
Do not invent facts. If data is missing, call it out. This is not financial advice.

User risk profile: {risk_profile}
Investment horizon: {horizon}
Additional user context: {extra_context or 'None'}

Primary stock snapshot:
{json.dumps(primary_snapshot, indent=2)}

Comparison stock snapshot:
{json.dumps(compare_snapshot, indent=2)}

Return:
1. Quick comparison summary
2. Relative momentum comparison
3. Relative valuation comparison
4. Quality of available data and missing data
5. Which appears stronger on technicals, and why
6. Which appears more expensive/cheaper based on available valuation metrics
7. Key risks for each
8. Watchlist triggers for each
9. Final educational view with no direct buy/sell recommendation.
"""


def build_question_prompt(question: str):
    primary_snapshot = st.session_state.primary_snapshot or {}
    compare_snapshot = st.session_state.compare_snapshot or {}
    analysis = st.session_state.analysis or "No single-stock analysis available."
    comparison_analysis = st.session_state.comparison_analysis or "No comparison analysis available."
    conversation = "\n".join([f"User: {m['user']}\nAssistant: {m['assistant']}" for m in st.session_state.messages[-5:]])
    return f"""
You are a cautious stock analysis assistant. Answer the user's question using only the included stock context.
If the answer cannot be determined from this data, say what is missing.
Do not provide direct buy/sell instructions. Use educational language.

Primary stock snapshot:
{json.dumps(primary_snapshot, indent=2)}

Comparison stock snapshot, if available:
{json.dumps(compare_snapshot, indent=2)}

Primary recent rows:
{st.session_state.primary_tail or 'Not available'}

Comparison recent rows:
{st.session_state.compare_tail or 'Not available'}

Prior primary analysis:
{analysis}

Prior comparison analysis:
{comparison_analysis}

Recent Q&A conversation:
{conversation or 'None'}

User question:
{question}

Answer clearly with:
- Short answer
- Evidence from data
- Risks/limitations
- Suggested watch items
"""


def process_symbol(symbol, period, interval):
    data, info = fetch_stock_data(symbol, period, interval)
    if data.empty:
        raise ValueError(f"No market data found for {symbol}")
    data = add_indicators(data)
    snapshot = create_snapshot(symbol, data, info)
    tail = data[["Open", "High", "Low", "Close", "Volume", "SMA_20", "SMA_50", "RSI_14", "MACD", "MACD_SIGNAL"]].tail(20).round(4).to_csv()
    return data, snapshot, tail

st.title("📈 Local AI Stock Analyzer + Compare + Q&A")
st.caption("Python + Streamlit + yfinance + local Ollama model")
st.warning(DISCLAIMER)

with st.sidebar:
    st.header("Configuration")
    primary_symbol = st.text_input("Primary stock symbol", value="AAPL", help="Examples: AAPL, MSFT, RELIANCE.NS, TCS.NS")
    enable_compare = st.checkbox("Compare with another stock", value=True)
    compare_symbol = st.text_input("Comparison stock symbol", value="MSFT", disabled=not enable_compare)
    period = st.selectbox("Period", ["3mo", "6mo", "1y", "2y", "5y"], index=2)
    interval = st.selectbox("Interval", ["1d", "1wk", "1mo"], index=0)
    model = st.text_input("Ollama model", value=OLLAMA_MODEL)
    risk_profile = st.selectbox("Risk profile", ["Conservative", "Moderate", "Aggressive"], index=1)
    horizon = st.selectbox("Investment horizon", ["Short term", "Medium term", "Long term"], index=1)
    extra_context = st.text_area("Extra context", placeholder="Example: compare momentum, focus on valuation, long-term portfolio fit...")
    analyze_button = st.button("Analyze", type="primary")
    if st.button("Clear Q&A chat"):
        st.session_state.messages = []

if analyze_button:
    try:
        p_symbol = primary_symbol.strip().upper()
        c_symbol = compare_symbol.strip().upper()
        if enable_compare and p_symbol == c_symbol:
            st.error("Please enter a different comparison stock symbol.")
            st.stop()

        with st.spinner("Fetching primary stock data..."):
            p_data, p_snapshot, p_tail = process_symbol(p_symbol, period, interval)
        st.session_state.primary_data = p_data
        st.session_state.primary_snapshot = p_snapshot
        st.session_state.primary_tail = p_tail
        st.session_state.compare_data = None
        st.session_state.compare_snapshot = None
        st.session_state.compare_tail = None
        st.session_state.comparison_analysis = None
        st.session_state.messages = []

        with st.spinner("Generating primary AI analysis using local Ollama..."):
            st.session_state.analysis = call_ollama(build_analysis_prompt(p_snapshot, risk_profile, horizon, extra_context), model)

        if enable_compare and c_symbol:
            with st.spinner("Fetching comparison stock data..."):
                c_data, c_snapshot, c_tail = process_symbol(c_symbol, period, interval)
            st.session_state.compare_data = c_data
            st.session_state.compare_snapshot = c_snapshot
            st.session_state.compare_tail = c_tail
            with st.spinner("Generating comparison analysis using local Ollama..."):
                st.session_state.comparison_analysis = call_ollama(build_compare_prompt(p_snapshot, c_snapshot, risk_profile, horizon, extra_context), model)
    except requests.exceptions.ConnectionError:
        st.error("Could not connect to Ollama. Make sure Ollama is running: `ollama serve`")
    except Exception as e:
        st.exception(e)

if st.session_state.primary_snapshot:
    p = st.session_state.primary_snapshot
    st.subheader(f"Primary Stock: {p['symbol']}")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Latest Close", p["latest_close"])
    col2.metric("Period Return", f'{p["period_return_percent"]}%')
    col3.metric("RSI 14", p["rsi_14"])
    col4.metric("Trailing P/E", p["trailing_pe"])

    if st.session_state.compare_snapshot:
        c = st.session_state.compare_snapshot
        st.subheader(f"Comparison: {p['symbol']} vs {c['symbol']}")
        st.dataframe(build_comparison_table(p, c), use_container_width=True, hide_index=True)
        st.plotly_chart(build_compare_normalized_chart(st.session_state.primary_data, p["symbol"], st.session_state.compare_data, c["symbol"]), use_container_width=True)
        st.subheader("AI Comparison Analysis")
        st.markdown(st.session_state.comparison_analysis)

    tab1, tab2 = st.tabs(["Primary Chart & Analysis", "Raw Snapshots"])
    with tab1:
        st.plotly_chart(build_price_chart(st.session_state.primary_data, p["symbol"]), use_container_width=True)
        st.subheader("Primary AI Analysis")
        st.markdown(st.session_state.analysis)
    with tab2:
        st.write("Primary snapshot")
        st.json(st.session_state.primary_snapshot)
        if st.session_state.compare_snapshot:
            st.write("Comparison snapshot")
            st.json(st.session_state.compare_snapshot)

    st.divider()
    st.subheader("Ask follow-up questions")
    st.caption("You can now ask questions about the primary stock or compare both stocks.")
    for msg in st.session_state.messages:
        with st.chat_message("user"):
            st.markdown(msg["user"])
        with st.chat_message("assistant"):
            st.markdown(msg["assistant"])

    question = st.chat_input("Example: Which has stronger momentum? Which looks more expensive? What should I watch?")
    if question:
        with st.chat_message("user"):
            st.markdown(question)
        try:
            with st.spinner("Thinking locally with Ollama..."):
                answer = call_ollama(build_question_prompt(question), model)
            st.session_state.messages.append({"user": question, "assistant": answer})
            with st.chat_message("assistant"):
                st.markdown(answer)
        except requests.exceptions.ConnectionError:
            st.error("Could not connect to Ollama. Make sure Ollama is running: `ollama serve`")
        except Exception as e:
            st.exception(e)

    export = f"# Stock Analysis: {p['symbol']}\n\n## Disclaimer\n{DISCLAIMER}\n\n## Primary Snapshot\n```json\n{json.dumps(st.session_state.primary_snapshot, indent=2)}\n```\n\n## Primary Analysis\n{st.session_state.analysis}\n"
    if st.session_state.compare_snapshot:
        export += f"\n## Comparison Snapshot\n```json\n{json.dumps(st.session_state.compare_snapshot, indent=2)}\n```\n\n## Comparison Analysis\n{st.session_state.comparison_analysis}\n"
    export += "\n## Q&A\n"
    for m in st.session_state.messages:
        export += f"\n### Q: {m['user']}\n\n{m['assistant']}\n"
    file_suffix = f"{p['symbol']}_analysis"
    if st.session_state.compare_snapshot:
        file_suffix += f"_vs_{st.session_state.compare_snapshot['symbol']}"
    st.download_button("Download analysis + comparison + Q&A", export, file_name=f"{file_suffix}.md", mime="text/markdown")
else:
    st.info("Enter a primary stock, optionally enable comparison, then click **Analyze**.")
