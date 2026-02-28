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
# 2. 사이드바 설정 (구조 통합)
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
    
    # [수정 핵심] min/max 범위를 1900~2100년으로 넉넉하게 잡았습니다.
    start_date = st.date_input(
        "시작 날짜",
        value=datetime(1990, 1, 1),
        min_value=datetime(1900, 1, 1),
        max_value=datetime.now()
    )
    
    end_date = st.date_input(
        "종료 날짜",
        value=datetime.now(),
        min_value=datetime(1900, 1, 1),
        max_value=datetime.now()
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
        # 데이터 로드 시 날짜를 인자로 넘기지 않고 전체를 가져온 뒤 필터링합니다.
        with st.spinner('데이터를 실시간으로 분석 중입니다...'):
            returns = load_monthly_returns(tickers)
            
            if not returns.empty:
                # pandas Timestamp로 변환하여 마스킹
                mask = (returns.index >= pd.Timestamp(start_date)) & (returns.index <= pd.Timestamp(end_date))
                filtered_returns = returns.loc[mask]
                
                if filtered_returns.empty:
                    st.warning("⚠️ 선택하신 기간에 자산 데이터가 존재하지 않습니다. 날짜를 조정해 주세요.")
                else:
                    portfolio = backtest(filtered_returns, weights, rebalance_option)
                    mdd = calculate_mdd(portfolio)

                    col1, col2 = st.columns(2)
                    with col1:
                        st.subheader(f"📈 자산 성장 곡선")
                        st.caption(f"{start_date} ~ {end_date}")
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
                            st.info("데이터 기간이 설정한 롤링 기간보다 짧습니다.")

                    st.divider()
                    st.subheader("🔢 성과 요약")
                    m1, m2, m3 = st.columns(3)
                    m1.metric("최종 가치", f"${(portfolio.iloc[-1]*1000):,.2f}")
                    
                    # 롤링 수익률이 계산된 경우에만 평균 표시
                    avg_rolling = f"{(rolling_cagr.mean()*100):.2f}%" if 'rolling_cagr' in locals() else "N/A"
                    m2.metric("평균 롤링 수익률", avg_rolling)
                    m3.metric("최대 낙폭 (MDD)", f"{(mdd*100):.2f}%")
            else:
                st.error("데이터 로드에 실패했습니다. 티커를 확인해 주세요.")
else:
    st.info("왼쪽 사이드바에서 비중 합계를 100%로 맞춰주세요.")
