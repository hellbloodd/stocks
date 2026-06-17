from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import yfinance as yf
import pandas as pd
import pandas_ta as ta
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
        # Calculate indicators
        df["SMA20"] = ta.sma(df["Close"], length=20)
        df["SMA50"] = ta.sma(df["Close"], length=50)
        rsi = ta.rsi(df["Close"], length=14)
        df["RSI"] = rsi.iloc[-1] if len(rsi) > 0 else None
        
        macd_obj = ta.macd(df["Close"])
        macd_line = macd_obj.iloc[-1]["MACD_12_26_9"] if macd_obj is not None and not macd_obj.empty else None
        signal_line = macd_obj.iloc[-1]["MACDs_12_26_9"] if macd_obj is not None and not macd_obj.empty else None
        histogram = macd_obj.iloc[-1]["MACDh_12_26_9"] if macd_obj is not None and not macd_obj.empty else None
        
        return {
            "sma20": float(df["SMA20"].iloc[-1]) if not pd.isna(df["SMA20"].iloc[-1]) else None,
            "sma50": float(df["SMA50"].iloc[-1]) if not pd.isna(df["SMA50"].iloc[-1]) else None,
            "rsi_14": float(df["RSI"].iloc[-1]) if not pd.isna(df["RSI"].iloc[-1]) else None,
            "macd": {
                "line": round(float(macd_line), 2) if macd_line is not None else None,
                "signal": round(float(signal_line), 2) if signal_line is not None else None,
                "histogram": round(float(histogram), 2) if histogram is not None else None
            }
        }
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Technical data unavailable: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
