import streamlit as st
import matplotlib.pyplot as plt

from data_loader import load_monthly_returns
from portfolio import backtest
from metrics import calculate_cagr, calculate_mdd

st.title("Institutional-Grade Asset Allocation Engine")

# -------------------
# 사용자 입력
# -------------------

weight_sp = st.slider("S&P500 비율 (%)", 0, 100, 50)
years = st.slider("롤링 기간 (년)", 1, 30, 5)
rebalance_option = st.selectbox(
    "리밸런싱 주기 선택",
    ["Monthly", "Yearly"]
)

weights = {
    "SP500": weight_sp / 100,
    "Gold": 1 - weight_sp / 100
}

# -------------------
# 데이터 로드
# -------------------

returns = load_monthly_returns()

# -------------------
# 백테스트 실행
# -------------------

portfolio = backtest(returns, weights, rebalance_option)

rolling_cagr = calculate_cagr(portfolio, years)
mdd = calculate_mdd(portfolio)

# -------------------
# 그래프 출력
# -------------------

fig, ax = plt.subplots()
rolling_cagr.plot(ax=ax)
ax.set_title(f"{years}-Year Rolling CAGR")
st.pyplot(fig)

fig2, ax2 = plt.subplots()
ax2.plot(portfolio * 1000)
ax2.set_title("Portfolio Growth (Start = 1000)")
st.pyplot(fig2)

# -------------------
# 통계
# -------------------

st.subheader("통계")

st.write("평균 CAGR:", round(rolling_cagr.mean() * 100, 2), "%")
st.write("최저 CAGR:", round(rolling_cagr.min() * 100, 2), "%")
st.write("최대 낙폭 (MDD):", round(mdd * 100, 2), "%")

# -------------------
# 데이터 검증용 수치 및 표 출력
# -------------------

st.subheader("📊 데이터 검증 센터")

# 1. 주요 지표 요약 (카드 형태)
col1, col2, col3 = st.columns(3)
col1.metric("최종 자산 (시작=1000)", f"{round(portfolio.iloc[-1] * 1000, 2)}")
col2.metric("평균 롤링 CAGR", f"{round(rolling_cagr.mean() * 100, 2)}%")
col3.metric("최대 낙폭 (MDD)", f"{round(mdd * 100, 2)}%")

# 2. 연도별 수익률 표 (데이터 검증의 핵심)
st.write("📅 연도별 포트폴리오 성과 (상세 데이터)")
# 연간 수익률로 계산해서 보여주기
annual_returns = portfolio.resample('Y').last().pct_change() * 100
st.dataframe(annual_returns.style.format("{:.2f}%")) 

# 3. 원본 월간 수익률 확인 (데이터 로더가 잘 작동하는지 확인)
if st.checkbox("원본 월간 데이터(Monthly Returns) 보기"):
    st.write(returns)
