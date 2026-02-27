import pandas as pd

def backtest(returns, weights, rebalance="Monthly"):

    weights = pd.Series(weights)
    weights = weights / weights.sum()

    portfolio_value = 1.0
    asset_values = weights.copy()

    values = []

    current_year = None

    for date, row in returns.iterrows():

        # 자산 성장
        asset_values = asset_values * (1 + row)

        total_value = asset_values.sum()
        values.append(total_value)

        # 리밸런싱
        if rebalance == "Monthly":
            asset_values = total_value * weights

        elif rebalance == "Yearly":
            if current_year != date.year:
                asset_values = total_value * weights
                current_year = date.year

    portfolio_series = pd.Series(values, index=returns.index)

    # 기준화
    portfolio_series = portfolio_series / portfolio_series.iloc[0]

    return portfolio_series
