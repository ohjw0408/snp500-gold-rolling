import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
from data_loader import load_monthly_returns
from portfolio import backtest
from metrics import calculate_cagr, calculate_mdd

st.set_page_config(page_title="Custom Asset Analyzer", layout="wide")
st.title("🚀 내 맘대로 자산배분 테스터")

# -------------------
# 1. 사이드바 설정 (비중 자동 조절 + 키보드 입력)
# -------------------
with st.sidebar:
    st.header("1. 자산 설정")
    ticker_input = st.text_input("티커 입력 (쉼표로 구분)", "SPY, TLT, GLD, BTC-USD")
    tickers = [t.strip().upper() for t in ticker_input.split(",") if t.strip()]

    st.header("2. 비중 설정")
    
    # 세션 상태 초기화 (티커 변경 시 비중 초기화)
    if 'prev_tickers' not in st.session_state or st.session_state.prev_tickers != tickers:
        st.session_state.prev_tickers = tickers
        n = len(tickers)
        for t in tickers:
            st.session_state[f"w_{t}"] = 100 // n if n > 0 else 0

    # 비중 자동 조절 콜백 함수
    def on_weight_change(changed_ticker):
        new_val = st.session_state[f"w_{changed_ticker}"]
        other_tickers = [t for t in tickers if t != changed_ticker]
        if not other_tickers:
            st.session_state[f"w_{changed_ticker}"] = 100
            return
        remaining = 100 - new_val
        current_other_sum = sum(st.session_state[f"w_{t}"] for t in other_tickers)
        if current_other_sum > 0:
            for t in other_tickers:
                ratio = st.session_state[f"w_{t}"] / current_other_sum
                st.session_state[f"w_{t}"] = int(remaining * ratio)
        else:
            for t in other_tickers:
                st.session_state[f"w_{t}"] = remaining // len(other_tickers)

    # 비중 입력 위젯 (슬라이더 + 숫자 입력창 가로 배치)
    weights = {}
    for ticker in tickers:
        st.write(f"**{ticker}**")
        col_slider, col_num = st.columns([7, 3])
        with col_slider:
            st.slider("Slider", 0, 100, key=f"w_{ticker}", on_change=on_weight_change, args=(ticker,), label_visibility="collapsed")
        with col_num:
            st.number_input("Num", 0, 100, key=f"w_{ticker}", on_change=on_weight_change, args=(ticker,), label_visibility="collapsed")
        weights[ticker] = st.session_state[f"w_{ticker}"] / 100

    total_w = sum(st.session_state[f"w_{t}"] for t in tickers)
    st.markdown(f"### 합계: `{total_w}%`")
    
    if total_w != 100 and len(tickers) > 0:
        if st.button("100% 맞춤 보정"):
            st.session_state[f"w_{tickers[0]}"] += (100 - total_w)
            st.rerun()

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
        mdd = calculate_mdd(portfolio)

        col1, col2 = st.columns(2)
        with col1:
            st.subheader("📈 자산 성장 곡선 ($1,000 투자 시)")
            fig2, ax2 = plt.subplots()
            ax2.plot(portfolio * 1000)
            st.pyplot(fig2)
        
        with col2:
            st.subheader(f"📉 {years}년 롤링 수익률")
            if len(portfolio) < years * 12:
                st.warning(f"⚠️ 데이터 기간이 {years}년보다 짧습니다.")
                rolling_cagr = None
            else:
                rolling_cagr = calculate_cagr(portfolio, years)
                fig, ax = plt.subplots()
                rolling_cagr.plot(ax
