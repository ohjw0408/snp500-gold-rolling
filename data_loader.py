import yfinance as yf
import pandas as pd

# 1. 한국 및 글로벌 핵심 지수 매핑 DB
PROSPECTUS_DB = {
    # --- 한국 시장 (KOREA) ---
    "069500.KS": "^KS11", "102110.KS": "^KS11",    # KODEX 200, TIGER 200 -> 코스피 지수
    "226490.KS": "^KS11",                         # KODEX 코스피
    "153130.KS": "^KS11",                         # KODEX 단기채권 (지수 대용)
    "102780.KS": "^KQ11",                         # KODEX 코스닥150 -> 코스닥 지수
    
    # --- 국내 상장 미국 ETF (한국인이 많이 사는 것) ---
    "133690.KS": "^NDX", "379800.KS": "^NDX",    # TIGER 미국나스닥100 -> 나스닥100 지수
    "360750.KS": "^GSPC", "364980.KS": "^GSPC",   # TIGER 미국S&P500 -> S&P 500 지수
    "402970.KS": "^SOX",                         # TIGER 미국필라델피아반도체나스닥 -> SOX 지수
    "446550.KS": "^DJUSD100",                    # ACE 미국배당다우존스 -> SCHD 지수
    
    # --- 미국 시장 대표 지수 ---
    "SPY": "^GSPC", "IVV": "^GSPC", "VOO": "^GSPC",
    "QQQ": "^NDX", "QQQM": "^NDX",
    "DIA": "^DJI",
    "IWM": "^RUT",
    
    # --- 반도체 & 테크 ---
    "SOXX": "^SOX", "SOXQ": "^SOX", "SMH": "^SOX",
    
    # --- 배당 및 채권 ---
    "SCHD": "^DJUSD100",
    "TLT": "^TYX", "TMF": "^TYX", "IEF": "^TNX",
    
    # --- 원자재 ---
    "GLD": "GC=F", "IAU": "GC=F", "SLV": "SI=F"
}

def load_monthly_returns(tickers):
    all_data = []
    
    for ticker in tickers:
        try:
            # 1. 원본 데이터 로드 (월간 단위)
            # 한국 종목의 경우 티커 끝에 .KS(코스피) 또는 .KQ(코스닥)가 붙어야 합니다.
            asset_obj = yf.download(ticker, start="1980-01-01", interval="1mo", progress=False, auto_adjust=True)
            if asset_obj.empty: continue
            
            # 멀티인덱스 여부에 따라 데이터 추출
            if 'Close' in asset_obj.columns:
                asset_price = asset_obj['Close']
                if isinstance(asset_price, pd.DataFrame):
                    asset_price = asset_price[ticker]
            else:
                continue
            
            asset_raw = asset_price.pct_change()

            # 2. 스마트 백필링
            if ticker in PROSPECTUS_DB:
                bench_ticker = PROSPECTUS_DB[ticker]
                bench_obj = yf.download(bench_ticker, start="1980-01-01", interval="1mo", progress=False, auto_adjust=True)
                
                if not bench_obj.empty and 'Close' in bench_obj.columns:
                    bench_price = bench_obj['Close']
                    if isinstance(bench_price, pd.DataFrame):
                        bench_price = bench_price[bench_ticker]
                        
                    bench_raw = bench_price.pct_change()
                    
                    # ETF 상장 전 구간을 지수 데이터로 메꿈
                    first_date = asset_raw.first_valid_index()
                    if first_date:
                        bench_before = bench_raw[bench_raw.index < first_date]
                        asset_raw = pd.concat([bench_before, asset_raw])
            
            asset_raw.name = ticker
            all_data.append(asset_raw)
            
        except Exception as e:
            print(f"{ticker} 처리 중 오류: {e}")
            continue
    
    if not all_data: return pd.DataFrame()
    
    # 데이터 병합 및 정리
    df = pd.concat(all_data, axis=1)
    return df.dropna(how='all').fillna(0)
