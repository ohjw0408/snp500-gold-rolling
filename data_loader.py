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
    all_data = []
    
    # [수정] 환율 데이터 미리 로드 (환노출 계산용)
    fx = yf.download("USDKRW=X", start="1980-01-01", interval=interval, progress=False, auto_adjust=True)['Close']
    if interval == "1mo":
        fx.index = fx.index.to_period('M').to_timestamp('M')
    fx_ret = fx[~fx.index.duplicated(keep='last')].pct_change().fillna(0)

    for ticker in tickers:
        try:
            asset_obj = yf.download(ticker, start="1980-01-01", interval=interval, progress=False, auto_adjust=True)
            if asset_obj.empty: continue
            
            asset_price = asset_obj['Close'][ticker] if isinstance(asset_obj['Close'], pd.DataFrame) else asset_obj['Close']
            if interval == "1mo":
                asset_price.index = asset_price.index.to_period('M').to_timestamp('M')
            
            asset_price = asset_price[~asset_price.index.duplicated(keep='last')]
            asset_raw = asset_price.pct_change().fillna(0)

            # [수정] 딕셔너리 구조에서 bench 티커 추출
            is_unhedged = True
            if ticker in PROSPECTUS_DB:
                info = PROSPECTUS_DB[ticker]
                bench_ticker = info["bench"] # 딕셔너리에서 값 추출
                is_unhedged = info["unhedged"]
                
                bench_obj = yf.download(bench_ticker, start="1980-01-01", interval=interval, progress=False, auto_adjust=True)
                if not bench_obj.empty:
                    bench_price = bench_obj['Close'][bench_ticker] if isinstance(bench_obj['Close'], pd.DataFrame) else bench_obj['Close']
                    if interval == "1mo":
                        bench_price.index = bench_price.index.to_period('M').to_timestamp('M')
                    
                    bench_price = bench_price[~bench_price.index.duplicated(keep='last')]
                    bench_raw = bench_price.pct_change().fillna(0)
                    
                    first_date = asset_raw.first_valid_index()
                    if first_date:
                        bench_before = bench_raw[bench_raw.index < first_date]
                        asset_raw = pd.concat([bench_before, asset_raw])
                        asset_raw = asset_raw[~asset_raw.index.duplicated(keep='last')]

            # [추가] 환노출 반영 (원화 수익률 계산)
            if is_unhedged:
                # 환율 데이터를 자산 날짜에 맞춤
                target_fx = fx_ret.reindex(asset_raw.index).ffill().fillna(0)
                asset_raw = (1 + asset_raw) * (1 + target_fx) - 1
            
            asset_raw.name = ticker
            all_data.append(asset_raw)
            
        except: continue
    
    if not all_data: return pd.DataFrame()
    
    # 최종 병합
    df = pd.concat(all_data, axis=1).fillna(0)
    return df[~df.index.duplicated(keep='last')]
