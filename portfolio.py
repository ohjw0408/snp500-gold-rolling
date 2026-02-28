import pandas as pd
import numpy as np

def backtest(returns, weights, rebalance_option="Monthly"):
    # 1. 데이터 클리닝: 수익률 데이터에 NaN이 있으면 0(수익률 없음)으로 채움
    returns = returns.fillna(0)
    
    # 2. 비중 설정
    w = pd.Series(weights)
    
    # 포트폴리오 가치 추적 (초기값 1.0)
    portfolio_values = []
    current_val = 1.0
    
    # 초기 비중 세팅
    current_weights = w.copy()
    
    for date, monthly_ret in returns.iterrows():
        # 자산별 수익 반영 (가치 = 이전비중 * (1 + 수익률))
        # 만약 monthly_ret이 '가격'이라면 여기서 엄청난 숫자가 나옴
        asset_values = current_weights * (1 + monthly_ret)
        
        # 이번 달 포트폴리오 전체 수익률
        port_ret = asset_values.sum()
        
        # 포트폴리오 총 가치 갱신
        current_val *= port_ret
        portfolio_values.append(current_val)
        
        # 리밸런싱 로직
        if rebalance_option == "Monthly":
            current_weights = w.copy()
        elif rebalance_option == "Yearly":
            if date.month == 12:
                current_weights = w.copy()
            else:
                # 리밸런싱 안 할 때는 자산 가치 변화에 따라 비중 업데이트
                current_weights = asset_values / port_ret
        else: # 리밸런싱 없음
            current_weights = asset_values / port_ret
            
    return pd.Series(portfolio_values, index=returns.index)
