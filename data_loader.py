import yfinance as yf
import pandas as pd

START_DATE = "1970-01-01"

ASSETS = {
    "SP500": "^SP500TR",   # S&P500 Total Return Index
    "Gold": "GLD"          # SPDR Gold ETF (현물 기반)
}

def load_monthly_returns():
    data = {}

    for name, ticker in ASSETS.items():
        raw = yf.download(ticker, start=START_DATE, auto_adjust=True)

        if isinstance(raw.columns, pd.MultiIndex):
            price = raw["Close"]
        else:
            price = raw["Close"]

        data[name] = price

    df = pd.concat(data.values(), axis=1)
    df.columns = data.keys()
    df = df.dropna()

    # 🔥 월말 기준 리샘플링
    monthly_prices = df.resample("M").last()

    # 월간 수익률
    monthly_returns = monthly_prices.pct_change().dropna()

    return monthly_returns
