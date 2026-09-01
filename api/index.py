import os
import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import google.generativeai as genai

app = FastAPI()

# Grab credentials from Vercel's environment variables
ALPACA_API_KEY = os.getenv("APCA_API_KEY_ID")
ALPACA_API_SECRET = os.getenv("APCA_API_SECRET_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

ALPACA_BASE_URL = "https://paper-api.alpaca.markets"

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

class TradeRequest(BaseModel):
    symbol: str
    qty: float
    side: str  # "buy" or "sell"

class ChatRequest(BaseModel):
    message: str

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

@app.post("/api/chat")
def chat_with_agent(chat: ChatRequest):
    if not GEMINI_API_KEY:
        raise HTTPException(status_code=500, detail="Gemini API key is not set in environment variables.")
    
    user_message = chat.message.lower()
    
    # If the user asks about account details, fetch it directly
    if "balance" in user_message or "account" in user_message or "cash" in user_message:
        account_info = get_alpaca_account()
        return {
            "reply": f"Here are your account details: Cash: ${account_info['cash']}, Portfolio Value: ${account_info['portfolio_value']}, Buying Power: ${account_info['buying_power']}"
        }
    
    # Otherwise, use Gemini to respond naturally as a customer service trading bot
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        prompt = f"You are a helpful, professional customer service assistant for an automated trading app. Respond to this customer message politely and concisely: {chat.message}"
        response = model.generate_content(prompt)
        return {"reply": response.text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
