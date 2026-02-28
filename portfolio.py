import pandas as pd
import numpy as np

def backtest(returns, weights, rebalance_option="Monthly"):
    # 수익률 하한선 제한 (상폐 수준의 급락 방어)
    returns = returns.fillna(0).clip(lower=-0.999)
    
    w = pd.Series(weights)
    portfolio_values = []
    current_val = 1.0 
    current_weights = w.copy()
    
    for date, monthly_ret in returns.iterrows():
        # 데이터가 없는 초기 구간(수익률 0)은 1.0 유지
        if (current_val == 1.0) and (monthly_ret.sum() == 0):
            portfolio_values.append(current_val)
            continue

        asset_values = current_weights * (1 + monthly_ret)
        port_ret = asset_values.sum()
        
        # 가치 업데이트 (수치가 0이 되어 사라지는 것 방지)
        current_val = max(current_val * port_ret, 1e-12)
        portfolio_values.append(current_val)
        
        # 리밸런싱
        if rebalance_option == "Monthly":
            current_weights = w.copy()
        elif rebalance_option == "Yearly" and date.month == 12:
            current_weights = w.copy()
        else:
            # 리밸런싱 안 할 경우 비중 추적
            current_weights = asset_values / port_ret if port_ret > 0 else current_weights
            
    return pd.Series(portfolio_values, index=returns.index)
