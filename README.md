# Ollama Stock Analyzer + Compare + Q&A

A local Python + Streamlit app that uses Yahoo Finance data and a local Ollama model to analyze one stock, compare it with another stock, and answer follow-up questions.

## Run

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
streamlit run app.py
```

Make sure Ollama is running:

```bash
ollama serve
ollama pull llama3.1:8b
```

## Example symbols

- US: `AAPL`, `MSFT`, `NVDA`, `GOOGL`
- India: `RELIANCE.NS`, `TCS.NS`, `INFY.NS`, `HDFCBANK.NS`

## Features

- Primary stock analysis
- Optional comparison ticker
- Side-by-side metrics table
- Normalized performance chart
- AI-generated comparison analysis
- Chat Q&A with context from both stocks
- Markdown download

Education/research only. Not financial advice.
