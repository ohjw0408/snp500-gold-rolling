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
    ticker_input = st.text_input("티커 입력 (쉼표로 구분)", "^GSPC, ^IXIC, GC=F, BTC-USD")
    tickers = [t.strip().upper() for t in ticker_input.split(",") if t.strip()]

    st.header("2. 비중 설정")
    weights = {}
    if tickers:
        default_val = 100 // len(tickers)
        for t in tickers:
            w_percent = st.slider(f"{t} 비중 (%)", 0, 100, default_val, key=f"slide_{t}")
            weights[t] = w_percent / 100
    
    total_w = sum(weights.values())
    if abs(total_w - 1.0) < 0.001:
        st.success(f"합계: {int(total_w*100)}% (준비 완료!)")
    else:
        st.warning(f"합계: {int(total_w*100)}% (100%로 맞춰주세요)")

    st.header("3. 분석 기간 설정")
    
    # [핵심 변경] 달력 대신 드롭다운/숫자로 연도 직접 선택
    col_s1, col_s2 = st.columns(2)
    with col_s1:
        s_year = st.number_input("시작 연도", 1900, 2026, 1990)
    with col_s2:
        s_month = st.selectbox("시작 월", range(1, 13), index=0)
    
    col_e1, col_e2 = st.columns(2)
    with col_e1:
        e_year = st.number_input("종료 연도", 1900, 2026, 2026)
    with col_e2:
        e_month = st.selectbox("종료 월", range(1, 13), index=1) # 2월

    start_date = datetime(s_year, s_month, 1)
    end_date = datetime(e_year, e_month, 1)
    
    st.divider()
    years = st.slider("롤링 기간 (년)", 1, 20, 5)
    rebalance_option = st.selectbox("리밸런싱 주기", ["Monthly", "Yearly"])

# -------------------
# 3. 메인 결과 출력
# -------------------
if abs(total_w - 1.0) < 0.001 and tickers:
    if start_date >= end_date:
        st.error("종료 날짜는 시작 날짜보다 나중이어야 합니다.")
    else:
        with st.spinner('데이터 분석 중...'):
            returns = load_monthly_returns(tickers)
            
            if not returns.empty:
                mask = (returns.index >= pd.Timestamp(start_date)) & (returns.index <= pd.Timestamp(end_date))
                filtered_returns = returns.loc[mask]
                
                if filtered_returns.empty:
                    st.warning("⚠️ 해당 기간에 데이터가 없습니다. 자산 상장일 이후를 선택해 주세요.")
                else:
                    portfolio = backtest(filtered_returns, weights, rebalance_option)
                    mdd = calculate_mdd(portfolio)

                    col1, col2 = st.columns(2)
                    with col1:
                        st.subheader(f"📈 자산 성장 곡선")
                        st.caption(f"분석 기간: {start_date.strftime('%Y-%m')} ~ {end_date.strftime('%Y-%m')}")
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
                            st.info("선택한 기간이 롤링 기간보다 짧습니다.")

                    st.divider()
                    st.subheader("🔢 성과 요약")
                    m1, m2, m3 = st.columns(3)
                    m1.metric("최종 가치", f"${(portfolio.iloc[-1]*1000):,.2f}")
                    avg_rolling = f"{(rolling_cagr.mean()*100):.2f}%" if 'rolling_cagr' in locals() else "N/A"
                    m2.metric("평균 롤링 수익률", avg_rolling)
                    m3.metric("최대 낙폭 (MDD)", f"{(mdd*100):.2f}%")
else:
    st.info("왼쪽 사이드바에서 비중 합계를 100%로 맞춰주세요.")
