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
    ticker_input = st.text_input("티커 입력 (쉼표 구분)", "SPY, QQQ, SCHD, 069500.KS")
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

    st.header("3. 분석 기간 및 옵션")
    # [수정] 날짜 락 해제: max_value를 datetime.now()로 설정
    start_date = st.date_input("시작 날짜", value=datetime(1990, 1, 1), 
                               min_value=datetime(1900, 1, 1), 
                               max_value=datetime.now())
    end_date = st.date_input("종료 날짜", value=datetime.now(), 
                             min_value=datetime(1900, 1, 1), 
                             max_value=datetime.now())
    
    st.divider()
    
    data_mode = st.radio("데이터 정밀도", ["월간 (빠름/장기)", "일간 (정밀/단기)"], index=0)
    interval = "1mo" if "월간" in data_mode else "1d"
    years = st.number_input("롤링 수익률 분석 기간 (년)", min_value=1, max_value=40, value=5)
    rebalance_option = st.selectbox("리밸런싱 주기", ["Monthly", "Yearly"])

# -------------------
# 3. 메인 결과 출력
# -------------------
if abs(total_w - 1.0) < 0.001 and tickers:
    if start_date >= end_date:
        st.error("종료 날짜는 시작 날짜보다 나중이어야 합니다.")
    else:
        with st.spinner('데이터를 분석 중입니다...'):
            returns = load_monthly_returns(tickers, interval=interval)
            
            if not returns.empty:
                mask = (returns.index >= pd.Timestamp(start_date)) & (returns.index <= pd.Timestamp(end_date))
                filtered_returns = returns.loc[mask]
                
                if filtered_returns.empty:
                    st.warning("⚠️ 해당 기간에 데이터가 없습니다.")
                else:
                    portfolio = backtest(filtered_returns, weights, rebalance_option)
                    mdd = calculate_mdd(portfolio)

                    col1, col2 = st.columns(2)
                    with col1:
                        st.subheader("📈 자산 성장 곡선")
                        fig1, ax1 = plt.subplots()
                        ax1.plot(portfolio * 1000, label="Portfolio")
                        # [삭제] 로그 스케일 코드 제거 (일반 선형 스케일 사용)
                        ax1.set_ylabel("Value")
                        ax1.legend()
                        st.pyplot(fig1)
                    
                    with col2:
                        st.subheader(f"📉 {years}년 롤링 수익률")
                        required_points = years * 12 if interval == "1mo" else years * 252
                        if len(portfolio) > required_points:
                            rolling_cagr = calculate_cagr(portfolio, years)
                            fig2, ax2 = plt.subplots()
                            rolling_cagr.plot(ax=ax2, color='orange')
                            st.pyplot(fig2)
                        else:
                            st.info(f"최소 {years}년 이상의 데이터가 필요합니다.")

                    st.divider()
                    st.subheader("🔢 성과 요약")
                    m1, m2, m3 = st.columns(3)
                    m1.metric("최종 가치", f"${(portfolio.iloc[-1]*1000):,.2f}")
                    avg_r = f"{(rolling_cagr.mean()*100):.2f}%" if 'rolling_cagr' in locals() else "N/A"
                    m2.metric(f"평균 {years}년 수익률", avg_r)
                    m3.metric("최대 낙폭 (MDD)", f"{(mdd*100):.2f}%")
            else:
                st.error("데이터 로드 실패")
else:
    st.info("비중을 맞춰주세요.")
