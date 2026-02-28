import yfinance as yf
import pandas as pd

def load_monthly_returns(tickers):
    if not tickers: return pd.DataFrame()
    data = {}
    
    # 1990년으로 시작일을 변경하여 SPY의 탄생(1993)부터 가져오게 합니다.
    for ticker in tickers:
        try:
            raw = yf.download(ticker, start="1990-01-01", auto_adjust=True)
            if not raw.empty:
                if isinstance(raw.columns, pd.MultiIndex):
                    data[ticker] = raw["Close"][ticker]
                else:
                    data[ticker] = raw["Close"]
        except: continue

    if not data: return pd.DataFrame()

    # 데이터를 합칩니다. (이때 데이터가 없는 기간은 NaN으로 남습니다)
    df = pd.concat(data.values(), axis=1)
    df.columns = data.keys()
    
    # 빈칸을 직전 값으로 채우되, 아예 데이터가 시작도 안 한 앞부분(NaN)은 둡니다.
    df = df.ffill()
    
    # 월말 종가로 리샘플링
    monthly_prices = df.resample("M").last()
    
    # 수익률 계산 (여기서 dropna를 하면 안 됩니다!)
    return monthly_prices.pct_change()
