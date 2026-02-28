import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd  # 데이터 표를 다루기 위해 추가

from data_loader import load_monthly_returns
from portfolio import backtest
from metrics import calculate_cagr, calculate_mdd

st.set_page_config(page_title="Asset Allocation Analyzer", layout="wide") # 넓게 보기
st.title("📊 자산배분 엔진 검증 대시보드")

# -------------------
# 1. 사용자 입력 (Sidebar로 이동하여 화면을 넓게 사용)
# -------------------
with st.sidebar:
    st.header("설정")
    weight_sp = st.slider("S&P500 비율 (%)", 0, 100, 50)
    years = st.slider("롤링 기간 (년)", 1, 30, 5)
    rebalance_option = st.selectbox("리밸런싱 주기", ["Monthly", "Yearly"])

weights = {
    "SP500": weight_sp / 100,
    "Gold": 1 - weight_sp / 100
}

# -------------------
# 2. 데이터 로드 및 연산
# -------------------
returns = load_monthly_returns()
portfolio = backtest(returns, weights, rebalance_option)
rolling_cagr = calculate_cagr(portfolio, years)
mdd = calculate_mdd(portfolio)

# -------------------
# 3. 시각화 및 데이터 검증 (핵심 추가 부분)
# -------------------
col1, col2 = st.columns(2)

with col1:
    st.subheader("📈 포트폴리오 성장 곡선")
    fig2, ax2 = plt.subplots()
    ax2.plot(portfolio * 1000, label="Portfolio")
    ax2.set_title("Growth of $1,000")
    st.pyplot(fig2)

with col2:
    st.subheader("📉 롤링 수익률 (Rolling CAGR)")
    fig, ax = plt.subplots()
    rolling_cagr.plot(ax=ax, color='orange')
    ax.set_title(f"{years}-Year Rolling CAGR")
    st.pyplot(fig)

st.divider()

# --- 여기서부터 숫자를 확인하는 테이블입니다 ---
st.subheader("🔢 데이터 상세 검증")

v_col1, v_col2, v_col3 = st.columns(3)
v_col1.metric("최종 자산 가치", f"${(portfolio.iloc[-1] * 1000):,.2f}")
v_col2.metric("평균 롤링 수익률", f"{(rolling_cagr.mean() * 100):.2f}%")
v_col3.metric("최대 낙폭 (MDD)", f"{(mdd * 100):.2f}%")

# 연도별 수익률 표 생성
st.write("📅 **연도별 수익률 데이터** (엑셀과 대조해보세요)")
annual_perf = portfolio.resample('Y').last().pct_change()
st.dataframe(annual_perf.to_frame(name="Annual Return").style.format("{:.2%}"), use_container_width=True)

# 원본 데이터 확인용 체크박스
if st.checkbox("야후 파이낸스에서 가져온 원본 월간 수익률 보기"):
    st.write(returns)
