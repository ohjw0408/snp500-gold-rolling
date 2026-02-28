import yfinance as yf
import pandas as pd

START_DATE = "1970-01-01"

def load_monthly_returns(tickers):
    if not tickers:
        return pd.DataFrame()

    data = {}

    for ticker in tickers:
        try:
            # 배당/권리락이 반영된 수정종가를 가져옵니다.
            raw = yf.download(ticker, start=START_DATE, auto_adjust=True)

            if raw.empty:
                continue

            # 데이터 구조(Single/Multi Index)에 상관없이 Close 가격만 추출
            if 'Close' in raw.columns:
                temp_close = raw['Close']
                if isinstance(temp_close, pd.DataFrame):
                    price = temp_close[ticker]
                else:
                    price = temp_close
                
                data[ticker] = price
        except Exception as e:
            print(f"{ticker} 다운로드 중 에러: {e}")

    if not data:
        return pd.DataFrame()

    # 1. 여러 자산 데이터를 하나로 합칩니다.
    df = pd.concat(data.values(), axis=1)
    df.columns = data.keys()
    
    # 🛠 [핵심 수정] 주말/공휴일 때문에 비어있는 칸을 직전 영업일 가격으로 채웁니다.
    # 이 과정을 거쳐야 비트코인(365일)과 주식(평일)의 날짜가 맞물립니다.
    df = df.ffill() 
    
    # 2. 모든 자산이 상장되어 '공통적으로' 데이터가 존재하는 시점부터 시작합니다.
    df = df.dropna()

    if df.empty or len(df) < 2:
        return pd.DataFrame()

    # 3. 월말 종가로 변환합니다.
    monthly_prices = df.resample("M").last()
    
    # 4. 월간 수익률 계산
    monthly_returns = monthly_prices.pct_change().dropna()

    return monthly_returns
