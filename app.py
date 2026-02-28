import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd

from data_loader import load_monthly_returns
from portfolio import backtest
from metrics import calculate_cagr, calculate_mdd

st.set_page_config(page_title="Custom Asset Analyzer", layout="wide")
st.title("🚀 내 맘대로 자산배분 테스터")

# -------------------
# 1. 사용자 입력 (티커 입력창)
# -------------------
with st.sidebar:
    st.header("1. 자산 설정")
    # 사용자가 쉼표로 구분해서 티커 입력
    ticker_input = st.text_input("티커 입력 (쉼표로 구분)", "SPY, TLT, GLD, BTC-USD")
    tickers = [t.strip().upper() for t in ticker_input.split(",") if t.strip()]
    
    st.header("2. 비중 설정")
    weights = {}
    total_w = 0
    for i, ticker in enumerate(tickers):
        # 자산별 슬라이더 자동 생성 (기본값은 균등 배분)
        default_w = 100 // len(tickers)
        w = st.slider(f"{ticker} 비중 (%)", 0, 100, default_w, key=f"w_{ticker}")
        weights[ticker] = w / 100
        total_w += w
    
    if total_w != 100:
        st.error(f"비중 합계가 {total_w}%입니다. 100%로 맞춰주세요!")

    st.header("3. 기타 설정")
    years = st.slider("롤링 기간 (년)", 1, 20, 5)
    rebalance_option = st.selectbox("리밸런싱 주기", ["Monthly", "Yearly"])

# -------------------
# 2. 실행 조건 확인 및 연산
# -------------------
if total_w == 100 and tickers:
    with st.spinner('데이터를 불러오는 중...'):
        returns = load_monthly_returns(tickers)
    
    if not returns.empty:
        portfolio = backtest(returns, weights, rebalance_option)
        rolling_cagr = calculate_cagr(portfolio, years)
        mdd = calculate_mdd(portfolio)

        # -------------------
        # 3. 화면 출력
        # -------------------
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("📈 자산 성장 곡선 ($1,000 투자 시)")
            fig2, ax2 = plt.subplots()
            ax2.plot(portfolio * 1000)
            st.pyplot(fig2)
        
        with col2:
            st.subheader(f"📉 {years}년 롤링 수익률")
            fig, ax = plt.subplots()
            rolling_cagr.plot(ax=ax, color='orange')
            st.pyplot(fig)

        st.divider()
        st.subheader("🔢 핵심 성과 지표")
        v1, v2, v3 = st.columns(3)
        v1.metric("최종 가치", f"${(portfolio.iloc[-1]*1000):,.2f}")
        v2.metric("평균 롤링 수익률", f"{(rolling_cagr.mean()*100):.2f}%")
        v3.metric("최대 낙폭 (MDD)", f"{(mdd*100):.2f}%")
    else:
        st.warning("데이터를 가져오지 못했습니다. 티커가 올바른지 확인해주세요.")
else:
    st.info("왼쪽에서 티커를 입력하고 비중 합계를 100%로 맞춰주세요.")
