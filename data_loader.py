import yfinance as yf
import pandas as pd

def load_monthly_returns(tickers):
    if not tickers: return pd.DataFrame()
    data = {}
    
    # 시작일을 1900년으로 설정하여 지수(Index)의 전체 역사를 가져옵니다.
    for ticker in tickers:
        try:
            raw = yf.download(ticker, start="1900-01-01", auto_adjust=True)
            if not raw.empty:
                # 지수 데이터는 보통 'Close' 컬럼에 들어있습니다.
                if isinstance(raw.columns, pd.MultiIndex):
                    data[ticker] = raw["Close"][ticker]
                else:
                    data[ticker] = raw["Close"]
        except Exception as e:
            print(f"{ticker} 에러: {e}")
            continue

    if not data: return pd.DataFrame()

    df = pd.concat(data.values(), axis=1)
    df.columns = data.keys()
    
    # 앞부분 빈칸(상장 전)은 그대로 두고, 중간 공휴일 빈칸만 채웁니다.
    df = df.ffill()
    
    # 월말 종가 리샘플링 및 수익률 계산
    monthly_prices = df.resample("M").last()
    return monthly_prices.pct_change()
