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

    st.header("3. 분석 및 기간 설정")
    
st.header("3. 분석 및 기간 설정")
    
    # 시작 날짜: 1900년부터 현재까지 선택할 수 있도록 범위를 대폭 확장
    start_date = st.date_input(
        "시작 날짜",
        value=datetime(2010, 1, 1),
        min_value=datetime(1900, 1, 1), # 1900년까지 내려갈 수 있음
        max_value=datetime.now()         # 오늘 날짜까지 선택 가능
    )
    
    # 종료 날짜: 1900년부터 2026년까지 선택 가능
    end_date = st.date_input(
        "종료 날짜",
        value=datetime.now(),
        min_value=datetime(1900, 1, 1),
        max_value=datetime.now() # 2026년 말까지 선택 가능
    )
    
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
                # 사용자가 지정한 기간으로 데이터 자르기
                mask = (returns.index >= pd.Timestamp(start_date)) & (returns.index <= pd.Timestamp(end_date))
                filtered_returns = returns.loc[mask]
                
                if filtered_returns.empty:
                    st.warning("선택한 기간에 데이터가 없습니다. 자산 상장일 이후의 날짜를 선택해 주세요.")
                else:
                    portfolio = backtest(filtered_returns, weights, rebalance_option)
                    mdd = calculate_mdd(portfolio)

                    col1, col2 = st.columns(2)
                    with col1:
                        st.subheader(f"📈 자산 성장 곡선 ({start_date} ~ {end_date})")
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
                            st.info("기간이 너무 짧아 롤링 수익률을 계산할 수 없습니다.")

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
