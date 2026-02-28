import yfinance as yf
import pandas as pd

# 1. 지수 매핑 및 환노출 설정 (is_unhedged: True면 환노출, False면 환헤지/국내자산)
# 1. 한국 및 글로벌 지수 매핑 및 환노출 설정 마스터 DB
# unhedged: True (달러 환율 변동 반영), False (환헤지 또는 국내 지수)
PROSPECTUS_DB = {
    # --- [미국 상장] 대표 지수 및 배당 (환노출) ---
    "SPY": {"bench": "^GSPC", "unhedged": True}, 
    "IVV": {"bench": "^GSPC", "unhedged": True},
    "VOO": {"bench": "^GSPC", "unhedged": True},
    "QQQ": {"bench": "^NDX", "unhedged": True},
    "QQQM": {"bench": "^NDX", "unhedged": True},
    "TQQQ": {"bench": "^NDX", "unhedged": True},
    "SCHD": {"bench": "^DJUSD100", "unhedged": True},
    "DIA": {"bench": "^DJI", "unhedged": True},
    "IWM": {"bench": "^RUT", "unhedged": True},

    # --- [미국 상장] 섹터 및 레버리지 (환노출) ---
    "SOXX": {"bench": "^SOX", "unhedged": True},
    "SMH": {"bench": "^SOX", "unhedged": True},
    "SOXL": {"bench": "^SOX", "unhedged": True},
    "VGT": {"bench": "^NDX", "unhedged": True},
    "XLK": {"bench": "^GSPC", "unhedged": True},
    "VIG": {"bench": "^DJUSD", "unhedged": True},
    "DGRO": {"bench": "^DJUSD", "unhedged": True},

    # --- [한국 상장] 미국 지수 시리즈 (환노출형) ---
    "360750.KS": {"bench": "^GSPC", "unhedged": True}, # TIGER 미국S&P500
    "133690.KS": {"bench": "^NDX", "unhedged": True},  # TIGER 미국나스닥100
    "446550.KS": {"bench": "^DJUSD100", "unhedged": True}, # ACE 미국배당다우존스
    "458730.KS": {"bench": "^DJUSD100", "unhedged": True}, # TIGER 미국배당다우존스
    "402970.KS": {"bench": "^SOX", "unhedged": True},  # TIGER 미국필라델피아반도체나스닥
    
    # --- [한국 상장] 미국 지수 시리즈 (환헤지형 - H) ---
    "441680.KS": {"bench": "^GSPC", "unhedged": False}, # TIGER 미국S&P500(H)
    "441670.KS": {"bench": "^NDX", "unhedged": False},  # TIGER 미국나스닥100(H)
    "461580.KS": {"bench": "^DJUSD100", "unhedged": False}, # SOL 미국배당다우존스(H)

    # --- [국내 자산] 코스피/코스닥 및 기타 ---
    "069500.KS": {"bench": "^KS11", "unhedged": False}, # KODEX 200
    "102110.KS": {"bench": "^KS11", "unhedged": False}, # TIGER 200
    "102780.KS": {"bench": "^KQ11", "unhedged": False}, # KODEX 코스닥150
    "226490.KS": {"bench": "^KS11", "unhedged": False}, # KODEX 코스피

    # --- [안전 자산] 채권 및 원자재 ---
    "TLT": {"bench": "^TYX", "unhedged": True},   # 미국 장기채 (환노출)
    "TMF": {"bench": "^TYX", "unhedged": True},   # 미국 장기채 3배 (환노출)
    "IEF": {"bench": "^TNX", "unhedged": True},   # 미국 중기채 (환노출)
    "GLD": {"bench": "GC=F", "unhedged": True},   # 금 (환노출)
    "BTC-USD": {"bench": "BTC-USD", "unhedged": True} # 비트코인 (달러기준 환노출)
}

def load_monthly_returns(tickers, interval="1mo"):
    # 0. 환율 데이터 로드 (시작 날짜를 1900년으로 수정)
    fx_obj = yf.download("USDKRW=X", start="1900-01-01", interval=interval, progress=False, auto_adjust=True)
    fx_price = fx_obj['Close']
    
    if interval == "1mo":
        fx_price.index = fx_price.index.to_period('M').to_timestamp('M')
    
    # 중복 제거 및 수익률 변환
    fx_price = fx_price[~fx_price.index.duplicated(keep='last')].ffill()
    fx_ret = fx_price.pct_change().fillna(0)

    all_data = []
    for ticker in tickers:
        try:
            # 자산 데이터 로드 (시작 날짜를 1900년으로 수정)
            asset_obj = yf.download(ticker, start="1900-01-01", interval=interval, progress=False, auto_adjust=True)
            if asset_obj.empty: continue
            
            asset_price = asset_obj['Close'][ticker] if isinstance(asset_obj['Close'], pd.DataFrame) else asset_obj['Close']
            
            if interval == "1mo":
                asset_price.index = asset_price.index.to_period('M').to_timestamp('M')
            
            asset_price = asset_price[~asset_price.index.duplicated(keep='last')].ffill()
            asset_raw_ret = asset_price.pct_change().fillna(0)

            # 벤치마크 백필링 (시작 날짜 1900년 적용)
            if ticker in PROSPECTUS_DB:
                info = PROSPECTUS_DB[ticker]
                bench_ticker = info["bench"]
                is_unhedged = info["unhedged"]
                
                bench_obj = yf.download(bench_ticker, start="1900-01-01", interval=interval, progress=False, auto_adjust=True)
                if not bench_obj.empty:
                    bench_price = bench_obj['Close'][bench_ticker] if isinstance(bench_obj['Close'], pd.DataFrame) else bench_obj['Close']
                    if interval == "1mo": 
                        bench_price.index = bench_price.index.to_period('M').to_timestamp('M')
                    
                    bench_price = bench_price[~bench_price.index.duplicated(keep='last')].ffill()
                    bench_raw_ret = bench_price.pct_change().fillna(0)
                    
                    first_date = asset_raw_ret.first_valid_index()
                    if first_date:
                        bench_before = bench_raw_ret[bench_raw_ret.index < first_date]
                        asset_raw_ret = pd.concat([bench_before, asset_raw_ret])
                        asset_raw_ret = asset_raw_ret[~asset_raw_ret.index.duplicated(keep='last')]

            # 원화 수익률 합성
            is_unhedged = PROSPECTUS_DB.get(ticker, {}).get("unhedged", True)
            if is_unhedged:
                clean_fx_ret = fx_ret[~fx_ret.index.duplicated(keep='last')]
                target_fx_ret = clean_fx_ret.reindex(asset_raw_ret.index).ffill().fillna(0)
                asset_final_ret = (1 + asset_raw_ret) * (1 + target_fx_ret) - 1
            else:
                asset_final_ret = asset_raw_ret
            
            asset_final_ret.name = ticker
            all_data.append(asset_final_ret)
        except: continue
    
    if not all_data: return pd.DataFrame()
    return pd.concat(all_data, axis=1).fillna(0)
🛠️ 2. portfolio.py 수정 (수치 안정화)
데이터가 없는 구간이 0으로 처리되어 자산 가치가 소멸하는 것을 방지하는 안전장치를 강화했습니다.

Python
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
