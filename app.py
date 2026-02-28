import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
from data_loader import load_monthly_returns
from portfolio import backtest
from metrics import calculate_cagr, calculate_mdd

# 1. 페이지 기본 설정
st.set_page_config(page_title="Custom Asset Analyzer", layout="wide")
st.title("🚀 내 맘대로 자산배분 테스터")

# ---------------------------------------------------------
# 2. 사이드바: 자산 및 비중 설정
# ---------------------------------------------------------
with st.sidebar:
    st.header("1. 자산 설정")
    # 지수 티커 예시: ^GSPC(S&P500), ^IXIC(나스닥), GC=F(금선물), BTC-USD(비트코인)
    ticker_input = st.text_input(
        "티커 입력 (쉼표로 구분)", 
        "^GSPC, ^IXIC, GC=F, BTC-USD",
        help="지수 데이터를 보려면 ^GSPC, ^IXIC 등을 입력하세요."
    )
    tickers = [t.strip().upper() for t in ticker_input.split(",") if t.strip()]

    st.header("2. 비중 설정")
    
    # [데이터 초기화] 티커 리스트가 변경되면 세션 상태를 새로 고침
    if 'prev_tickers' not in st.session_state or st.session_state.prev_tickers != tickers:
        st.session_state.prev_tickers = tickers
        n = len(tickers)
        for t in tickers:
            # 초기 비중을 균등하게 배분하여 'val_티커'에 저장
            st.session_state[f"val_{t}"] = 100 // n if n > 0 else 0

    # [동기화 함수] 슬라이더나 숫자창이 바뀔 때 실행되어 합계 100%를 유지함
    def update_sync(target_ticker, key_prefix):
        # 1. 사용자가 건드린 위젯의 값을 가져와 중앙 세션값(val_)에 저장
        new_val = st.session_state[f"{key_prefix}_{target_ticker}"]
        st.session_state[f"val_{target_ticker}"] = new_val
        
        # 2. 다른 자산들의 비중을 자동으로 조절하여 합계 100% 유지
        other_tickers = [t for t in tickers if t != target_ticker]
        if not other_tickers:
            st.session_state[f"val_{target_ticker}"] = 100
            return

        remaining = 100 - new_val
        current_other_sum = sum(st.session_state[f"val_{t}"] for t in other_tickers)
        
        if current_other_sum > 0:
            for t in other_tickers:
                ratio = st.session_state[f"val_{t}"] / current_other_sum
                st.session_state[f"val_{t}"] = int(remaining * ratio)
        else:
            # 나머지가 모두 0인 경우 남은 비중을 균등 배분
            for t in other_tickers:
                st.session_state[f"val_{t}"] = remaining // len(other_tickers)

    # [위젯 생성] 슬라이더와 숫자 입력창을 나란히 배치
    weights = {}
    for ticker in tickers:
        st.write(f"**{ticker}**")
        col_slider, col_num = st.columns([7, 3])
        
        # 슬라이더: value를 중앙 세션값으로 고정하여 양방향 동기화 구현
        with col_slider:
            st.slider(
                f"S_{ticker}", 0, 100, 
                key=f"slider_{ticker}", 
                value=st.session_state[f"val_{ticker}"],
                on_change=update_sync, 
                args=(ticker, "slider"),
                label_visibility="collapsed"
            )
        
        # 숫자 입력창: 위 슬라이더와 동일한 중앙 세션값을 바라봄
        with col_num:
            st.number_input(
                f"N_{ticker}", 0, 100, 
                key=f"num_{ticker}", 
                value=st.session_state[f"val_{ticker}"],
                on_change=update_sync, 
                args=(ticker, "num"),
                label_visibility="collapsed"
            )
        
        # 연산에 사용할 비중값 저장 (0.0 ~ 1.0)
        weights[ticker] = st.session_state[f"val_{ticker}"] / 100

    # 최종 합계 출력 및 보정 버튼
    total_w = sum(st.session_state[f"val_{t}"] for t in tickers)
    st.markdown(f"### 현재 합계: `{total_w}%`")
    
    if total_w != 100 and len(tickers) > 0:
        if st.button("100% 강제 맞춤"):
            st.session_state[f"val_{tickers[0]}"] += (100 - total_w)
            st.rerun()

    st.header("3. 분석 설정")
    years = st.slider("롤링 기간 (년)", 1, 20, 5)
    rebalance_option = st.selectbox("리밸런싱 주기", ["Monthly", "Yearly"])

# ---------------------------------------------------------
# 3. 메인 화면: 결과 출력
# ---------------------------------------------------------
if total_w == 100 and tickers:
    with st.spinner('역사적 데이터를 분석 중입니다...'):
        returns = load_monthly_returns(tickers)
    
    if not returns.empty:
        # 백필링 엔진(다중 자산 순차 합류) 실행
        portfolio = backtest(returns, weights, rebalance_option)
        mdd = calculate_mdd(portfolio)

        # 그래프 출력 영역
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("📈 자산 성장 곡선 ($1,000 투자 시)")
            fig1, ax1 = plt.subplots()
            ax1.plot(portfolio * 1000)
            st.pyplot(fig1)
        
        with c2:
            st.subheader(f"📉 {years}년 롤링 수익률")
            if len(portfolio) < years * 12:
                st.warning(f"⚠️ {years}년치 데이터가 부족합니다.")
                rolling_cagr = None
            else:
                rolling_cagr = calculate_cagr(portfolio, years)
                fig2, ax2 = plt.subplots()
                rolling_cagr.plot(ax=ax2, color='orange')
                st.pyplot(fig2)

        st.divider()
        st.subheader("🔢 성과 요약")
        m1, m2, m3 = st.columns(3)
        m1.metric("최종 자산 가치", f"${(portfolio.iloc[-1]*1000):,.2f}")
        m2.metric("평균 롤링 수익률", f"{(rolling_cagr.mean()*100):.2f}%" if rolling_cagr is not None else "N/A")
        m3.metric("최대 낙폭 (MDD)", f"{(mdd*100):.2f}%")
    else:
        st.error("데이터 로드 실패. 티커를 확인해 주세요.")
else:
    st.info("사이드바에서 비중 합계를 100%로 맞춰주세요.")
