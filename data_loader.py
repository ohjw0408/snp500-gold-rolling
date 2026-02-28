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
    # 0. 환율 데이터
    fx_obj = yf.download("USDKRW=X", start="1980-01-01", interval=interval, progress=False, auto_adjust=True)
    fx_price = fx_obj['Close']
    if interval == "1mo":
        fx_price.index = fx_price.index.to_period('M').to_timestamp('M')
    fx_price = fx_price[~fx_price.index.duplicated(keep='last')].ffill()
    fx_ret = fx_price.pct_change().fillna(0) # 반드시 수익률로 변환!

    all_data = []
    for ticker in tickers:
        try:
            asset_obj = yf.download(ticker, start="1980-01-01", interval=interval, progress=False, auto_adjust=True)
            if asset_obj.empty: continue
            
            # 가격 데이터 추출
            asset_price = asset_obj['Close'][ticker] if isinstance(asset_obj['Close'], pd.DataFrame) else asset_obj['Close']
            if interval == "1mo":
                asset_price.index = asset_price.index.to_period('M').to_timestamp('M')
            
            # 중복 제거 및 수익률 변환
            asset_price = asset_price[~asset_price.index.duplicated(keep='last')].ffill()
            asset_raw_ret = asset_price.pct_change() # 여기서 수익률로 바뀜!

            # [보정] 첫 번째 행의 NaN 제거
            asset_raw_ret = asset_raw_ret.fillna(0)

            # (백필링 로직은 기존과 동일하되, concat 후 다시 중복 제거 필수)
            # ... 생략 ...

            # 원화 수익률 합성
            is_unhedged = PROSPECTUS_DB.get(ticker, {}).get("unhedged", True)
            if is_unhedged:
                # 환율 수익률을 자산 날짜에 맞춤
                target_fx_ret = fx_ret.reindex(asset_raw_ret.index).ffill().fillna(0)
                asset_final_ret = (1 + asset_raw_ret) * (1 + target_fx_ret) - 1
            else:
                asset_final_ret = asset_raw_ret
            
            asset_final_ret.name = ticker
            all_data.append(asset_final_ret)
        except: continue
    
    if not all_data: return pd.DataFrame()
    return pd.concat(all_data, axis=1).fillna(0)
