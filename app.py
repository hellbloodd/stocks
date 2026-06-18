import time
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import yfinance as yf
import pandas as pd

app = FastAPI()

# Allow your GitHub Pages site to talk to this server
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# --- THE CACHE SYSTEM ---
# This dictionary stores data in the server's memory so we don't ask Yahoo repeatedly.
stock_cache = {}
CACHE_EXPIRY_SECONDS = 600  # Data is valid for 10 minutes (600 seconds)

def get_cached_stock(ticker: str):
    ticker = ticker.strip().upper()
    current_time = time.time()
    
    # 1. Check if data exists in memory and isn't expired
    if ticker in stock_cache:
        cached_data = stock_cache[ticker]
        if current_time < cached_data['expires']:
            print(f"Cache hit for {ticker} - Returning stored data.")
            return cached_data['data']
    
    # 2. If not in cache, fetch from Yahoo (Add a safety delay to avoid bans)
    print(f"Cache miss for {ticker}. Fetching new data...")
    time.sleep(2) # Wait 2 seconds before asking Yahoo
    
    try:
        t = yf.Ticker(ticker)
        info = t.info or {}
        hist = t.history(period="6mo")
        
        if not info or "regularMarketPrice" not in info or hist.empty:
            return None # Ticker invalid

        data = {
            'symbol': ticker,
            'name': info.get('shortName', 'Unknown'),
            'price': float(info.get('regularMarketPrice', 0)),
            'currency': info.get('currency', 'USD'),
            'market_cap': int(info.get('marketCap', 0)),
            'pe_ratio': float(info.get('trailingPE', 0)) or None,
            'rsi_14': None, # Calculated below
            'trend': 'N/A', # Calculated below
            'history': hist.reset_index().to_dict(orient='records')
        }
        
        # --- Calculations (Risk & Technicals) ---
        if len(hist) > 14:
            close = hist['Close']
            # RSI Calculation
            delta = close.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            data['rsi_14'] = round(100 - (100 / (1 + rs.iloc[-1])), 2)
            
            # Trend Calculation (SMA 20 vs SMA 50)
            sma20 = close.rolling(window=20).mean().iloc[-1]
            sma50 = close.rolling(window=50).mean().iloc[-1]
            data['trend'] = 'Uptrend' if sma20 > sma50 else 'Downtrend'
            data['technical_score'] = int((sma20 / sma50) * 100) # Simple trend score

        # Save to cache so next request is instant
        stock_cache[ticker] = {
            'data': data,
            'expires': current_time + CACHE_EXPIRY_SECONDS
        }
        
        return data

    except Exception as e:
        print(f"Error fetching {ticker}: {e}")
        return None

@app.get("/stock/{ticker}")
def get_stock(ticker: str):
    result = get_cached_stock(ticker)
    
    if not result:
        raise HTTPException(status_code=404, detail="Ticker not found or data unavailable.")
        
    return result

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
