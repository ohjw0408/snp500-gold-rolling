import yfinance as yf
import pandas as pd

START_DATE = "1970-01-01"

# 이제 ASSETS 고정 변수는 필요 없습니다. (함수 내부에서 처리)

def load_monthly_returns(tickers): # tickers 리스트를 인자로 받습니다.
    if not tickers:
        return pd.DataFrame()

    data = {}

    for ticker in tickers:
        # 사용자가 입력한 티커로 데이터를 다운로드합니다.
        raw = yf.download(ticker, start=START_DATE, auto_adjust=True)

        if raw.empty:
            continue

        # 최신 yfinance 버전 대응
        if isinstance(raw.columns, pd.MultiIndex):
            price = raw["Close"][ticker]
        else:
            price = raw["Close"]

        data[ticker] = price

    if not data:
        return pd.DataFrame()

    df = pd.concat(data.values(), axis=1)
    df.columns = data.keys()
    df = df.dropna()

    # 🔥 월말 기준 리샘플링
    monthly_prices = df.resample("M").last()

    # 월간 수익률
    monthly_returns = monthly_prices.pct_change().dropna()

    return monthly_returns
