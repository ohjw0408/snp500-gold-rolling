import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

st.title("S&P500 + Gold Rolling Return Calculator")

# 입력값
weight_sp = st.slider("S&P500 비율 (%)", 0, 100, 50)
years = st.slider("롤링 기간 (년)", 1, 30, 5)

weight_sp = weight_sp / 100
weight_gold = 1 - weight_sp

# 데이터 다운로드
sp = yf.download("^GSPC", start="1970-01-01", interval="1mo", auto_adjust=True)
gold = yf.download("GLD", start="1970-01-01", interval="1mo", auto_adjust=True)

sp = sp["Close"]
gold = gold["Close"]

data = pd.concat([sp, gold], axis=1)
data.columns = ["SP500", "Gold"]
data = data.dropna()

# 월 수익률 계산
returns = data.pct_change().dropna()

# 포트폴리오 수익률
portfolio = weight_sp * returns["SP500"] + weight_gold * returns["Gold"]

# 롤링 계산
rolling_period = years * 12

rolling_return = (
    (1 + portfolio)
    .rolling(rolling_period)
    .apply(lambda x: np.prod(x) ** (12/rolling_period) - 1)
)

# 그래프
fig, ax = plt.subplots()
rolling_return.plot(ax=ax)
ax.set_ylabel("Annualized Return")
ax.set_title(f"{years}-Year Rolling Return")
st.pyplot(fig)
