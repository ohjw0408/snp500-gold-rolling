import pandas as pd
import numpy as np

def backtest(returns, weights, rebalance_option="Monthly"):
    # 비중을 Series로 변환
    w = pd.Series(weights)
    
    # 포트폴리오 가치를 저장할 Series (시작값 1.0)
    portfolio_value = [1.0]
    current_weights = w.copy()
    
    # 날짜별로 루프를 돌며 계산
    for i in range(len(returns)):
        # 1. 이번 달 수익률 적용
        month_return = returns.iloc[i]
        
        # 자산별 가치 변화 반영
        asset_values = current_weights * (1 + month_return)
        total_value = asset_values.sum()
        
        # 전체 포트폴리오 수익률 반영
        portfolio_value.append(portfolio_value[-1] * total_value)
        
        # 2. 리밸런싱 체크
        # 자산별 비중이 수익률에 따라 변함
        current_weights = asset_values / total_value
        
        # 리밸런싱 시점이라면 비중을 다시 초기 설정값(w)으로 리셋
        if rebalance_option == "Monthly":
            # 매월 리밸런싱
            current_weights = w.copy()
        elif rebalance_option == "Yearly":
            # 12월(또는 1년의 마지막 달)에만 리밸런싱
            if returns.index[i].month == 12:
                current_weights = w.copy()
        # "None" 옵션이 있다면 current_weights를 그대로 유지 (리밸런싱 안함)

    # 결과 반환 (시작일 인덱스 맞춰주기)
    result = pd.Series(portfolio_value[1:], index=returns.index)
    return result
