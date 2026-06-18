import time
import random
import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import yfinance as yf
import pandas as pd

app = FastAPI()

# Allow your GitHub Pages site to talk to this server
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# --- The Cache System (Stores data so we don't spam Yahoo) ---
cache = {}
CACHE_DURATION_MINUTES = 5

def get_stock_data_cached(ticker: str):
    """Fetches stock data with caching to prevent 429 errors."""
    
    # Check if we already have valid data in our memory cache
    if ticker in cache:
        item = cache[ticker]
        if (datetime.datetime.now() - item['time']).seconds < CACHE_DURATION_MINUTES * 60:
            return None, None, item['info'], item['hist']
    
    # If not in cache, fetch from Yahoo with heavy delays
    print(f"Fetching new data for {ticker}...")
    for attempt in range(5):
        try:
            time.sleep(random.uniform(3.0, 8.0)) # Wait 3-8 seconds between requests!
            
            t = yf.Ticker(ticker.strip().upper())
            info = t.info or {}
            hist = t.history(period="6mo")

            if not info or "regularMarketPrice" not in info:
                return None, f"Ticker '{ticker}' not found.", None, None
            
            if hist.empty:
                return None, f"No data for {ticker}.", None, None

            # Save to cache so next time is instant
            cache[ticker] = {'info': info, 'hist': hist, 'time': datetime.datetime.now()}
            
            return t, None, info, hist
        
        except Exception as e:
            # If we hit a 429, wait longer and retry
            if "429" in str(e) or "Too Many Requests" in str(e):
                time.sleep(15) # Wait 15s if blocked
            
    return None, "Yahoo Finance is currently blocking this server. Please try again in 30 seconds.", None, None

@app.get("/stock/{ticker}")
def get_stock_data(ticker: str):
    t, error_msg, info, hist = get_stock_data_cached(ticker)
    
    # If there was an error (invalid ticker or blocked), return it as a clean error message
    if error_msg:
        status_code = 404 if "not found" in error_msg else 429
        raise HTTPException(status_code=status_code, detail=error_msg)

    price = float(info.get("regularMarketPrice", 0))
    currency = info.get("currency", "USD")

    # --- Calculations (P/E, RSI, Risk) ---
    pe_ratio = float(info.get("trailingPE", 0)) or None
    
    # Technical Score Logic
    rsi_val = 50 # Default neutral
    if len(hist) > 14:
        close = hist['Close']
        rsi_series = (close - close.rolling(14).min()) / (close.rolling(14).max() - close.rolling(14).min()) * 100
        rsi_val = rsi_series.iloc[-1]

    sma20 = hist['Close'].rolling(20).mean().iloc[-1]
    sma50 = hist['Close'].rolling(50).mean().iloc[-1]
    
    # Simple Score based on RSI and Trend
    score = 50 + (20 if rsi_val < 30 else (-20 if rsi_val > 70 else 0)) + (10 if sma20 > sma50 else -10)

    return {
        "symbol": ticker.strip().upper(),
        "name": info.get("shortName", "Unknown"),
        "price": price,
        "currency": currency,
        "market_cap": int(info.get("marketCap", 0)),
        "pe_ratio": pe_ratio,
        
        # Analysis Features
        "technical_score": max(0, min(100, int(score))),
        "rsi_14": round(float(rsi_val), 2) if not pd.isna(rsi_val) else None,
        "trend": "Uptrend" if sma20 > sma50 else "Downtrend",
        
        "analyst_target_price": float(t.fast_info.targetMeanPrice) if hasattr(t.fast_info, 'targetMeanPrice') else None,
        
        # Data for charts
        "history": hist.reset_index().to_dict(orient="records")
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
