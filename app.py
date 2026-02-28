import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
from data_loader import load_monthly_returns
from portfolio import backtest
from metrics import calculate_cagr, calculate_mdd

st.set_page_config(page_title="Custom Asset Analyzer", layout="wide")
st.title("🚀 내 맘대로 자산배분 테스터")

# -------------------
# 1. 사이드바 설정
# -------------------
with st.sidebar:
    st.header("1. 자산 설정")
    ticker_input = st.text_input("티커 입력 (쉼표로 구분)", "^GSPC, ^IXIC, GC=F, BTC-USD")
    tickers = [t.strip().upper() for t in ticker_input.split(",") if t.strip()]

    st.header("2. 비중 설정")
    
    # 세션 초기화
    if 'val' not in st.session_state or st.session_state.get('last_tickers') != tickers:
        st.session_state.last_tickers = tickers
        n = len(tickers)
        st.session_state.val = {t: 100 // n for t in tickers} if n > 0 else {}

    # 동기화 로직: 사용자가 변경한 값을 세션에 즉시 반영
    weights = {}
    temp_total = sum(st.session_state.val.values())

    for t in tickers:
        st.write(f"**{t}**")
        c1, c2 = st.columns([7, 3])
        
        # 슬라이더와 숫자 입력창이 동일한 세션 값을 공유 (key를 val_{t}로 통일)
        # 콜백 없이 key만 사용하여 자동 세션 업데이트 유도
        current_val = st.session_state.val.get(t, 0)
        
        # 슬라이더
        new_s = c1.slider(f"S_{t}", 0, 100, current_val, key=f"s_{t}", label_visibility="collapsed")
        # 숫자창
        new_n = c2.number_input(f"N_{t}", 0, 100, current_val, key=f"n_{t}", label_visibility="collapsed")
        
        # 둘 중 하나라도 바뀌면 세션 업데이트
        if new_s != current_val:
            st.session_state.val[t] = new_s
            st.rerun()
        elif new_n != current_val:
            st.session_state.val[t] = new_n
            st.rerun()
            
        weights[t] = st.session_state.val[t] / 100

    total_w = sum(st.session_state.val.values())
    
    # 합계 색상 표시
    color = "green" if total_w == 100 else "red"
    st.markdown(f"### 현재 합계: <span style='color:{color}'>{total_w}%</span>", unsafe_allow_html=True)
    
    if total_w != 100 and len(tickers) > 0:
        if st.button("100% 강제 맞춤"):
            diff = 100 - total_w
            st.session_state.val[tickers[0]] += diff
            st.rerun()

    st.header("3. 분석 설정")
    years = st.slider("롤링 기간 (년)", 1, 20, 5)
    rebalance_option = st.selectbox("리밸런싱 주기", ["Monthly", "Yearly"])

# -------------------
# 2. 메인 결과 출력
# -------------------
# 정수 오차 감안하여 100%일 때만 실행
if total_w == 100 and tickers:
    with st.spinner('역사적 데이터 분석 중...'):
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
                    st.warning("데이터가 부족하여 롤링 수익률을 표시할 수 없습니다.")

            st.divider()
            st.subheader("🔢 성과 요약")
            m1, m2, m3 = st.columns(3)
            m1.metric("최종 가치", f"${(portfolio.iloc[-1]*1000):,.2f}")
            m2.metric("평균 롤링 수익률", f"{(rolling_cagr.mean()*100):.2f}%" if 'rolling_cagr' in locals() else "N/A")
            m3.metric("최대 낙폭 (MDD)", f"{(mdd*100):.2f}%")
else:
    st.info("왼쪽 사이드바에서 비중 합계를 100%로 맞춰주세요.")
