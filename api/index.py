import os
import requests
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import google.generativeai as genai

app = FastAPI()

def get_gemini():
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    return genai.GenerativeModel("gemini-3.6-flash")

def fetch_alpaca_account():
    api_key = os.getenv("ALPACA_API_KEY")
    secret_key = os.getenv("ALPACA_SECRET_KEY")
    
    headers = {
        "APCA-API-KEY-ID": api_key,
        "APCA-API-SECRET-KEY": secret_key
    }
    
    url = "https://paper-api.alpaca.markets/v2/account"
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        raise Exception(f"Alpaca API Error: {response.status_code} - {response.text}")
        
    return response.json()

class ChatRequest(BaseModel):
    message: str

class TradeRequest(BaseModel):
    symbol: str
    qty: int
    side: str
    type: str = "market"
    time_in_force: str = "gtc"

@app.get("/", response_class=HTMLResponse)
@app.get("/api/index.py", response_class=HTMLResponse)
def read_root():
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Trade-Bot Assistant</title>
    <style>
        body { font-family: Arial, sans-serif; background-color: #0f172a; color: #f8fafc; margin: 0; display: flex; justify-content: center; align-items: center; height: 100vh; }
        .chat-container { width: 100%; max-width: 600px; background: #1e293b; border-radius: 12px; display: flex; flex-direction: column; height: 80vh; box-shadow: 0 4px 20px rgba(0,0,0,0.5); overflow: hidden; }
        .chat-header { padding: 20px; background: #334155; font-size: 1.2rem; font-weight: bold; text-align: center; }
        .chat-box { flex: 1; padding: 20px; overflow-y: auto; display: flex; flex-direction: column; gap: 12px; }
        .message { padding: 12px 16px; border-radius: 8px; max-width: 80%; line-height: 1.4; }
        .user-message { background: #3b82f6; align-self: flex-end; color: white; }
        .bot-message { background: #475569; align-self: flex-start; color: #f8fafc; }
        .chat-input-area { display: flex; padding: 15px; background: #334155; gap: 10px; }
        input { flex: 1; padding: 12px; border-radius: 6px; border: none; background: #1e293b; color: white; font-size: 1rem; }
        input:focus { outline: 2px solid #3b82f6; }
        button { padding: 12px 20px; background: #3b82f6; color: white; border: none; border-radius: 6px; font-weight: bold; cursor: pointer; }
        button:hover { background: #2563eb; }
    </style>
</head>
<body>
    <div class="chat-container">
        <div class="chat-header">AI Trading Assistant</div>
        <div class="chat-box" id="chatBox">
            <div class="message bot-message">Hello! I am your AI trading assistant. How can I help you check your account or manage trades today?</div>
        </div>
        <div class="chat-input-area">
            <input type="text" id="userInput" placeholder="Type your question here..." onkeypress="handleKey(event)">
            <button onclick="sendMessage()">Send</button>
        </div>
    </div>
    <script>
        async function sendMessage() {
            const inputField = document.getElementById('userInput');
            const chatBox = document.getElementById('chatBox');
            const text = inputField.value.trim();
            if (!text) return;
            chatBox.innerHTML += `<div class="message user-message">${text}</div>`;
            inputField.value = '';
            chatBox.scrollTop = chatBox.scrollHeight;
            const loadingId = 'loading-' + Date.now();
            chatBox.innerHTML += `<div class="message bot-message" id="${loadingId}">Thinking...</div>`;
            chatBox.scrollTop = chatBox.scrollHeight;
            try {
                const response = await fetch('/api/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message: text })
                });
                const data = await response.json();
                document.getElementById(loadingId).innerText = data.reply || JSON.stringify(data);
            } catch (error) {
                document.getElementById(loadingId).innerText = "Error connecting to backend.";
            }
            chatBox.scrollTop = chatBox.scrollHeight;
        }
        function handleKey(event) {
            if (event.key === 'Enter') sendMessage();
        }
    </script>
</body>
</html>
    """

@app.get("/api/account")
def get_account():
    try:
        account = fetch_alpaca_account()
        return {
            "status": "success",
            "cash": account.get("cash"),
            "portfolio_value": account.get("portfolio_value"),
            "buying_power": account.get("buying_power"),
            "currency": account.get("currency")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat")
def chat_with_agent(request: ChatRequest):
    try:
        user_msg = request.message.lower()
        context = "General financial or assistant query."
        
        if "balance" in user_msg or "account" in user_msg or "portfolio" in user_msg or "value" in user_msg:
            try:
                account = fetch_alpaca_account()
                context = f"Live Alpaca Account Details: Cash: ${account.get('cash')}, Portfolio Value: ${account.get('portfolio_value')}, Buying Power: ${account.get('buying_power')}"
            except Exception as e:
                context = f"Could not fetch account details due to: {str(e)}"

        model = get_gemini()
        prompt = f"""
        You are an AI financial trading assistant connected to an Alpaca paper trading account.
        Context information: {context}
        User message: {request.message}
        Provide a helpful, concise response to the user based on the context.
        """
        response = model.generate_content(prompt)
        return {"reply": response.text.strip()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
