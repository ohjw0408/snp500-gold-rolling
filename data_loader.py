import yfinance as yf
import pandas as pd
import streamlit as st

START_DATE = "2005-01-01" # 검증하셨던 2005년부터 가져오도록 설정

def load_monthly_returns(tickers):
    if not tickers:
        return pd.DataFrame()

    combined_df = pd.DataFrame()

    for ticker in tickers:
        try:
            # 개별 자산 다운로드
            raw = yf.download(ticker, start=START_DATE, auto_adjust=True)
            
            if raw.empty:
                st.sidebar.warning(f"{ticker} 데이터를 찾을 수 없습니다.")
                continue

            # 종가 추출 (멀티인덱스 대응)
            if isinstance(raw.columns, pd.MultiIndex):
                price = raw["Close"][ticker]
            else:
                price = raw["Close"]
            
            # 개별 자산의 월말 종가로 먼저 변환
            monthly_price = price.resample("M").last()
            combined_df[ticker] = monthly_price
            
        except Exception as e:
            st.sidebar.error(f"{ticker} 로딩 실패: {e}")

    if combined_df.empty:
        return pd.DataFrame()

    # 🔥 핵심: 모든 자산이 '동시에' 존재하는 기간만 남김
    # 만약 비트코인이 2014년에 시작했다면, 전체 표가 2014년부터로 맞춰집니다.
    final_df = combined_df.dropna()

    # 수익률 계산
    monthly_returns = final_df.pct_change().dropna()

    return monthly_returns
