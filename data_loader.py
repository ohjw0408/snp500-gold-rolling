import yfinance as yf
import pandas as pd

# 1. 한국 투자자가 가장 선호하는 자산군/지수 매핑 DB
PROSPECTUS_DB = {
    # --- 미국 4대 시장 지수 ---
    "SPY": "^GSPC", "IVV": "^GSPC", "VOO": "^GSPC", "SPLG": "^GSPC", # S&P 500
    "QQQ": "^NDX", "QQQM": "^NDX",                                  # Nasdaq 100
    "DIA": "^DJI",                                                  # Dow Jones Industrial
    "IWM": "^RUT", "VTWO": "^RUT",                                  # Russell 2000 (중소형주)
    
    # --- 반도체 & 테크 (한국인 최애) ---
    "SOXX": "^SOX", "SOXQ": "^SOX", "SMH": "^SOX",                  # 필라델피아 반도체 지수
    "VGT": "MSCI.IT", "XLK": "MSCI.IT",                             # 미국 테크 섹터
    
    # --- 배당 및 가치주 ---
    "SCHD": "^DJUSD100",                                            # Dow Jones US Dividend 100
    "VIG": "^@VIG", "DGRO": "^@DGRO",                               # 배당성장 지수 (대용치 연결 필요)
    
    # --- 채권 (안전 자산) ---
    "TLT": "^TYX", "EDV": "^TYX", "TMF": "^TYX",                    # 미국 30년 국채 (금리 지수 활용)
    "IEF": "^TNX",                                                  # 미국 10년 국채
    "SHY": "^FVX",                                                  # 미국 5년 단기채
    
    # --- 원자재 및 기타 ---
    "GLD": "GC=F", "IAU": "GC=F",                                   # 금 선물
    "SLV": "SI=F",                                                  # 은 선물
    "USO": "CL=F",                                                  # 원유 선물
    
    # --- 해외(미국외) 지수 ---
    "VEA": "^MSDEUPX",                                              # 선진국 지수
    "VWO": "^MSEMGFX",                                              # 신흥국 지수
}

def load_monthly_returns(tickers):
    all_data = []
    
    for ticker in tickers:
        # 1. 원본 ETF 데이터 로드
        asset_obj = yf.download(ticker, start="1900-01-01", interval="1mo")
        if asset_obj.empty: continue
        
        asset_raw = asset_obj['Adj Close'].pct_change()
        
        # 2. 스마트 백필링 로직
        if ticker in PROSPECTUS_DB:
            bench_ticker = PROSPECTUS_DB[ticker]
            # 지수 데이터는 최대한 먼 과거부터 가져옴
            bench_obj = yf.download(bench_ticker, start="1900-01-01", interval="1mo")
            
            if not bench_obj.empty:
                bench_raw = bench_obj['Adj Close'].pct_change()
                first_valid_date = asset_raw.first_valid_index()
                
                if first_valid_date:
                    # 상장 전 구간은 지수 수익률로 채움
                    bench_before = bench_raw[bench_raw.index < first_valid_date]
                    asset_raw = pd.concat([bench_before, asset_raw])
        
        asset_raw.name = ticker
        all_data.append(asset_raw)
    
    if not all_data: return pd.DataFrame()
    
    # 모든 데이터를 합치고 데이터가 하나라도 존재하는 시점부터 시작
    df = pd.concat(all_data, axis=1)
    return df.dropna(how='all').fillna(0)
