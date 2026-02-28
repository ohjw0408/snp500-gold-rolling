import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd

from data_loader import load_monthly_returns
from portfolio import backtest
from metrics import calculate_cagr, calculate_mdd

st.set_page_config(page_title="Custom Asset Analyzer", layout="wide")
st.title("🚀 내 맘대로 자산배분 테스터")

# -------------------
# 1. 사용자 입력 (Sidebar)
# -------------------
with st.sidebar:
    st.header("1. 자산 설정")
    ticker_input = st.text_input("티커 입력 (쉼표로 구분)", "SPY, TLT, GLD, BTC-USD")
    tickers = [t.strip().upper() for t in ticker_input.split(",") if t.strip()]
    
    st.header("2. 비중 설정")
    weights = {}
    total_w = 0
    for i, ticker in enumerate(tickers):
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
        # 데이터가 로드된 후 'portfolio'를 먼저 생성합니다.
        portfolio = backtest(returns, weights, rebalance_option)
        mdd = calculate_mdd(portfolio)

        # -------------------
        # 3. 화면 출력 (검증 로직 포함)
        # -------------------
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📈 자산 성장 곡선 ($1,000 투자 시)")
            fig2, ax2 = plt.subplots()
            ax2.plot(portfolio * 1000)
            st.pyplot(fig2)
        
        with col2:
            st.subheader(f"📉 {years}년 롤링 수익률")
            # 💡 여기서 검증! 데이터 길이가 롤링 기간보다 긴지 확인합니다.
            if len(portfolio) < years * 12:
                st.warning(f"⚠️ 데이터 기간이 {years}년보다 짧습니다. 롤링 기간을 낮춰주세요.")
                rolling_cagr = None # 계산하지 않음
            else:
                rolling_cagr = calculate_cagr(portfolio, years)
                fig, ax = plt.subplots()
                rolling_cagr.plot(ax=ax, color='orange')
                st.pyplot(fig)

        st.divider()
        st.subheader("🔢 핵심 성과 지표")
        v1, v2, v3 = st.columns(3)
        v1.metric("최종 가치", f"${(portfolio.iloc[-1]*1000):,.2f}")
        
        # 롤링 수익률이 계산되었을 때만 평균을 표시합니다.
        avg_rolling = f"{(rolling_cagr.mean()*100):.2f}%" if rolling_cagr is not None else "N/A"
        v2.metric("평균 롤링 수익률", avg_rolling)
        v3.metric("최대 낙폭 (MDD)", f"{(mdd*100):.2f}%")
    else:
        st.warning("데이터를 가져오지 못했습니다. 티커가 올바른지 확인해주세요.")
else:
    st.info("왼쪽에서 티커를 입력하고 비중 합계를 100%로 맞춰주세요.")
