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


def load_monthly_returns(tickers, interval="1mo"):
    all_data = []
    
    for ticker in tickers:
        try:
            # 1. 데이터 로드 (interval 반영)
            asset_obj = yf.download(ticker, start="1980-01-01", interval=interval, progress=False, auto_adjust=True)
            if asset_obj.empty: continue
            
            # 가격 추출
            asset_price = asset_obj['Close'][ticker] if isinstance(asset_obj['Close'], pd.DataFrame) else asset_obj['Close']
            
            # [날짜 처리]
            if interval == "1mo":
                # 월간일 때는 말일로 통일 (글로벌 지수 정렬용)
                asset_price.index = asset_price.index.to_period('M').to_timestamp('M')
            
            # 중복 날짜 제거
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
    
    # 3. 데이터 병합 (모든 자산 정렬)
    df = pd.concat(all_data, axis=1)
    
    # 일간 데이터일 경우 빈 날짜(휴장일 등)는 ffill로 메꿔서 계산 오류 방지
    if interval == "1d":
        df = df.fillna(0) # 수익률이므로 빈 날은 0%
    else:
        df = df.dropna(how='all').fillna(0)
        
    return df
