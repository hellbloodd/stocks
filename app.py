import time
import random
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import yfinance as yf
import pandas as pd
import numpy as np
import requests

app = FastAPI()

# Allow GitHub Pages to talk to this server
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

def get_stock_with_retry(ticker):
    """Fetches data with headers and delays to avoid 429 errors."""
    # Try up to 3 times
    for i in range(3):
        try:
            time.sleep(random.uniform(1.5, 3.0)) # Wait 1.5s to 3s before request
            
            t = yf.Ticker(ticker.strip().upper())
            
            # Check if valid first
            info = t.info or {}
            if not info or "regularMarketPrice" not in info:
                return None, f"Ticker {ticker} not found. Please check spelling."

            hist = t.history(period="6mo")
            if hist.empty:
                return None, f"No price history for {ticker}."
                
            return t, info, hist
        
        except Exception as e:
            time.sleep(2) # Wait longer before retrying
            
    return None, "Yahoo Finance is currently busy. Please try again in 60 seconds."

def calculate_technical_score(df):
    """Calculates a 0-100 technical score."""
    if len(df) < 50: return 50
    
    close = df['Close']
    rsi = (close - close.rolling(14).min()) / (close.rolling(14).max() - close.rolling(14).min()) * 100
    sma20 = close.rolling(20).mean().iloc[-1]
    sma50 = close.rolling(50).mean().iloc[-1]
    
    score = 50
    
    rsi_val = rsi.iloc[-1] if not pd.isna(rsi.iloc[-1]) else 50
    if rsi_val > 70: score -= 20 
    elif rsi_val < 30: score += 20 
    
    if sma20 > sma50: score += 15 
    else: score -= 15
    
    return max(0, min(100, int(score)))

def calculate_risk_info(ticker_obj):
    """Calculates risk metrics."""
    info = ticker_obj.info or {}
    beta = info.get("beta", None)
    volatility_52w = info.get("fiftyTwoWeekHigh", 0) / info.get("fiftyTwoWeekLow", 1)
    
    risk_score = 25 + (beta if beta else 1) * 20 + volatility_52w * 10
    
    return {
        "beta": round(beta, 2) if beta else None,
        "volatility_ratio": round(volatility_52w, 2),
        "risk_level": "HIGH" if risk_score > 70 else ("MEDIUM" if risk_score > 40 else "LOW")
    }

@app.get("/stock/{ticker}")
def get_stock_data(ticker: str):
    t, info_or_error, hist = get_stock_with_retry(ticker)
    
    if not t:
        raise HTTPException(status_code=404, detail=info_or_error)

    price = float(info_or_error.get("regularMarketPrice", 0))
    
    # Fetch Analyst Data
    key_stats = t.default_key_statistics or {}
    analyst_data = t.fast_info
    target_price = analyst_data.targetMeanPrice if hasattr(analyst_data, 'targetMeanPrice') else None
    
    tech_score = calculate_technical_score(hist)
    
    return {
        "symbol": ticker.strip().upper(),
        "name": info_or_error.get("shortName", "Unknown"),
        "price": price,
        "currency": info_or_error.get("currency", "USD"),
        "market_cap": int(info_or_error.get("marketCap", 0)),
        "pe_ratio": float(info_or_error.get("trailingPE", 0)) or None,
        "dividend_yield": float(info_or_error.get("dividendYield", 0) * 100 or 0),
        
        "technical_score": tech_score,
        "risk_info": calculate_risk_info(t),
        "rsi_14": round(float(hist['Close'].rolling(14).mean().iloc[-1]), 2) if len(hist) > 14 else None,
        
        "analyst_target_price": float(target_price) if target_price and target_price > 0 else None,
        "recommendation": info_or_error.get("recommendation", {}).get("key", "N/A").upper() if isinstance(info_or_error.get("recommendation"), dict) else "NEUTRAL",
        
        "history": hist.reset_index().to_dict(orient="records")
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
