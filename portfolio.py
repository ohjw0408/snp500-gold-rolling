import pandas as pd
import numpy as np

def backtest(returns, weights, rebalance_option="Monthly"):
    # 수익률 데이터가 너무 크거나 작으면(상폐 등) 에러가 날 수 있으므로 제한
    returns = returns.clip(lower=-0.99) # 자산 가치가 0 이하로 가는 것 방지
    
    w = pd.Series(weights)
    portfolio_values = []
    current_val = 1.0
    current_weights = w.copy()
    
    for date, monthly_ret in returns.iterrows():
        # 자산별 수익 반영
        asset_values = current_weights * (1 + monthly_ret)
        
        # 이번 달 포트폴리오 전체 수익률 가중치 합산
        port_ret = asset_values.sum()
        
        # 포트폴리오 가치 업데이트
        current_val *= port_ret
        portfolio_values.append(current_val)
        
        # 리밸런싱
        if rebalance_option == "Monthly":
            current_weights = w.copy()
        elif rebalance_option == "Yearly" and date.month == 12:
            current_weights = w.copy()
        else:
            # 리밸런싱 안 할 때는 변화된 가치 비중 유지
            current_weights = asset_values / port_ret
            
    return pd.Series(portfolio_values, index=returns.index)
