import os
import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

# Grab the credentials from Vercel's environment variables
ALPACA_API_KEY = os.getenv("APCA_API_KEY_ID")
ALPACA_API_SECRET = os.getenv("APCA_API_SECRET_KEY")
# Using the Alpaca Paper Trading endpoint for safety during testing
ALPACA_BASE_URL = "https://paper-api.alpaca.markets"

class TradeRequest(BaseModel):
    symbol: str
    qty: float
    side: str  # "buy" or "sell"

@app.get("/")
def read_root():
    return {"message": "AI Trade-Bot is running on Vercel!"}

@app.get("/api/account")
def get_alpaca_account():
    if not ALPACA_API_KEY or not ALPACA_API_SECRET:
        raise HTTPException(status_code=500, detail="Alpaca API keys are not set in environment variables.")
    
    headers = {
        "APCA-API-KEY-ID": ALPACA_API_KEY,
        "APCA-API-SECRET-KEY": ALPACA_API_SECRET
    }
    
    response = requests.get(f"{ALPACA_BASE_URL}/v2/account", headers=headers)
    
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.json())
        
    account_data = response.json()
    return {
        "status": "success",
        "cash": account_data.get("cash"),
        "portfolio_value": account_data.get("portfolio_value"),
        "buying_power": account_data.get("buying_power"),
        "currency": account_data.get("currency")
    }

@app.post("/api/trade")
def place_trade(trade: TradeRequest):
    if not ALPACA_API_KEY or not ALPACA_API_SECRET:
        raise HTTPException(status_code=500, detail="Alpaca API keys are not set in environment variables.")
    
    headers = {
        "APCA-API-KEY-ID": ALPACA_API_KEY,
        "APCA-API-SECRET-KEY": ALPACA_API_SECRET,
        "Content-Type": "application/json"
    }
    
    payload = {
        "symbol": trade.symbol.upper(),
        "qty": trade.qty,
        "side": trade.side.lower(),
        "type": "market",
        "time_in_force": "gtc"
    }
    
    response = requests.post(f"{ALPACA_BASE_URL}/v2/orders", json=payload, headers=headers)
    
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.json())
        
    return {
        "status": "success",
        "order_details": response.json()
    }
