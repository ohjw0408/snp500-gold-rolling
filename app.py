import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
from data_loader import load_monthly_returns
from portfolio import backtest
from metrics import calculate_cagr, calculate_mdd

# 페이지 설정
st.set_page_config(page_title="Custom Asset Analyzer", layout="wide")
st.title("🚀 내 맘대로 자산배분 테스터")

# ---------------------------------------------------------
# 1. 사이드바 설정 영역
# ---------------------------------------------------------
with st.sidebar:
    st.header("1. 자산 설정")
    # 기본 지수 티커 예시 제공 (^GSPC: S&P500, ^IXIC: 나스닥, GC=F: 금선물)
    ticker_input = st.text_input(
        "티커 입력 (쉼표로 구분)", 
        "^GSPC, ^IXIC, GC=F, BTC-USD",
        help="지수 데이터를 보려면 ^GSPC, ^IXIC 등을 입력하세요."
    )
    tickers = [t.strip().upper() for t in ticker_input.split(",") if t.strip()]

    st.header("2. 비중 설정")
    
    # 세션 상태 초기화: 티커 리스트가 바뀌면 비중 값을 새로 세팅
    if 'prev_tickers' not in st.session_state or st.session_state.prev_tickers != tickers:
        st.session_state.prev_tickers = tickers
        n = len(tickers)
        for t in tickers:
            # 초기 비중은 균등하게 배분
            st.session_state[f"val_{t}"] = 100 // n if n > 0 else 0

    # [핵심] 비중 동기화 및 자동 조절 함수
    def update_weights(target_ticker, key_suffix):
        # 방금 수정한 위젯(슬라이더 혹은 입력창)의 값을 가져와서 공통 세션값에 저장
        new_val = st.session_state[f"{key_suffix}_{target_ticker}"]
        st.session_state[f"val_{target_ticker}"] = new_val
        
        other_tickers = [t for t in tickers if t != target_ticker]
        if not other_tickers:
            st.session_state[f"val_{target_ticker}"] = 100
            return

        # 합계 100을 유지하기 위해 나머지 자산들의 비중을 재계산
        remaining = 100 - new_val
        current_other_sum = sum(st.session_state[f"val_{t}"] for t in other_tickers)
        
        if current_other_sum > 0:
            for t in other_tickers:
                # 기존 비율을 유지하며 남은 파이를 나눠가짐
                ratio = st.session_state[f"val_{t}"] / current_other_sum
                st.session_state[f"val_{t}"] = int(remaining * ratio)
        else:
            # 나머지가 모두 0이었으면 균등하게 배분
            for t in other_tickers:
                st.session_state[f"val_{t}"] = remaining // len(other_tickers)

    # 비중 조절 위젯 생성 루프
    weights = {}
    for ticker in tickers:
        st.write(f"**{ticker}**")
        col_slider, col_num = st.columns([7, 3])
        
        # 슬라이더: value를 st.session_state[f"val_{ticker}"]로 고정하여 동기화
        with col_slider:
            st.slider(
                f"Slider_{ticker}", 0, 100, 
                key=f"slider_{ticker}", 
                value=st.session_state[f"val_{ticker}"],
                on_change=update_weights, 
                args=(ticker, "slider"),
                label_visibility="collapsed"
            )
        
        # 숫자 입력창: 위와 동일한 로직 적용
        with col_num:
            st.number_input(
                f"Num_{ticker}", 0, 100, 
                key=f"num_{ticker}", 
                value=st.session_state[f"val_{ticker}"],
                on_change=update_weights, 
                args=(ticker, "num"),
                label_visibility="collapsed"
            )
        
        # 실제 연산에 사용할 비중 저장 (0.0 ~ 1.0)
        weights[ticker] = st.session_state[f"val_{ticker}"] / 100

    # 최종 합계 표시
    total_w = sum(st.session_state[f"val_{t}"] for t in tickers)
    st.markdown(f"### 현재 합계: `{total_w}%`")
    
    # 정수 연산 오차(1% 내외) 보정 버튼
    if total_w != 100 and len(tickers) > 0:
        if st.button("100% 맞춤 보정"):
            st.session_state[f"val_{tickers[0]}"] += (100 - total_w)
            st.rerun()

    st.header("3. 기타 설정")
    years = st.slider("롤링 기간 (년)", 1, 20, 5)
    rebalance_option = st.selectbox("리밸런싱 주기", ["Monthly", "Yearly"])

# ---------------------------------------------------------
# 2. 메인 화면 연산 및 그래프 출력
# ---------------------------------------------------------
# 비중 합계가 100%일 때만 실행 (합계 오류 시 실행 방지)
if total_w == 100 and tickers:
    with st.spinner('데이터를 불러오고 백테스트를 진행 중입니다...'):
        returns = load_monthly_returns(tickers)
    
    if not returns.empty:
        # 백필링 엔진 실행
        portfolio = backtest(returns, weights, rebalance_option)
        mdd = calculate_mdd(portfolio)

        # 결과 시각화
        col_main1, col_main2 = st.columns(2)
        
        with col_main1:
            st.subheader("📈 자산 성장 곡선 ($1,000 투자 시)")
            fig_growth, ax_growth = plt.subplots()
            ax_growth.plot(portfolio * 1000)
            st.pyplot(fig_growth)
        
        with col_main2:
            st.subheader(f"📉 {years}년 롤링 수익률")
            if len(portfolio) < years * 12:
                st.warning(f"⚠️ 데이터 기간이 {years}년보다 짧아 롤링 수익률을 계산할 수 없습니다.")
                rolling_cagr = None
            else:
                rolling_cagr = calculate_cagr(portfolio, years)
                fig_roll, ax_roll = plt.subplots()
                rolling_cagr.plot(ax=ax_roll, color='orange')
                st.pyplot(fig_roll)

        st.divider()
        
        # 핵심 성과 지표 출력
        st.subheader("🔢 핵심 성과 지표")
        v1, v2, v3 = st.columns(3)
        v1.metric("최종 가치", f"${(portfolio.iloc[-1]*1000):,.2f}")
        
        avg_rolling = f"{(rolling_cagr.mean()*100):.2f}%" if rolling_cagr is not None else "N/A"
        v2.metric("평균 롤링 수익률", avg_rolling)
        v3.metric("최대 낙폭 (MDD)", f"{(mdd*100):.2f}%")
    else:
        st.error("데이터를 가져오지 못했습니다. 티커명이 정확한지 확인해 주세요.")
else:
    st.info("왼쪽 사이드바에서 비중 합계를 100%로 맞춰주세요.")
