import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
from data_loader import load_monthly_returns
from portfolio import backtest
from metrics import calculate_cagr, calculate_mdd

# 1. 페이지 설정
st.set_page_config(page_title="Custom Asset Analyzer", layout="wide")
st.title("🚀 내 맘대로 자산배분 테스터")

# -------------------
# 2. 사이드바 설정
# -------------------
with st.sidebar:
    st.header("1. 자산 설정")
    ticker_input = st.text_input("티커 입력 (쉼표로 구분)", "^GSPC, ^IXIC, GC=F, BTC-USD")
    tickers = [t.strip().upper() for t in ticker_input.split(",") if t.strip()]

    st.header("2. 비중 설정")
    
    # 세션 상태 초기화 (동기화 로직 삭제, 단순 저장용)
    if 'weights_dict' not in st.session_state:
        st.session_state.weights_dict = {}

    weights = {}
    for t in tickers:
        # 각 티커별로 슬라이더 하나만 깔끔하게 배치
        # (숫자 입력창과의 복잡한 연결을 끊어 무한 새로고침을 방지합니다)
        default_val = 100 // len(tickers) if len(tickers) > 0 else 0
        w_percent = st.slider(f"{t} 비중 (%)", 0, 100, default_val, key=f"slide_{t}")
        weights[t] = w_percent / 100

    total_w = sum(w for w in weights.values())
    
    # 합계 표시
    if total_w == 1: # 100%
        st.success(f"합계: {int(total_w*100)}% (준비 완료!)")
    else:
        st.warning(f"합계: {int(total_w*100)}% (100%로 맞춰주세요)")

    st.header("3. 분석 설정")
    years = st.slider("롤링 기간 (년)", 1, 20, 5)
    rebalance_option = st.selectbox("리밸런싱 주기", ["Monthly", "Yearly"])

# -------------------
# 3. 메인 결과 출력
# -------------------
if total_w == 1.0 and tickers:
    with st.spinner('데이터 분석 중...'):
        returns = load_monthly_returns(tickers)
        
        if not returns.empty:
            portfolio = backtest(returns, weights, rebalance_option)
            mdd = calculate_mdd(portfolio)

            col1, col2 = st.columns(2)
            with col1:
                st.subheader("📈 자산 성장 곡선 ($1,000 투자 시)")
                fig1, ax1 = plt.subplots()
                ax1.plot(portfolio * 1000)
                st.pyplot(fig1)
            with col2:
                st.subheader(f"📉 {years}년 롤링 수익률")
                if len(portfolio) >= years * 12:
                    rolling_cagr = calculate_cagr(portfolio, years)
                    fig2, ax2 = plt.subplots()
                    rolling_cagr.plot(ax=ax2, color='orange')
                    st.pyplot(fig2)
                else:
                    st.warning("데이터가 부족합니다.")

            st.divider()
            st.subheader("🔢 성과 요약")
            m1, m2, m3 = st.columns(3)
            m1.metric("최종 가치", f"${(portfolio.iloc[-1]*1000):,.2f}")
            m2.metric("평균 롤링 수익률", f"{(rolling_cagr.mean()*100):.2f}%" if 'rolling_cagr' in locals() else "N/A")
            m3.metric("최대 낙폭 (MDD)", f"{(mdd*100):.2f}%")
        else:
            st.error("데이터를 가져오지 못했습니다.")
else:
    st.info("왼쪽 사이드바에서 비중 합계를 100%로 맞춰주세요.")
