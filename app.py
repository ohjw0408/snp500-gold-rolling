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
    # [수정] 날짜 선택 범위를 1980년부터로 확장하여 '락'을 해제합니다.
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
    
    st.divider()
    
    data_mode = st.radio(
        "데이터 정밀도",
        ["월간 (빠름/장기)", "일간 (정밀/단기)"],
        index=0
    )
    interval = "1mo" if "월간" in data_mode else "1d"

    # [수정] 롤링 기간을 데이터 길이에 따라 유연하게 선택하도록 조정
    years = st.number_input("롤링 수익률 분석 기간 (년)", min_value=1, max_value=40, value=5)
    rebalance_option = st.selectbox("리밸런싱 주기", ["Monthly", "Yearly"])
    # [추가] 로그 스케일 선택 체크박스
    use_log_scale = st.checkbox("차트 로그 스케일 적용", value=True, help="수십 년치 장기 데이터의 변동을 균형 있게 보려면 체크하세요.")

# -------------------
# 3. 메인 결과 출력
# -------------------
if abs(total_w - 1.0) < 0.001 and tickers:
    if start_date >= end_date:
        st.error("종료 날짜는 시작 날짜보다 나중이어야 합니다.")
    else:
        with st.spinner(f'{data_mode} 데이터를 분석 중입니다...'):
            returns = load_monthly_returns(tickers, interval=interval)
            
            if not returns.empty:
                # 날짜 필터링
                mask = (returns.index >= pd.Timestamp(start_date)) & (returns.index <= pd.Timestamp(end_date))
                filtered_returns = returns.loc[mask]
                
                if filtered_returns.empty:
                    st.warning("⚠️ 해당 기간에 데이터가 없습니다. 시작 날짜를 늦춰보세요.")
                else:
                    portfolio = backtest(filtered_returns, weights, rebalance_option)
                    mdd = calculate_mdd(portfolio)

                    col1, col2 = st.columns(2)
                    # ... app.py의 결과 출력 부분 수정 ...
                    with col1:
                        st.subheader("📈 원화 자산 성장 곡선")
                        fig1, ax1 = plt.subplots()
                        # 초기 투자금 1,000만 원 기준
                        ax1.plot(portfolio * 10000000, label="포트폴리오 (원화)")
                        
                        # [수정] 사용자가 체크했을 때만 로그 스케일 적용
                        if use_log_scale:
                            ax1.set_yscale('log')
                            ax1.set_ylabel("자산 가치 (로그 스케일)")
                        else:
                            ax1.set_ylabel("자산 가치 (일반 스케일)")
                            
                        ax1.legend()
                        st.pyplot(fig1)
                    
                    with col2:
                        st.subheader(f"📉 {years}년 롤링 수익률")
                        # 데이터 포인트가 충분한지 확인 (월간/일간 구분)
                        required_points = years * 12 if interval == "1mo" else years * 252
                        if len(portfolio) > required_points:
                            rolling_cagr = calculate_cagr(portfolio, years)
                            fig2, ax2 = plt.subplots()
                            rolling_cagr.plot(ax=ax2, color='orange')
                            st.pyplot(fig2)
                        else:
                            st.info(f"롤링 분석을 하려면 최소 {years}년 이상의 데이터가 필요합니다.")

                    st.divider()
                    st.subheader("🔢 원화 기준 성과 요약")
                    m1, m2, m3 = st.columns(3)
                    m1.metric("최종 가치", f"{(portfolio.iloc[-1]*10000000):,.0f}원")
                    avg_r = f"{(rolling_cagr.mean()*100):.2f}%" if 'rolling_cagr' in locals() else "N/A"
                    m2.metric(f"평균 {years}년 수익률", avg_r)
                    m3.metric("최대 낙폭 (MDD)", f"{(mdd*100):.2f}%")
            else:
                st.error("데이터 로드에 실패했습니다. 티커와 인터넷 연결을 확인하세요.")
else:
    st.info("사이드바에서 자산 비중 합계를 100%로 맞춰주세요.")
