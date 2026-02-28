import yfinance as yf
import pandas as pd

# 1. 프로그램 내부의 지수 매핑 사전 (사용자에게는 숨겨짐)
# 주요 ETF들이 추종하는 '인덱스'의 야후 파이낸스 티커들을 정리해두었습니다.
PROSPECTUS_DB = {
    "SCHD": "^DJUSD100",  # Dow Jones U.S. Dividend 100 Index
    "SPY": "^GSPC",       # S&P 500
    "IVV": "^GSPC",
    "VOO": "^GSPC",
    "QQQ": "^NDX",        # Nasdaq 100
    "DIA": "^DJI",        # Dow Jones Industrial Average
    "IWM": "^RUT",        # Russell 2000
    "VEA": "^MSDEUPX",    # MSCI EAFE (유럽/아시아 선진국)
    "VWO": "^MSEMGFX",    # MSCI Emerging Markets
    "GLD": "GC=F",        # Gold Futures
    "TLT": "^TYX",        # 30Y Treasury (대용치)
}

def load_monthly_returns(tickers):
    all_data = []
    
    for ticker in tickers:
        # 1. ETF/주식 본래 데이터 로드
        # 상장일부터 현재까지의 데이터를 가져옵니다.
        asset_obj = yf.download(ticker, start="1900-01-01", interval="1mo")
        if asset_obj.empty: continue
        
        asset_raw = asset_obj['Adj Close'].pct_change()
        
        # 2. 족보(지수) 탐색 및 백필링
        # 사전에 정의된 지수가 있다면 해당 지수의 과거 데이터를 가져옵니다.
        if ticker in PROSPECTUS_DB:
            bench_ticker = PROSPECTUS_DB[ticker]
            bench_obj = yf.download(bench_ticker, start="1900-01-01", interval="1mo")
            
            if not bench_obj.empty:
                bench_raw = bench_obj['Adj Close'].pct_change()
                
                # ETF 데이터가 시작되는 시점(첫 번째 valid한 수익률)을 찾습니다.
                first_valid_date = asset_raw.first_valid_index()
                
                if first_valid_date:
                    # ETF 상장 전 데이터는 지수 데이터에서 가져옵니다.
                    bench_before = bench_raw[bench_raw.index < first_valid_date]
                    # 두 데이터를 결합합니다 (지수 과거 + ETF 현재)
                    combined = pd.concat([bench_before, asset_raw])
                    asset_raw = combined
        
        asset_raw.name = ticker
        all_data.append(asset_raw)
    
    # 3. 모든 자산 합치기
    if not all_data: return pd.DataFrame()
    
    df = pd.concat(all_data, axis=1)
    
    # NaN은 수익률 0으로 처리하거나 제거 (여기서는 데이터가 있는 시점부터 자름)
    return df.dropna(how='all').fillna(0)
