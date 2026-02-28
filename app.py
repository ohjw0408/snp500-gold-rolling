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
    
    # 세션 상태 초기화
    if 'val' not in st.session_state or st.session_state.get('last_tickers') != tickers:
        st.session_state.last_tickers = tickers
        n = len(tickers)
        st.session_state.val = {t: 100 // n for t in tickers} if n > 0 else {}

    def on_change_logic(t, key_type):
        # 입력된 새 값을 가져옴
        new_v = st.session_state[f"{key_type}_{t}"]
        st.session_state.val[t] = new_v
        
        # 합계 조절 로직 (나머지 자산에서 차감)
        others = [ot for ot in tickers if ot != t]
        if others:
            rem = 100 - new_v
            current_other_sum = sum(st.session_state.val[ot] for ot in others)
            if current_other_sum > 0:
                for ot in others:
                    st.session_state.val[ot] = int(rem * (st.session_state.val[ot] / current_other_sum))
            else:
                for ot in others:
                    st.session_state.val[ot] = rem // len(others)
        
        # [중요] 강제 새로고침으로 위젯 눈금 동기화
        st.rerun()

    weights = {}
    for t in tickers:
        st.write(f"**{t}**")
        c1, c2 = st.columns([7, 3])
        current_v = st.session_state.val.get(t, 0)
        
        with c1:
            st.slider(f"S_{t}", 0, 100, current_v, key=f"sli_{t}", on_change=on_change_logic, args=(t, "sli"), label_visibility="collapsed")
        with c2:
            st.number_input(f"N_{t}", 0, 100, current_v, key=f"num_{t}", on_change=on_change_logic, args=(t, "num"), label_visibility="collapsed")
        
        weights[t] = current_v / 100

    total_w = sum(st.session_state.val.values())
    st.markdown(f"### 현재 합계: `{total_w}%`")
    
    # 100% 보정 버튼
    if total_w != 100 and len(tickers) > 0:
        if st.button("100% 강제 맞춤"):
            first_t = tickers[0]
            st.session_state.val[first_t] += (100 - total_w)
            st.rerun()

    st.header("3. 분석 설정")
    years = st.slider("롤링 기간 (년)", 1, 20, 5)
    rebalance_option = st.selectbox("리밸런싱 주기", ["Monthly", "Yearly"])

# -------------------
# 2. 메인 결과 출력
# -------------------
# 99%~101% 사이면 정수 계산 오차로 간주하고 실행 허용 (사용자 편의성)
if 99 <= total_w <= 101 and tickers:
    with st.spinner('분석 중...'):
        # 실제 계산 시에는 합계를 정확히 1.0으로 정규화하여 사용
        norm_weights = {t: w/sum(weights.values()) for t, w in weights.items()}
        returns = load_monthly_returns(tickers)
        
        if not returns.empty:
            portfolio = backtest(returns, norm_weights, rebalance_option)
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
                    st.warning("데이터 부족")

            st.divider()
            st.subheader("🔢 성과 요약")
            m1, m2, m3 = st.columns(3)
            m1.metric("최종 가치", f"${(portfolio.iloc[-1]*1000):,.2f}")
            m2.metric("평균 롤링 수익률", f"{(rolling_cagr.mean()*100):.2f}%" if 'rolling_cagr' in locals() else "N/A")
            m3.metric("최대 낙폭 (MDD)", f"{(mdd*100):.2f}%")
else:
    st.info("사이드바에서 비중 합계를 100%로 맞춰주세요.")
