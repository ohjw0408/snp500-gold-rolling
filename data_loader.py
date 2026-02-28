import yfinance as yf
import pandas as pd

def load_monthly_returns(tickers):
    if not tickers: return pd.DataFrame()
    data = {}
    
    for ticker in tickers:
        try:
            # 2005년부터 데이터를 최대한 긁어옵니다.
            raw = yf.download(ticker, start="2005-01-01", auto_adjust=True)
            if not raw.empty:
                if isinstance(raw.columns, pd.MultiIndex):
                    data[ticker] = raw["Close"][ticker]
                else:
                    data[ticker] = raw["Close"]
        except: continue

    if not data: return pd.DataFrame()

    df = pd.concat(data.values(), axis=1)
    df.columns = data.keys()
    
    # 🔥 [중요] dropna()를 하지 않고 ffill만 해서 빈칸을 둡니다.
    # 비어있는 칸은 나중에 portfolio.py에서 알아서 제외하고 계산합니다.
    df = df.ffill()
    
    # 월말 종가로 변환
    monthly_prices = df.resample("M").last()
    return monthly_prices.pct_change() # 첫 줄 NaN은 나중에 처리됨
