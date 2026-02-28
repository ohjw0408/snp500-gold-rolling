import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
from datetime import datetime
from data_loader import load_monthly_returns
from portfolio import backtest
from metrics import calculate_cagr, calculate_mdd

st.set_page_config(page_title="Custom Asset Analyzer", layout="wide")
st.title("🚀 내 맘대로 자산배분 테스터")

with st.sidebar:
    st.header("1. 자산 설정")
    ticker_input = st.text_input("티커 입력", "^GSPC, ^IXIC, GC=F, BTC-USD")
    tickers = [t.strip().upper() for t in ticker_input.split(",") if t.strip()]

    st.header("2. 비중 설정")
    weights = {}
    if tickers:
        n = len(tickers)
        for t in tickers:
            # 슬라이더가 여기 있습니다!
            w_percent = st.slider(f"{t} 비중 (%)", 0, 100, 100 // n, key=f"v_{t}")
            weights[t] = w_percent / 100
    
    total_w = sum(weights.values())
    
    st.header("3. 기간 설정")
    # 에러 방지를 위해 number_input 사용
    sy = st.number_input("시작 연도", 1900, 2026, 1990)
    ey = st.number_input("종료 연도", 1900, 2026, 2026)
    
    # 롤링 기간 슬라이더
    years = st.slider("롤링 기간 (년)", 1, 20, 5, key="roll_v")
    rebalance_option = st.selectbox("리밸런싱 주기", ["Monthly", "Yearly"])

# 메인 로직
if abs(total_w - 1.0) < 0.001 and tickers:
    start_date = datetime(sy, 1, 1)
    end_date = datetime(ey, 12, 31)
    
    with st.spinner('분석 중...'):
        returns = load_monthly_returns(tickers)
        if not returns.empty:
            mask = (returns.index >= pd.Timestamp(start_date)) & (returns.index <= pd.Timestamp(end_date))
            filtered_returns = returns.loc[mask]
            
            if not filtered_returns.empty:
                portfolio = backtest(filtered_returns, weights, rebalance_option)
                st.subheader("📈 자산 성장 곡선")
                fig, ax = plt.subplots()
                ax.plot(portfolio * 1000)
                st.pyplot(fig)
            else:
                st.warning("선택한 기간에 데이터가 없습니다.")
else:
    st.info("비중 합계를 100%로 맞춰주세요.")
