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
            # 1. 데이터 로드
            asset_obj = yf.download(ticker, start="1980-01-01", interval="1mo", progress=False, auto_adjust=True)
            if asset_obj.empty: continue
            
            # 컬럼 추출 (멀티인덱스 대응)
            asset_price = asset_obj['Close'][ticker] if isinstance(asset_obj['Close'], pd.DataFrame) else asset_obj['Close']
            
            # [수정 핵심] 날짜 인덱스를 해당 월의 마지막 날로 통일하고 중복 제거
            asset_price.index = asset_price.index.to_period('M').to_timestamp('M')
            asset_price = asset_price[~asset_price.index.duplicated(keep='last')]
            
            asset_raw = asset_price.pct_change()

            # 2. 스마트 백필링
            if ticker in PROSPECTUS_DB:
                bench_ticker = PROSPECTUS_DB[ticker]
                bench_obj = yf.download(bench_ticker, start="1980-01-01", interval="1mo", progress=False, auto_adjust=True)
                
                if not bench_obj.empty:
                    bench_price = bench_obj['Close'][bench_ticker] if isinstance(bench_obj['Close'], pd.DataFrame) else bench_obj['Close']
                    # 지수 날짜도 동일하게 통일
                    bench_price.index = bench_price.index.to_period('M').to_timestamp('M')
                    bench_price = bench_price[~bench_price.index.duplicated(keep='last')]
                    
                    bench_raw = bench_price.pct_change()
                    
                    first_date = asset_raw.first_valid_index()
                    if first_date:
                        bench_before = bench_raw[bench_raw.index < first_date]
                        asset_raw = pd.concat([bench_before, asset_raw])
                        # 합친 후 다시 한번 날짜 정리
                        asset_raw = asset_raw[~asset_raw.index.duplicated(keep='last')]
            
            asset_raw.name = ticker
            all_data.append(asset_raw)
            
        except Exception as e:
            print(f"{ticker} 에러: {e}")
            continue
    
    if not all_data: return pd.DataFrame()
    
    # 3. 데이터 병합 (모든 자산의 날짜를 맞춤)
    df = pd.concat(all_data, axis=1)
    return df.dropna(how='all').fillna(0)
