import yfinance as yf
import pandas as pd

# 1. 마스터 DB (사용자 설정 유지)
PROSPECTUS_DB = {
    "SPY": {"bench": "^GSPC", "unhedged": True}, 
    "IVV": {"bench": "^GSPC", "unhedged": True},
    "VOO": {"bench": "^GSPC", "unhedged": True},
    "QQQ": {"bench": "^NDX", "unhedged": True},
    "QQQM": {"bench": "^NDX", "unhedged": True},
    "TQQQ": {"bench": "^NDX", "unhedged": True},
    "SCHD": {"bench": "^DJUSD100", "unhedged": True},
    "DIA": {"bench": "^DJI", "unhedged": True},
    "IWM": {"bench": "^RUT", "unhedged": True},
    "SOXX": {"bench": "^SOX", "unhedged": True},
    "SMH": {"bench": "^SOX", "unhedged": True},
    "SOXL": {"bench": "^SOX", "unhedged": True},
    "VGT": {"bench": "^NDX", "unhedged": True},
    "XLK": {"bench": "^GSPC", "unhedged": True},
    "VIG": {"bench": "^DJUSD", "unhedged": True},
    "DGRO": {"bench": "^DJUSD", "unhedged": True},
    "360750.KS": {"bench": "^GSPC", "unhedged": True},
    "133690.KS": {"bench": "^NDX", "unhedged": True},
    "446550.KS": {"bench": "^DJUSD100", "unhedged": True},
    "458730.KS": {"bench": "^DJUSD100", "unhedged": True},
    "402970.KS": {"bench": "^SOX", "unhedged": True},
    "441680.KS": {"bench": "^GSPC", "unhedged": False},
    "441670.KS": {"bench": "^NDX", "unhedged": False},
    "461580.KS": {"bench": "^DJUSD100", "unhedged": False},
    "069500.KS": {"bench": "^KS11", "unhedged": False},
    "102110.KS": {"bench": "^KS11", "unhedged": False},
    "102780.KS": {"bench": "^KQ11", "unhedged": False},
    "226490.KS": {"bench": "^KS11", "unhedged": False},
    "TLT": {"bench": "^TYX", "unhedged": True},
    "TMF": {"bench": "^TYX", "unhedged": True},
    "IEF": {"bench": "^TNX", "unhedged": True},
    "GLD": {"bench": "GC=F", "unhedged": True},
    "BTC-USD": {"bench": "BTC-USD", "unhedged": True}
}

def load_monthly_returns(tickers, interval="1mo"):
    # 0. 환율 데이터 미리 준비 (환노출 자산 계산용)
    fx_obj = yf.download("USDKRW=X", start="1900-01-01", interval=interval, progress=False, auto_adjust=True)
    fx_price = fx_obj['Close']
    if interval == "1mo":
        fx_price.index = fx_price.index.to_period('M').to_timestamp('M')
    fx_ret = fx_price[~fx_price.index.duplicated(keep='last')].pct_change().fillna(0)

    all_data = []
    for ticker in tickers:
        try:
            # 자산 데이터 로드
            asset_obj = yf.download(ticker, start="1900-01-01", interval=interval, progress=False, auto_adjust=True)
            if asset_obj.empty: continue
            
            asset_price = asset_obj['Close'][ticker] if isinstance(asset_obj['Close'], pd.DataFrame) else asset_obj['Close']
            if interval == "1mo":
                asset_price.index = asset_price.index.to_period('M').to_timestamp('M')
            
            asset_price = asset_price[~asset_price.index.duplicated(keep='last')].ffill()
            asset_raw_ret = asset_price.pct_change().fillna(0)

            # 스마트 백필링 로직
            is_unhedged = True # 기본값
            if ticker in PROSPECTUS_DB:
                info = PROSPECTUS_DB[ticker]
                bench_ticker = info["bench"] # 딕셔너리에서 티커 문자열만 추출
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

            # 환율 적용 (환노출 자산일 경우)
            if is_unhedged:
                # 자산 날짜에 맞춰 환율 수익률 매칭
                target_fx = fx_ret.reindex(asset_raw_ret.index).ffill().fillna(0)
                asset_final_ret = (1 + asset_raw_ret) * (1 + target_fx) - 1
            else:
                asset_final_ret = asset_raw_ret
            
            asset_final_ret.name = ticker
            all_data.append(asset_final_ret)
            
        except Exception as e:
            continue
    
    if not all_data: return pd.DataFrame()
    
    df = pd.concat(all_data, axis=1).fillna(0)
    return df[~df.index.duplicated(keep='last')]
