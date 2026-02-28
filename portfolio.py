import pandas as pd
import numpy as np

def backtest(returns, weights, rebalance_option="Monthly"):
    # 수익률 데이터 클리닝 및 하한선 제한
    returns = returns.fillna(0).clip(lower=-0.99)
    
    w = pd.Series(weights)
    portfolio_values = []
    current_val = 1.0 
    current_weights = w.copy()
    
    for date, monthly_ret in returns.iterrows():
        # 수익률이 모두 0인 구간(데이터 시작 전)은 가치를 유지
        if monthly_ret.sum() == 0 and current_val == 1.0:
            portfolio_values.append(current_val)
            continue

        asset_values = current_weights * (1 + monthly_ret)
        port_ret = asset_values.sum()
        
        # 가치 업데이트 (0이 되지 않도록 최소값 유지)
        current_val = max(current_val * port_ret, 1e-6)
        portfolio_values.append(current_val)
        
        # 리밸런싱
        if rebalance_option == "Monthly":
            current_weights = w.copy()
        elif rebalance_option == "Yearly" and date.month == 12:
            current_weights = w.copy()
        else:
            current_weights = asset_values / port_ret if port_ret > 0 else current_weights
            
    return pd.Series(portfolio_values, index=returns.index)
