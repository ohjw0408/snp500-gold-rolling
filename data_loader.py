import yfinance as yf
import pandas as pd

# 1. 지수 매핑 DB (한국 및 글로벌 핵심 지수)
# 1. 한국 및 글로벌 지수 매핑 DB (레버리지 및 배당주 보강)
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

# [핵심] interval 인자를 받을 수 있도록 함수 정의를 수정했습니다.
def load_monthly_returns(tickers, interval="1mo"):
    all_data = []
    
    for ticker in tickers:
        try:
            # 1. 원본 데이터 로드
            asset_obj = yf.download(ticker, start="1980-01-01", interval=interval, progress=False, auto_adjust=True)
            if asset_obj.empty: continue
            
            # 멀티인덱스 여부에 따라 가격 추출
            asset_price = asset_obj['Close'][ticker] if isinstance(asset_obj['Close'], pd.DataFrame) else asset_obj['Close']
            
            # 날짜 정규화 (월간 모드일 때만 말일로 통일)
            if interval == "1mo":
                asset_price.index = asset_price.index.to_period('M').to_timestamp('M')
            
            asset_price = asset_price[~asset_price.index.duplicated(keep='last')]
            asset_raw = asset_price.pct_change()

            # 2. 스마트 백필링
            if ticker in PROSPECTUS_DB:
                bench_ticker = PROSPECTUS_DB[ticker]
                bench_obj = yf.download(bench_ticker, start="1980-01-01", interval=interval, progress=False, auto_adjust=True)
                
                if not bench_obj.empty:
                    bench_price = bench_obj['Close'][bench_ticker] if isinstance(bench_obj['Close'], pd.DataFrame) else bench_obj['Close']
                    if interval == "1mo":
                        bench_price.index = bench_price.index.to_period('M').to_timestamp('M')
                    
                    bench_price = bench_price[~bench_price.index.duplicated(keep='last')]
                    bench_raw = bench_price.pct_change()
                    
                    first_date = asset_raw.first_valid_index()
                    if first_date:
                        bench_before = bench_raw[bench_raw.index < first_date]
                        asset_raw = pd.concat([bench_before, asset_raw])
                        asset_raw = asset_raw[~asset_raw.index.duplicated(keep='last')]
            
            asset_raw.name = ticker
            all_data.append(asset_raw)
            
        except Exception as e:
            continue
    
    if not all_data: return pd.DataFrame()
    
    # 데이터 병합
    df = pd.concat(all_data, axis=1)
    
    if interval == "1d":
        df = df.fillna(0) # 일간 데이터 빈 날짜 처리
    else:
        df = df.dropna(how='all').fillna(0)
        
    return df
