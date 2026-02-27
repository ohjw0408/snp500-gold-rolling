import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

st.title("Institutional-Grade S&P500 + Gold Backtest")

# -------------------
# 사용자 입력
# -------------------

weight_sp = st.slider("S&P500 비율 (%)", 0, 100, 50)
years = st.slider("롤링 기간 (년)", 1, 30, 5)
rebalance_option = st.selectbox(
    "리밸런싱 주기 선택",
    ["Daily", "Monthly", "Yearly"]
)

weight_sp = weight_sp / 100
weight_gold = 1 - weight_sp

start_date = "1970-01-01"

# -------------------
# 데이터 다운로드
# -------------------

# -------------------
# 데이터 다운로드 (안정 버전)
# -------------------

sp_raw = yf.download("^SP500TR", start=start_date, auto_adjust=True)
gold_raw = yf.download("GC=F", start=start_date, auto_adjust=True)

# MultiIndex 방지
if isinstance(sp_raw.columns, pd.MultiIndex):
    sp = sp_raw["Close"]
else:
    sp = sp_raw["Close"]

if isinstance(gold_raw.columns, pd.MultiIndex):
    gold = gold_raw["Close"]
else:
    gold = gold_raw["Close"]

data = pd.concat([sp, gold], axis=1)
data.columns = ["SP500", "Gold"]
data = data.dropna()

returns = data.pct_change().dropna()

# -------------------
# 리밸런싱 로직
# -------------------

def backtest(returns, w_sp, w_gold, rebalance):

    sp_value = w_sp
    gold_value = w_gold

    values = []

    for date, row in returns.iterrows():
        r_sp = row["SP500"]
        r_gold = row["Gold"]

        # 각 자산 개별 성장
        sp_value *= (1 + r_sp)
        gold_value *= (1 + r_gold)

        total_value = sp_value + gold_value
        values.append(total_value)

        # 리밸런싱 시점
        if rebalance == "Daily":
            sp_value = total_value * w_sp
            gold_value = total_value * w_gold

        elif rebalance == "Monthly":
            if date.is_month_end:
                sp_value = total_value * w_sp
                gold_value = total_value * w_gold

        elif rebalance == "Yearly":
            if date.month == 12 and date.is_month_end:
                sp_value = total_value * w_sp
                gold_value = total_value * w_gold

    return pd.Series(values, index=returns.index)

portfolio = backtest(returns, weight_sp, weight_gold, rebalance_option)

# -------------------
# 롤링 CAGR 계산
# -------------------

rolling_days = years * 252  # 연평균 거래일 기준

rolling_cagr = (
    portfolio
    .pct_change(rolling_days)
)

rolling_cagr = (
    (portfolio / portfolio.shift(rolling_days))
    ** (1/years) - 1
)

# -------------------
# 누적 포트폴리오 가치 (Start = 1000)
# -------------------

initial_value = 1000

portfolio_value_scaled = portfolio * initial_value

# -------------------
# 그래프 출력
# -------------------

fig, ax = plt.subplots(figsize=(10, 5))
rolling_cagr.plot(ax=ax)
ax.set_title(f"{years}-Year Rolling CAGR")
ax.set_ylabel("Annualized Return")
st.pyplot(fig)

# -------------------
# 그래프 출력 - 토탈리턴 그래프
# -------------------

fig2, ax2 = plt.subplots()
ax2.plot(portfolio_value_scaled)
ax2.set_ylabel("Portfolio Value")
ax2.set_xlabel("Date")
st.pyplot(fig2)

# -------------------
# 통계 출력
# -------------------

st.subheader("통계")

st.write("평균 CAGR:", round(rolling_cagr.mean() * 100, 2), "%")
st.write("최저 CAGR:", round(rolling_cagr.min() * 100, 2), "%")
st.write("최고 CAGR:", round(rolling_cagr.max() * 100, 2), "%")
