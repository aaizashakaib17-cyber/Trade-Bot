import os
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import alpaca_trade_api as tradeapi
import google.generativeai as genai

app = FastAPI()

# Configure Alpaca API credentials
ALPACA_API_KEY = os.getenv("ALPACA_API_KEY")
ALPACA_SECRET_KEY = os.getenv("ALPACA_SECRET_KEY")
ALPACA_BASE_URL = "https://paper-api.alpaca.markets"

alpaca = tradeapi.REST(
    ALPACA_API_KEY,
    ALPACA_SECRET_KEY,
    ALPACA_BASE_URL,
    api_version='v2'
)

# Configure Google Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)
gemini_model = genai.GenerativeModel("gemini-1.5-flash")

# Request Models
class ChatRequest(BaseModel):
    message: str

class TradeRequest(BaseModel):
    symbol: str
    qty: int
    side: str  # "buy" or "sell"
    type: str = "market"
    time_in_force: str = "gtc"


# Root endpoint serving the chat frontend HTML page
@app.get("/", response_class=HTMLResponse)
def read_root():
    html_path = Path(__file__).parent.parent / "index.html"
    if html_path.exists():
        with open(html_path, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>AI Trade-Bot is running, but index.html was not found.</h1>"


# Get Alpaca Account Balance
@app.get("/api/account")
def get_account():
    try:
        account = alpaca.get_account()
        return {
            "status": "success",
            "cash": account.cash,
            "portfolio_value": account.portfolio_value,
            "buying_power": account.buying_power,
            "currency": account.currency
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Place Trade Endpoint
@app.post("/api/trade")
def place_trade(trade: TradeRequest):
    try:
        order = alpaca.submit_order(
            symbol=trade.symbol.upper(),
            qty=trade.qty,
            side=trade.side.lower(),
            type=trade.type.lower(),
            time_in_force=trade.time_in_force.lower()
        )
        return {
            "status": "success",
            "message": f"Successfully placed {trade.side} order for {trade.qty} shares of {trade.symbol.upper()}",
            "order_id": order.id
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# Chat Endpoint with Gemini & Alpaca integration
@app.post("/api/chat")
def chat_with_agent(request: ChatRequest):
    user_msg = request.message.lower()
    
    # Check if user is asking for account balances
    if "balance" in user_msg or "account" in user_msg or "portfolio" in user_msg:
        try:
            account = alpaca.get_account()
            context = f"Live Alpaca Account Details: Cash: ${account.cash}, Portfolio Value: ${account.portfolio_value}, Buying Power: ${account.buying_power}"
        except Exception as e:
            context = "Could not fetch account details due to an error."
    else:
        context = "General financial or assistant query."

    prompt = f"""
    You are an AI financial trading assistant connected to an Alpaca paper trading account.
    Context information: {context}
    User message: {request.message}
    
    Provide a helpful, concise response to the user.
    """

    try:
        response = gemini_model.generate_content(prompt)
        return {"reply": response.text.strip()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        
