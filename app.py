import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
from datetime import datetime
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
    ticker_input = st.text_input("티커 입력", "^GSPC, ^IXIC, GC=F, BTC-USD")
    tickers = [t.strip().upper() for t in ticker_input.split(",") if t.strip()]

    st.header("2. 비중 설정")
    weights = {}
    if tickers:
        n = len(tickers)
        for t in tickers:
            # key 값을 고유하게 설정하여 충돌 방지
            w_percent = st.slider(f"{t} 비중 (%)", 0, 100, 100 // n, key=f"weights_{t}")
            weights[t] = w_percent / 100
    
    total_w = sum(weights.values())
    if abs(total_w - 1.0) < 0.001:
        st.success(f"합계: {int(total_w*100)}%")
    else:
        st.warning(f"합계: {int(total_w*100)}% (100%로 맞춰주세요)")

    st.header("3. 분석 기간 설정")
    # [해결책] 에러를 뿜는 date_input 대신 number_input으로 연도 직접 입력
    # 이렇게 하면 '범위 밖' 에러가 절대 발생하지 않습니다.
    c1, c2 = st.columns(2)
    with c1:
        s_year = st.number_input("시작 연도", 1900, 2026, 1990)
    with c2:
        e_year = st.number_input("종료 연도", 1900, 2026, 2026)

    st.divider()
    # 롤링 기간 슬라이더 (이게 안 나왔던 이유는 위에서 코드가 멈췄기 때문입니다)
    years = st.slider("롤링 기간 (년)", 1, 20, 5, key="rolling_slider")
    rebalance_option = st.selectbox("리밸런싱 주기", ["Monthly", "Yearly"])

# -------------------
# 3. 메인 결과 출력
# -------------------
# 날짜 객체 생성 (안전하게 처리)
start_date = datetime(s_year, 1, 1)
end_date = datetime(e_year, 12, 31)

if abs(total_w - 1.0) < 0.001 and tickers:
    if start_date >= end_date:
        st.error("종료 연도는 시작 연도보다 커야 합니다.")
    else:
        with st.spinner('데이터 분석 중...'):
            returns = load_monthly_returns(tickers)
            if not returns.empty:
                mask = (returns.index >= pd.Timestamp(start_date)) & (returns.index <= pd.Timestamp(end_date))
                filtered_returns = returns.loc[mask]
                
                if filtered_returns.empty:
                    st.warning("선택한 기간에 데이터가 없습니다.")
                else:
                    portfolio = backtest(filtered_returns, weights, rebalance_option)
                    mdd = calculate_mdd(portfolio)

                    col1, col2 = st.columns(2)
                    with col1:
                        st.subheader("📈 자산 성장 곡선")
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
                            st.info("데이터가 부족합니다.")
