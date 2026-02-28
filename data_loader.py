import yfinance as yf
import pandas as pd

START_DATE = "1970-01-01"

def load_monthly_returns(tickers):
    if not tickers:
        return pd.DataFrame()

    data = {}

    for ticker in tickers:
        try:
            # auto_adjust=True로 배당 포함 수익률 반영
            raw = yf.download(ticker, start=START_DATE, auto_adjust=True)

            if raw.empty:
                continue

            # 구조에 상관없이 'Close' 컬럼 추출
            if 'Close' in raw.columns:
                temp_close = raw['Close']
                if isinstance(temp_close, pd.DataFrame):
                    price = temp_close[ticker]
                else:
                    price = temp_close
                
                data[ticker] = price
        except Exception as e:
            print(f"{ticker} 에러: {e}")

    if not data:
        return pd.DataFrame()

    # 모든 자산을 하나의 표로 합침
    df = pd.concat(data.values(), axis=1)
    df.columns = data.keys()
    
    # 🔥 핵심 수정: 비트코인(주말 거래)과 주식(평일 거래)의 날짜 차이 해결
    # 1. 주말/공휴일 등 비어있는 칸을 직전 영업일 가격으로 채움 (전진 채우기)
    df = df.ffill()
    
    # 2. 모든 자산이 상장되어 '함께' 존재하기 시작한 시점부터만 남김
    df = df.dropna()

    if df.empty:
        return pd.DataFrame()

    # 월말 기준 리샘플링 및 수익률 계산
    monthly_prices = df.resample("M").last()
    monthly_returns = monthly_prices.pct_change().dropna()

    return monthly_returns
