import yfinance as yf
import pandas as pd

START_DATE = "1970-01-01"

def load_monthly_returns(tickers):
    if not tickers:
        return pd.DataFrame()
    
    data = {}
    for ticker in tickers:
        try:
            # 배당 포함 수익률을 위해 auto_adjust=True 유지 (원하시면 False로 변경 가능)
            raw = yf.download(ticker, start=START_DATE, auto_adjust=True)
            
            if raw.empty:
                continue
                
            # 최신 yfinance 버전의 멀티인덱스 대응
            if isinstance(raw.columns, pd.MultiIndex):
                price = raw["Close"][ticker]
            else:
                price = raw["Close"]
                
            data[ticker] = price
        except Exception as e:
            print(f"Error downloading {ticker}: {e}")

    if not data:
        return pd.DataFrame()

    df = pd.concat(data.values(), axis=1)
    df.columns = data.keys()
    
    # 모든 자산의 데이터가 존재하는 기간만 남김 (교집합)
    df = df.dropna()

    # 월말 기준 리샘플링 및 수익률 계산
    monthly_prices = df.resample("M").last()
    monthly_returns = monthly_prices.pct_change().dropna()

    return monthly_returns
