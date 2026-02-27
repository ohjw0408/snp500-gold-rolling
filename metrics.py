import numpy as np

def calculate_cagr(portfolio, years):
    rolling = (portfolio / portfolio.shift(years * 12)) ** (1 / years) - 1
    return rolling.dropna()

def calculate_mdd(portfolio):
    running_max = portfolio.cummax()
    drawdown = (portfolio - running_max) / running_max
    return drawdown.min()
