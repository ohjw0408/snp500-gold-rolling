import pandas as pd

def backtest(returns, weights, rebalance_option):
    # 초기 설정
    portfolio_value = 1.0
    values = []
    
    # 날짜별로 루프를 돌며 수익률 계산
    for date, row in returns.iterrows():
        # 1. 현재 날짜에 데이터가 있는 자산들만 필터링
        available_assets = row.dropna().index
        if len(available_assets) == 0:
            values.append(portfolio_value)
            continue
            
        # 2. 이용 가능한 자산들의 설정 비중 합계 계산
        current_weights = {t: weights[t] for t in available_assets}
        total_w = sum(current_weights.values())
        
        # 3. 비중 재분배 (비중 합이 1이 되도록 조정)
        # 예: 원래 주식 50:비트 50인데 비트가 없으면 주식 100으로 계산
        if total_w > 0:
            normalized_weights = {t: w / total_w for t, w in current_weights.items()}
        else:
            values.append(portfolio_value)
            continue
            
        # 4. 해당 달의 포트폴리오 수익률 계산
        day_return = 0
        for ticker in available_assets:
            day_return += row[ticker] * normalized_weights[ticker]
            
        portfolio_value *= (1 + day_return)
        values.append(portfolio_value)
        
    return pd.Series(values, index=returns.index)
