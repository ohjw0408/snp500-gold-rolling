import yfinance as yf
import pandas as pd

START_DATE = "1970-01-01"

ASSETS = {
    "SP500": "SPY",   # ^SPY가 아니라 SPY입니다.
    "Gold": "GLD"
}

def load_monthly_returns():
    data = {}

    for name, ticker in ASSETS.items():
        # 엑셀과 맞추기 위해 auto_adjust=False로 설정 (배당 제외 순수 주가)
        raw = yf.download(ticker, start=START_DATE, auto_adjust=False)

        # Close는 일반 종가, Adj Close는 배당 포함 수정 종가입니다.
        # 엑셀 데이터가 배당 제외라면 'Close'를 사용하세요.
        if "Close" in raw.columns:
            price = raw["Close"]
        else:
            price = raw.iloc[:, 0] # 예외 처리

        data[name] = price

    df = pd.concat(data.values(), axis=1)
    df.columns = data.keys()
    
    # 2005년부터 보시려면 여기서 데이터를 잘라주면 검증이 더 쉽습니다.
    df = df[df.index >= "2005-01-01"]
    df = df.dropna()

    # 🔥 월말 기준 리샘플링
    monthly_prices = df.resample("M").last()

    # 월간 수익률 계산
    monthly_returns = monthly_prices.pct_change().dropna()

    return monthly_returns
