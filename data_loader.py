import yfinance as yf
import pandas as pd

# 1. 한국 투자자 선호 지수 및 ETF 매핑 DB
PROSPECTUS_DB = {
    # 시장 지수
    "SPY": "^GSPC", "IVV": "^GSPC", "VOO": "^GSPC", "SPLG": "^GSPC",
    "QQQ": "^NDX", "QQQM": "^NDX",
    "DIA": "^DJI",
    "IWM": "^RUT", "VTWO": "^RUT",
    
    # 반도체 및 테크 (필라델피아 반도체 포함)
    "SOXX": "^SOX", "SOXQ": "^SOX", "SMH": "^SOX",
    "VGT": "^NDX", "XLK": "^GSPC", # 섹터 지수 대용
    
    # 배당주 (SCHD 등)
    "SCHD": "^DJUSD100",
    "VIG": "^GSPC", "DGRO": "^GSPC",
    
    # 채권 및 원자재
    "TLT": "^TYX", "TMF": "^TYX",
    "IEF": "^TNX",
    "GLD": "GC=F", "IAU": "GC=F",
    "SLV": "SI=F"
}

def load_monthly_returns(tickers):
    all_data = []
    
    for ticker in tickers:
        try:
            # 1. 데이터 로드 (월간 단위)
            asset_obj = yf.download(ticker, start="1970-01-01", interval="1mo", progress=False)
            if asset_obj.empty: continue
            
            # [에러 해결 핵심] 최근 yfinance의 멀티인덱스 구조 대응
            if isinstance(asset_obj.columns, pd.MultiIndex):
                asset_price = asset_obj['Adj Close'][ticker]
            else:
                asset_price = asset_obj['Adj Close']
            
            asset_raw = asset_price.pct_change()

            # 2. 스마트 백필링
            if ticker in PROSPECTUS_DB:
                bench_ticker = PROSPECTUS_DB[ticker]
                bench_obj = yf.download(bench_ticker, start="1970-01-01", interval="1mo", progress=False)
                
                if not bench_obj.empty:
                    # 지수 데이터 컬럼 선택
                    if isinstance(bench_obj.columns, pd.MultiIndex):
                        bench_price = bench_obj['Adj Close'][bench_ticker]
                    else:
                        bench_price = bench_obj['Adj Close']
                        
                    bench_raw = bench_price.pct_change()
                    
                    # ETF 상장 전 데이터 합치기
                    first_date = asset_raw.first_valid_index()
                    if first_date:
                        bench_before = bench_raw[bench_raw.index < first_date]
                        asset_raw = pd.concat([bench_before, asset_raw])
            
            asset_raw.name = ticker
            all_data.append(asset_raw)
            
        except Exception as e:
            print(f"{ticker} 데이터 처리 중 오류: {e}")
            continue
    
    if not all_data: return pd.DataFrame()
    
    # 데이터 병합 및 정리
    df = pd.concat(all_data, axis=1)
    return df.dropna(how='all').fillna(0)
