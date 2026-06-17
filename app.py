# app.py
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pdfplumber
import io
import re
import pandas as pd
from collections import defaultdict
from datetime import datetime

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

def parse_tr_pdf(pdf_bytes: bytes) -> list[dict]:
    trades = []
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables() or []
            for table in tables:
                if not table or len(table) < 2: continue
                
                # Normalize first row to detect columns
                header = [str(cell).strip().lower() if cell else "" for cell in table[0]]
                
                # Auto-detect column indices based on Trade Republic's common headers
                date_idx = next((i for i, h in enumerate(header) if "datum" in h or "date" in h), 0)
                type_idx = next((i for i, h in enumerate(header) if "vorgang" in h or "type" in h or "transaktion" in h), 1)
                amount_idx = next((i for i, h in enumerate(header) if "anzahl" in h or "quantity" in h or "menge" in h), 2)
                price_idx = next((i for i, h in enumerate(header) if "kurs" in h or "price" in h or "preis" in h), 3)
                value_idx = next((i for i, h in enumerate(header) if "kurswert" in h or "value" in h or "wert" in h), 4)
                fee_idx = next((i for i, h in enumerate(header) if "gebühr" in h or "fee" in h or "courtage" in h), 5)
                
                for row in table[1:]:
                    if not any(str(c).strip() for c in row): continue
                    
                    def to_float(v):
                        if v is None: return None
                        s = str(v).replace(",", ".").replace(" ", "").replace("\xa0", "")
                        return float(re.sub(r"[^0-9.\-]", "", s)) if re.match(r"^[\d\.\-]+$", s) else None
                    
                    try:
                        trades.append({
                            "date": str(row[date_idx]).strip() if date_idx < len(row) else None,
                            "type": str(row[type_idx]).strip().upper() if type_idx < len(row) else "",
                            "quantity": to_float(row[amount_idx]) if amount_idx < len(row) else 0,
                            "price": to_float(row[price_idx]) if price_idx < len(row) else 0,
                            "value": to_float(row[value_idx]) if value_idx < len(row) else 0,
                            "fee": to_float(row[fee_idx]) if fee_idx < len(row) else 0
                        })
                    except Exception: continue
    return trades

def calculate_stats(trades: list[dict]) -> dict:
    buys = [t for t in trades if "KAUF" in t["type"] or "BUY" in t["type"]]
    sells = [t for t in trades if "VERKAUF" in t["type"] or "SELL" in t["type"]]
    
    # Realized P&L approximation: match sells to buys by value/quantity
    pnl_realized = 0.0
    qty_tracker = defaultdict(float)
    cost_tracker = defaultdict(float)
    
    for t in trades:
        if "KAUF" in t["type"] or "BUY" in t["type"]:
            qty_tracker[t.get("date")] += t["quantity"] or 0
            cost_tracker[t.get("date")] += (t["value"] or 0) + (t["fee"] or 0)
        elif "VERKAUF" in t["type"] or "SELL" in t["type"]:
            # Simple FIFO matching
            qty = abs(t["quantity"] or 0)
            sell_val = abs(t["value"] or 0)
            sell_fee = abs(t["fee"] or 0)
            
            matched_cost = 0.0
            for date in sorted(qty_tracker.keys()):
                if qty <= 0: break
                available = min(qty, qty_tracker[date])
                cost_per_share = cost_tracker[date] / qty_tracker[date] if qty_tracker[date] else 0
                matched_cost += available * cost_per_share + (sell_fee * (available / qty))
                qty_tracker[date] -= available
                qty -= available
            pnl_realized += sell_val - matched_cost
            
    win_trades = [t for t in sells if abs(t["value"] or 0) > (abs(t.get("fee",0)) + (abs(t["quantity"]) * 0.01))]
    
    return {
        "summary": {
            "total_trades": len(trades),
            "realized_pnl_eur": round(pnl_realized, 2),
            "win_rate_pct": round((len(win_trades) / max(len(sells), 1)) * 100, 1),
            "avg_hold_days": 0.5  # Placeholder; add date diff logic if needed
        },
        "trades_raw": trades[:200],
        "top_sells": sorted([t for t in sells if t["value"]], key=lambda x: abs(x["value"]), reverse=True)[:5]
    }

@app.post("/analyze")
async def analyze(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Upload a PDF only")
    
    data = await file.read()
    trades = parse_tr_pdf(data)
    if not trades:
        raise HTTPException(400, "No readable Trade Republic table found. Upload the annual tax statement PDF.")
    
    return calculate_stats(trades)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
