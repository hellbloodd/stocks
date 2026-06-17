from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import yfinance as yf
import pandas as pd
import numpy as np
from typing import Optional, Dict, List

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@app.get("/validate/{ticker}")
def validate_ticker(ticker: str):
    try:
        info = yf.Ticker(ticker.strip().upper()).info
        if not info or "symbol" not in info: raise ValueError("Invalid ticker")
        return {"valid": True, "name": info.get("longName", info.get("shortName", ticker))}
    except:
        return {"valid": False}

@app.get("/stock/{ticker}")
def get_stock(ticker: str):
    try:
        t = yf.Ticker(ticker.strip().upper())
        hist = t.history(period="1y")
        if hist.empty: raise ValueError("No data")
        
        info = t.info or {}
        price = float(info.get("currentPrice", 0) or info.get("regularMarketPrice", 0) or 0)
        
        return {
            "symbol": ticker.strip().upper(),
            "name": info.get("longName", "Unknown"),
            "price": round(price, 2),
            "currency": info.get("currency", "USD"),
            "market_cap": int(info.get("marketCap", 0)) or None,
            "pe_ratio": float(info.get("trailingPE", 0) or 0) or None,
            "eps": float(info.get("trailingEps", 0) or 0) or None,
            "dividend_yield": float(info.get("dividendYield", 0) * 100 or 0) or None,
            "beta": float(info.get("beta", 0) or 0) or None,
            "52w_high": float(hist["High"].max()) or None,
            "52w_low": float(hist["Low"].min()) or None,
            "volume": int(info.get("volume", 0) or info.get("averageVolume", 0) or 0),
            "history": hist.reset_index().to_dict(orient="records")
        }
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Ticker not found or invalid: {str(e)}")

@app.get("/tech/{ticker}")
def get_technicals(ticker: str):
    try:
        hist = yf.Ticker(ticker.strip().upper()).history(period="1y")
        if hist.empty: raise ValueError("No history data")
        
        df = pd.DataFrame(hist)
        close = df['Close']
        
        # --- Calculate Indicators Manually (No external library needed) ---
        
        # SMA 20 & 50
        sma20 = close.rolling(window=20).mean().iloc[-1]
        sma50 = close.rolling(window=50).mean().iloc[-1]
        
        # RSI 14 (Standard Formula)
        delta = close.diff()
        gain = delta.where(delta > 0, 0).rolling(window=14).mean()
        loss = (-delta).where(delta < 0, 0).rolling(window=14).mean()
        rs = gain / loss
        rsi_14 = 100 - (100 / (1 + rs)).iloc[-1]
        
        # MACD (12, 26, 9)
        ema12 = close.ewm(span=12, adjust=False).mean()
        ema26 = close.ewm(span=26, adjust=False).mean()
        macd_line = ema12 - ema26
        signal_line = macd_line.ewm(span=9, adjust=False).mean()
        histogram = macd_line - signal_line
        
        # Return standardized JSON to match the frontend dashboard
        return {
            "sma20": round(float(sma20), 2) if not pd.isna(sma20) else None,
            "sma50": round(float(sma50), 2) if not pd.isna(sma50) else None,
            "rsi_14": round(float(rsi_14), 2) if not pd.isna(rsi_14) else None,
            "macd": {
                "line": round(float(macd_line.iloc[-1]), 2) if not pd.isna(macd_line.iloc[-1]) else None,
                "signal": round(float(signal_line.iloc[-1]), 2) if not pd.isna(signal_line.iloc[-1]) else None,
                "histogram": round(float(histogram.iloc[-1]), 2) if not pd.isna(histogram.iloc[-1]) else None
            }
        }
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Technical data unavailable: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
