import yfinance as yf
import pandas as pd

# 1. 지수 매핑 DB (한국 및 글로벌 핵심 지수)
# 1. 한국 및 글로벌 지수 매핑 DB (레버리지 및 배당주 보강)
PROSPECTUS_DB = {
    # --- 미국 대표 시장 지수 ---
    "SPY": "^GSPC", "IVV": "^GSPC", "VOO": "^GSPC", "SPLG": "^GSPC",
    "QQQ": "^NDX", "QQQM": "^NDX", "TQQQ": "^NDX", "QLD": "^NDX",     # 나스닥 레버리지 포함
    "DIA": "^DJI",
    "IWM": "^RUT",
    
    # --- 반도체 & 테크 (한국인 최애) ---
    "SOXX": "^SOX", "SOXQ": "^SOX", "SMH": "^SOX",
    "SOXL": "^SOX", "SOXS": "^SOX",                                 # 반도체 레버리지
    "VGT": "^NDX", "XLK": "^GSPC",
    
    # --- 배당 및 가치주 (정밀 매핑) ---
    "SCHD": "^DJUSD100", 
    "VIG": "^DJUSD", "DGRO": "^DJUSD",                              # 배당성장 지수 대용
    "VYM": "^VYM",                                                  # 고배당 지수
    
    # --- 한국 시장 및 국내상장 ETF ---
    "069500.KS": "^KS11", "102110.KS": "^KS11", "102780.KQ": "^KQ11",
    "133690.KS": "^NDX", "379800.KS": "^NDX",                       # 나스닥100 (국내)
    "360750.KS": "^GSPC", "446550.KS": "^DJUSD100",                 # S&P500, 배당다우존스 (국내)
    "402970.KS": "^SOX",                                            # 필반나 (국내)
    
    # --- 채권 및 안전자산 ---
    "TLT": "^TYX", "TMF": "^TYX", "EDV": "^TYX",                    # 장기채 (30년물 금리 기반)
    "IEF": "^TNX", "TYD": "^TNX",                                   # 중기채 (10년물 금리 기반)
    "GLD": "GC=F", "IAU": "GC=F", "SLV": "SI=F",                    # 금, 은 선물
    "BTC-USD": "BTC-USD"                                            # 비트코인은 그대로
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
