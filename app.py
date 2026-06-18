import time
import random
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import yfinance as yf
import pandas as pd
import numpy as np

app = FastAPI()
# Allow your GitHub Pages site to talk to this server
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

def get_stock_info(ticker: str):
    """
    Safely fetches data from Yahoo Finance with retries.
    Returns a dictionary containing 'success' status and data/error message.
    """
    for attempt in range(3):
        try:
            # Add random delay to mimic human behavior and avoid 429s
            time.sleep(random.uniform(2.0, 5.0)) 
            
            t = yf.Ticker(ticker.strip().upper())
            
            info = t.info or {}
            hist = t.history(period="6mo")

            # Check if the ticker is valid
            if not info or "regularMarketPrice" not in info:
                return {"success": False, "error": f"Ticker '{ticker}' not found. Please check spelling."}
            
            if hist.empty:
                return {"success": False, "error": f"No data found for {ticker}."}

            return {"success": True, "data": (t, info, hist)}
        
        except Exception as e:
            # If we get a 429 error specifically, wait longer
            if "429" in str(e):
                time.sleep(10)
            
    return {"success": False, "error": "Yahoo Finance is too busy right now. Please try again in 60 seconds."}

@app.get("/stock/{ticker}")
def get_stock_data(ticker: str):
    # Get result from our safe fetcher
    result = get_stock_info(ticker)
    
    # If it failed (invalid ticker or yahoo blocked us), return that error to the frontend
    if not result["success"]:
        raise HTTPException(status_code=404, detail=result["error"])

    # Unpack data safely now that we know it succeeded
    t, info, hist = result["data"]

    price = float(info.get("regularMarketPrice", 0))
    currency = info.get("currency", "USD")

    # --- Calculations ---
    rsi = (hist['Close'] - hist['Close'].rolling(14).min()) / (hist['Close'].rolling(14).max() - hist['Close'].rolling(14).min()) * 100
    rsi_val = rsi.iloc[-1] if not pd.isna(rsi.iloc[-1]) else 50
    
    sma20 = hist['Close'].rolling(20).mean().iloc[-1]
    sma50 = hist['Close'].rolling(50).mean().iloc[-1]

    score = 50 + (15 if rsi_val < 30 else -15) + (15 if sma20 > sma50 else -15)
    
    # --- Risk ---
    beta = info.get("beta", None)
    vol_high = info.get("fiftyTwoWeekHigh", 0) / info.get("fiftyTwoWeekLow", 1)
    risk_level = "HIGH" if (vol_high > 2.5 or (beta and beta > 1.5)) else ("MEDIUM" if (vol_high > 2.0) else "LOW")

    # --- Analysts ---
    analyst_data = t.fast_info
    target_price = analyst_data.targetMeanPrice if hasattr(analyst_data, 'targetMeanPrice') else None
    
    return {
        "symbol": ticker.strip().upper(),
        "name": info.get("shortName", "Unknown"),
        "price": price,
        "currency": currency,
        "market_cap": int(info.get("marketCap", 0)),
        "pe_ratio": float(info.get("trailingPE", 0)) or None,
        
        # Analysis Features
        "technical_score": max(0, min(100, int(score))),
        "rsi_14": round(float(rsi_val), 2),
        "trend": "Uptrend" if sma20 > sma50 else "Downtrend",
        
        "risk_info": {
            "level": risk_level,
            "beta": round(beta, 2) if beta else None,
            "volatility": round(vol_high, 2)
        },

        "analyst_target_price": float(target_price) if target_price and target_price > 0 else None,
        
        # Data for frontend charts
        "history": hist.reset_index().to_dict(orient="records")
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
