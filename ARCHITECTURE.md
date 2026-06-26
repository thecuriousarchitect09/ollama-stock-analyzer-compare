# Architecture: Local AI Stock Analyzer + Compare + Q&A

> **Project:** Python + Streamlit + yfinance + Plotly + Ollama  
> **Purpose:** Analyze a stock, compare it with another stock, and answer follow-up questions using a local LLM.  
> **Note:** This project is for educational/research use only and is **not financial advice**.

---

## 1. High-Level Overview

This application is a **local AI-assisted stock analysis workbench**.

It allows a user to:

1. Enter a primary stock symbol.
2. Optionally enter a comparison stock symbol.
3. Fetch market data using `yfinance`.
4. Calculate technical indicators using `pandas`.
5. Render charts using `Plotly`.
6. Generate stock analysis using a local Ollama model.
7. Ask contextual follow-up questions.
8. Download the full report as Markdown.

The core architecture combines deterministic analytics with local LLM reasoning.

```text
User
 │
 ▼
Streamlit UI
 │
 ▼
Application Orchestration Layer
 │
 ├── Market Data Service: yfinance
 │
 ├── Technical Indicator Engine: pandas
 │
 ├── Visualization Layer: Plotly
 │
 ├── Prompt Builder
 │
 └── Local AI Layer: Ollama
 │
 ▼
Analysis + Comparison + Q&A + Markdown Export
```

---

## 2. Main Architecture Diagram

```text
┌─────────────────────────────────────────────┐
│                Streamlit UI                  │
│                                             │
│  - Primary stock input                       │
│  - Compare stock checkbox                    │
│  - Comparison stock input                    │
│  - Period / interval selection               │
│  - Risk profile / horizon                    │
│  - Analyze button                            │
│  - Chat input                                │
│  - Download report                           │
└──────────────────────┬──────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────┐
│         Application Orchestration Layer       │
│                                             │
│  - Validates input                           │
│  - Coordinates data fetching                 │
│  - Calculates indicators                     │
│  - Creates stock snapshots                   │
│  - Manages session state                     │
│  - Builds prompts                            │
│  - Handles errors                            │
└──────────────┬──────────────────┬───────────┘
               │                  │
               ▼                  ▼
┌──────────────────────┐   ┌──────────────────────┐
│   Market Data Layer   │   │ Technical Analytics   │
│                      │   │ Layer                │
│  yfinance             │   │                      │
│  - OHLCV data         │   │ pandas               │
│  - Company info       │   │ - SMA                │
│  - Valuation metrics  │   │ - EMA                │
│                      │   │ - RSI                │
│                      │   │ - MACD               │
└──────────┬───────────┘   └──────────┬───────────┘
           │                          │
           └──────────┬───────────────┘
                      ▼
┌─────────────────────────────────────────────┐
│              Stock Snapshot Layer            │
│                                             │
│  Compact JSON-style data context             │
│  - Symbol                                    │
│  - Company name                              │
│  - Sector / industry                         │
│  - Latest close                              │
│  - Period return                             │
│  - SMA / RSI / MACD                          │
│  - Market cap / P/E / P/B                    │
└──────────────────────┬──────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────┐
│              Prompt Builder Layer            │
│                                             │
│  - Single stock analysis prompt              │
│  - Comparison prompt                         │
│  - Follow-up Q&A prompt                      │
│  - Safety/caution instructions               │
└──────────────────────┬──────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────┐
│              Local AI Layer                  │
│                                             │
│  Ollama API                                  │
│  http://localhost:11434/api/generate         │
│                                             │
│  Local models such as:                       │
│  - llama3.1:8b                               │
│  - mistral                                   │
│  - qwen2.5:7b                                │
└──────────────────────┬──────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────┐
│              Output Layer                    │
│                                             │
│  - AI stock analysis                         │
│  - AI comparison analysis                    │
│  - Chat Q&A answers                          │
│  - Charts                                    │
│  - Markdown download                         │
└─────────────────────────────────────────────┘
```

---

## 3. Layered Architecture

The project can be understood as six logical layers.

```text
┌──────────────────────────────┐
│ 1. UI Layer                  │
├──────────────────────────────┤
│ 2. Application Layer         │
├──────────────────────────────┤
│ 3. Data Layer                │
├──────────────────────────────┤
│ 4. Analytics Layer           │
├──────────────────────────────┤
│ 5. AI Reasoning Layer        │
├──────────────────────────────┤
│ 6. Export Layer              │
└──────────────────────────────┘
```

---

## 4. UI Layer

The UI is built using **Streamlit**.

Responsibilities:

- Capture user inputs.
- Display metrics.
- Render charts.
- Show AI analysis.
- Provide chat-style Q&A.
- Provide download capability.

Main UI elements:

```python
primary_symbol = st.text_input("Primary stock symbol", value="AAPL")
enable_compare = st.checkbox("Compare with another stock", value=True)
compare_symbol = st.text_input("Comparison stock symbol", value="MSFT")
period = st.selectbox("Period", ["3mo", "6mo", "1y", "2y", "5y"])
interval = st.selectbox("Interval", ["1d", "1wk", "1mo"])
model = st.text_input("Ollama model", value=OLLAMA_MODEL)
risk_profile = st.selectbox("Risk profile", ["Conservative", "Moderate", "Aggressive"])
horizon = st.selectbox("Investment horizon", ["Short term", "Medium term", "Long term"])
```

The UI is intentionally simple and demo-friendly.

---

## 5. Data Layer

The data layer uses `yfinance` to fetch stock data.

```python
def fetch_stock_data(symbol: str, period: str, interval: str):
    ticker = yf.Ticker(symbol)
    hist = ticker.history(period=period, interval=interval, auto_adjust=False)
    info = ticker.info or {}
    return hist, info
```

It returns:

- Historical price data.
- Company metadata.
- Basic valuation metrics.

Typical historical fields:

- Open
- High
- Low
- Close
- Volume
- Dividends
- Stock splits

Typical company info fields:

- Company name
- Sector
- Industry
- Market capitalization
- Trailing P/E
- Forward P/E
- Price-to-book
- Dividend yield
- 52-week high
- 52-week low

---

## 6. Technical Analytics Layer

The technical analytics layer uses `pandas` to calculate indicators.

```python
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
```

Indicators calculated:

| Indicator | Purpose |
|---|---|
| SMA 20 | Short-term trend |
| SMA 50 | Medium-term trend |
| EMA 12 | Short-term exponential average |
| EMA 26 | Longer exponential average |
| MACD | Momentum comparison between EMA 12 and EMA 26 |
| MACD Signal | Smoothed MACD signal line |
| RSI 14 | Overbought/oversold momentum indicator |

This layer is deterministic and does not use AI.

---

## 7. Snapshot Layer

The snapshot layer converts raw data and indicators into a compact context object.

Example snapshot:

```json
{
  "symbol": "AAPL",
  "company_name": "Apple Inc.",
  "sector": "Technology",
  "industry": "Consumer Electronics",
  "currency": "USD",
  "latest_close": 195.64,
  "period_return_percent": 12.5,
  "sma_20": 192.1,
  "sma_50": 188.4,
  "rsi_14": 61.2,
  "macd": 1.024,
  "macd_signal": 0.812,
  "market_cap": 3000000000000,
  "trailing_pe": 29.4,
  "forward_pe": 26.7,
  "price_to_book": 45.1,
  "dividend_yield": 0.005,
  "fifty_two_week_high": 210.0,
  "fifty_two_week_low": 165.0
}
```

Why this layer matters:

- Reduces raw data size.
- Gives Ollama clean structured context.
- Improves response consistency.
- Makes Q&A easier.
- Makes report export simple.

---

## 8. Comparison Architecture

When comparison is enabled, the app performs the same pipeline for a second ticker.

```text
Primary Symbol                      Comparison Symbol
     │                                      │
     ▼                                      ▼
Fetch Data                            Fetch Data
     │                                      │
     ▼                                      ▼
Calculate Indicators                  Calculate Indicators
     │                                      │
     ▼                                      ▼
Create Snapshot                       Create Snapshot
     │                                      │
     └──────────────┬───────────────────────┘
                    ▼
          Comparison Prompt Builder
                    │
                    ▼
              Ollama Analysis
```

The comparison view includes:

- Side-by-side metrics table.
- Normalized performance chart.
- AI comparison analysis.
- Follow-up Q&A using both contexts.

---

## 9. Normalized Performance Chart

The app normalizes both stock prices to `100` at the beginning of the selected period.

This avoids misleading comparisons caused by different absolute stock prices.

Example:

```text
Day 1:
AAPL = 100
MSFT = 100

Later:
AAPL = 116
MSFT = 108
```

Interpretation:

- AAPL gained around 16%.
- MSFT gained around 8%.
- AAPL outperformed over the selected period.

Implementation concept:

```python
common = pd.concat([primary_close, compare_close], axis=1, join="inner")
normalized = common / common.iloc[0] * 100
```

---

## 10. AI Layer: Ollama Integration

The AI layer calls a local Ollama endpoint.

```python
def call_ollama(prompt: str, model: str):
    url = f"{OLLAMA_BASE_URL.rstrip('/')}/api/generate"
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.2,
            "top_p": 0.9
        }
    }
    response = requests.post(url, json=payload, timeout=180)
    response.raise_for_status()
    return response.json().get("response", "")
```

Default endpoint:

```text
http://localhost:11434/api/generate
```

Environment variables:

```env
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1:8b
```

Benefits of local Ollama usage:

- Runs locally.
- No external LLM API key required.
- Better privacy for user queries.
- Easy model switching.
- Useful for offline/local demos once model is available.

---

## 11. Prompt Types

The app has three major prompt types.

### 11.1 Single Stock Analysis Prompt

Used for primary stock analysis.

Includes:

- Primary stock snapshot.
- Risk profile.
- Investment horizon.
- Additional user context.

Output requested:

1. Executive summary
2. Price trend and momentum
3. Technical indicator interpretation
4. Valuation snapshot
5. Key risks and unknowns
6. Bull case
7. Bear case
8. Watchlist triggers
9. Final educational view

---

### 11.2 Comparison Prompt

Used when comparing two stocks.

Includes:

- Primary stock snapshot.
- Comparison stock snapshot.
- Risk profile.
- Investment horizon.
- Additional context.

Output requested:

1. Quick comparison summary
2. Relative momentum comparison
3. Relative valuation comparison
4. Quality of available data and missing data
5. Stronger technical setup
6. Relative valuation view
7. Key risks for each stock
8. Watchlist triggers for each stock
9. Final educational view

---

### 11.3 Q&A Prompt

Used for follow-up user questions.

Includes:

- Primary snapshot.
- Comparison snapshot if available.
- Recent primary indicator rows.
- Recent comparison indicator rows.
- Prior primary analysis.
- Prior comparison analysis.
- Recent Q&A history.
- Latest user question.

This enables contextual questions such as:

```text
Which has stronger momentum?
```

```text
Which stock looks more expensive?
```

```text
Compare RSI and MACD for both.
```

```text
What should I watch before deciding between these two?
```

---

## 12. Session State Architecture

Streamlit reruns the script after interactions. To retain context, the app uses `st.session_state`.

Session state keys:

```python
st.session_state.primary_snapshot
st.session_state.compare_snapshot
st.session_state.analysis
st.session_state.comparison_analysis
st.session_state.messages
st.session_state.primary_tail
st.session_state.compare_tail
st.session_state.primary_data
st.session_state.compare_data
```

Purpose:

| State Key | Purpose |
|---|---|
| `primary_snapshot` | Stores summarized primary stock data |
| `compare_snapshot` | Stores summarized comparison stock data |
| `analysis` | Stores primary AI analysis |
| `comparison_analysis` | Stores AI comparison output |
| `messages` | Stores Q&A chat history |
| `primary_tail` | Stores recent primary indicator rows as CSV text |
| `compare_tail` | Stores recent comparison indicator rows as CSV text |
| `primary_data` | Stores primary DataFrame for charting |
| `compare_data` | Stores comparison DataFrame for charting |

Without session state:

- Chat history would be lost.
- Charts may reset unexpectedly.
- Q&A would not know prior analysis.
- Report download would not include the full context.

---

## 13. End-to-End Runtime Flow

```text
1. User opens Streamlit app.
2. User enters primary stock symbol.
3. User optionally enables comparison.
4. User enters comparison stock symbol.
5. User selects period, interval, model, risk profile, and horizon.
6. User clicks Analyze.
7. App validates symbols.
8. App fetches primary stock data using yfinance.
9. App calculates indicators for primary stock.
10. App creates primary snapshot.
11. App sends primary snapshot to Ollama.
12. Ollama returns primary stock analysis.
13. If comparison is enabled:
    a. App fetches comparison stock data.
    b. App calculates indicators for comparison stock.
    c. App creates comparison snapshot.
    d. App sends both snapshots to Ollama.
    e. Ollama returns comparison analysis.
14. App renders metrics, charts, and AI analysis.
15. User asks follow-up question.
16. App builds Q&A prompt with all available context.
17. Ollama returns contextual answer.
18. App stores Q&A in session state.
19. User downloads full Markdown report.
```

---

## 14. File-Level Architecture

Current project structure:

```text
ollama_stock_analyzer_compare/
├── app.py
├── requirements.txt
├── README.md
├── .env.example
└── run.sh
```

### 14.1 `app.py`

Main application file.

Responsibilities:

- Streamlit UI definition.
- Market data fetching.
- Indicator calculation.
- Snapshot creation.
- Chart rendering.
- Prompt construction.
- Ollama calls.
- Q&A handling.
- Markdown download generation.

### 14.2 `requirements.txt`

Dependencies:

```text
streamlit
yfinance
pandas
plotly
requests
python-dotenv
```

### 14.3 `.env.example`

Configuration template:

```env
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1:8b
```

### 14.4 `run.sh`

Convenience script:

```bash
#!/usr/bin/env bash
set -e
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
if [ ! -f .env ]; then cp .env.example .env; fi
streamlit run app.py
```

---

## 15. Current Strengths

- Simple local-first architecture.
- No external LLM API dependency.
- Easy to run on Mac.
- Supports US and Indian stock symbols.
- Good for demos and prototypes.
- Provides summary, comparison, and Q&A.
- Uses deterministic indicators plus LLM reasoning.
- Markdown export makes outputs reusable.
- Easy to extend into a larger agentic finance platform.

---

## 16. Current Limitations

| Limitation | Explanation |
|---|---|
| Single-file app | Most logic is currently inside `app.py` |
| No persistent database | Session data is lost after app restart |
| Data source dependency | Relies on Yahoo Finance data through `yfinance` |
| Delayed/incomplete data | Market data may not be real time |
| Limited fundamentals | Uses only basic `ticker.info` fields |
| LLM hallucination risk | Prompting reduces risk but cannot fully eliminate it |
| No authentication | Suitable for local prototype, not production |
| Two-stock comparison only | Current version compares primary stock with one other stock |
| No advanced risk model | Does not calculate beta, volatility, drawdown, Sharpe ratio, etc. |

---

## 17. Recommended Modular Architecture

For a cleaner production-style structure, split the project into modules.

```text
ollama_stock_analyzer/
├── app.py
├── config.py
├── requirements.txt
├── .env.example
├── README.md
│
├── services/
│   ├── market_data_service.py
│   ├── indicator_service.py
│   ├── ollama_service.py
│   └── report_service.py
│
├── prompts/
│   ├── stock_analysis_prompt.py
│   ├── comparison_prompt.py
│   └── qa_prompt.py
│
├── ui/
│   ├── sidebar.py
│   ├── charts.py
│   └── layout.py
│
├── models/
│   └── stock_snapshot.py
│
└── utils/
    ├── formatting.py
    └── validation.py
```

Benefits:

- Easier testing.
- Easier maintenance.
- Clear separation of responsibilities.
- Easier to add new data sources.
- Easier to add portfolio analysis.
- Easier to migrate from Streamlit to FastAPI/React later.

---

## 18. Future Enhancement Ideas

### 18.1 Multi-Stock Comparison

Allow users to compare 3–5 stocks at once.

Example:

```text
AAPL vs MSFT vs NVDA vs GOOGL
```

---

### 18.2 Portfolio Analyzer

Allow users to enter:

- Stock symbol
- Quantity
- Average buy price
- Current allocation

Then calculate:

- Portfolio value
- Gain/loss
- Sector exposure
- Concentration risk
- AI portfolio commentary

---

### 18.3 Fundamental Analysis

Add deeper financial metrics:

- Revenue growth
- Net income growth
- Free cash flow
- Debt-to-equity
- ROE
- ROIC
- Operating margin
- Net margin

---

### 18.4 Risk Analytics

Add quantitative risk metrics:

- Volatility
- Maximum drawdown
- Beta
- Sharpe ratio
- Sortino ratio
- Correlation between stocks

---

### 18.5 News and Sentiment

Add an optional news layer:

```text
Stock symbol
   ↓
Fetch recent news
   ↓
Summarize articles
   ↓
Classify sentiment
   ↓
Include in AI analysis
```

---

### 18.6 RAG with Annual Reports

Allow users to upload:

- Annual reports
- Earnings call transcripts
- Investor presentations

Then use local retrieval to answer questions from company documents.

---

### 18.7 Agentic Workflow

A future agentic version could decide which tools to call.

```text
User question
   ↓
Planner agent
   ↓
Tool selection
   ├── Fetch market data
   ├── Calculate indicators
   ├── Fetch fundamentals
   ├── Compare peers
   ├── Retrieve documents
   └── Generate report
   ↓
Final answer
```

---

## 19. Security and Privacy Considerations

Since the LLM runs locally through Ollama:

- User questions are not sent to a cloud LLM.
- Stock snapshots remain local.
- No external LLM API key is needed.

However:

- `yfinance` still fetches data from the internet.
- The app has no authentication.
- The app is intended for local use.
- Do not expose it publicly without adding auth, rate limiting, validation, and hardening.

---

## 20. Summary

The project follows this architecture:

```text
Streamlit UI
   +
yfinance market data
   +
pandas indicator calculations
   +
Plotly visualization
   +
Ollama local LLM reasoning
   +
Session-based Q&A
   +
Markdown export
```

It is currently a strong local prototype for AI-assisted stock research.

The next best architectural step is to split the single `app.py` into services, prompts, UI components, models, and utilities.
