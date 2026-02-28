import yfinance as yf
import pandas as pd

START_DATE = "1970-01-01"

def load_monthly_returns(tickers):
    if not tickers:
        return pd.DataFrame()

    data = {}

    for ticker in tickers:
        try:
            # 데이터를 다운로드합니다.
            raw = yf.download(ticker, start=START_DATE, auto_adjust=True)

            if raw.empty:
                continue

            # 🛠 어떤 구조로 데이터가 오든 'Close' 컬럼만 안전하게 추출합니다.
            if 'Close' in raw.columns:
                # 데이터가 1차원인지 2차원인지 확인하여 처리
                temp_close = raw['Close']
                if isinstance(temp_close, pd.DataFrame):
                    # 멀티인덱스인 경우 해당 티커 컬럼 선택
                    price = temp_close[ticker]
                else:
                    price = temp_close
                
                data[ticker] = price
        except Exception as e:
            st.error(f"{ticker} 데이터를 가져오는 중 오류 발생: {e}")

    if not data:
        return pd.DataFrame()

    df = pd.concat(data.values(), axis=1)
    df.columns = data.keys()
    
    # 모든 자산의 데이터가 공통으로 존재하는 기간만 남김
    df = df.dropna()

    if df.empty:
        return pd.DataFrame()

    # 월말 기준 리샘플링 및 수익률 계산
    monthly_prices = df.resample("M").last()
    monthly_returns = monthly_prices.pct_change().dropna()

    return monthly_returns
