import time
import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import yfinance as yf
import pandas as pd
import numpy as np

app = FastAPI()

# Allow GitHub Pages to talk to this Render server
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

def calculate_technical_score(df):
    """Calculates a 0-100 technical score based on indicators."""
    if len(df) < 50: return 50
    
    close = df['Close']
    rsi = (close - close.rolling(14).min()) / (close.rolling(14).max() - close.rolling(14).min()) * 100
    sma20 = close.rolling(20).mean().iloc[-1]
    sma50 = close.rolling(50).mean().iloc[-1]
    
    score = 50 # Neutral
    
    # RSI Logic
    rsi_val = rsi.iloc[-1] if not pd.isna(rsi.iloc[-1]) else 50
    if rsi_val > 70: score -= 20 # Overbought (Risk)
    elif rsi_val < 30: score += 20 # Oversold (Buy Signal)
    
    # Trend Logic
    if sma20 > sma50: score += 15 # Bullish trend
    else: score -= 15
    
    return max(0, min(100, int(score)))

def calculate_risk_info(ticker_obj):
    """Calculates risk metrics."""
    info = ticker_obj.info or {}
    
    beta = info.get("beta", None)
    volatility_52w = info.get("fiftyTwoWeekHigh", 0) / info.get("fiftyTwoWeekLow", 1)
    
    # Simple Risk Score (Lower is safer)
    # Beta > 1.5 is volatile. Volatility Ratio > 3.0 is dangerous.
    risk_score = 25 + (beta if beta else 1) * 20 + volatility_52w * 10
    
    return {
        "beta": round(beta, 2) if beta else None,
        "volatility_ratio": round(volatility_52w, 2),
        "risk_level": "HIGH" if risk_score > 70 else ("MEDIUM" if risk_score > 40 else "LOW")
    }

@app.get("/stock/{ticker}")
def get_stock_data(ticker: str):
    try:
        t = yf.Ticker(ticker.strip().upper())
        
        # Wait briefly to avoid 429s from Yahoo
        time.sleep(0.1) 
        
        info = t.info or {}
        hist = t.history(period="6mo")
        
        if hist.empty or not info:
            raise ValueError("No data available for this ticker.")

        price = float(info.get("currentPrice", 0))
        currency = info.get("currency", "USD")
        
        # Fetch Analyst Data (Buy/Sell/Hold counts)
        key_stats = t.default_key_statistics or {}
        analyst_data = t.fast_info
        target_price = analyst_data.targetMeanPrice if hasattr(analyst_data, 'targetMeanPrice') else None
        
        # Calculate Technical Score
        tech_score = calculate_technical_score(hist)
        
        return {
            "symbol": ticker.strip().upper(),
            "name": info.get("shortName", "Unknown"),
            "price": price,
            "currency": currency,
            "market_cap": int(info.get("marketCap", 0)),
            "pe_ratio": float(info.get("trailingPE", 0)) or None,
            "dividend_yield": float(info.get("dividendYield", 0) * 100 or 0),
            
            # New Analysis Features
            "technical_score": tech_score,
            "risk_info": calculate_risk_info(t),
            "rsi_14": round(float(hist['Close'].rolling(14).mean().iloc[-1]), 2) if len(hist) > 14 else None,
            
            # Analyst Data
            "analyst_target_price": float(target_price) if target_price and target_price > 0 else None,
            "recommendation": info.get("recommendation", {}).get("key", "N/A").upper() if isinstance(info.get("recommendation"), dict) else "NEUTRAL",
            
            # History for charts
            "history": hist.reset_index().to_dict(orient="records")
        }

    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Ticker not found or data unavailable: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
