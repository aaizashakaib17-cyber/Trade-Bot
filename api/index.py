import os
import requests
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import google.generativeai as genai

app = FastAPI()

def get_gemini():
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    return genai.GenerativeModel("gemini-3.7-flash")

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
    <title>Trade Bot - AI Assistant</title>
    <style>
        :root {
            --bg-base: #090d16;
            --surface: #111827;
            --surface-glass: rgba(17, 24, 39, 0.75);
            --border: #1f2937;
            --accent: #10b981;
            --accent-hover: #059669;
            --text-main: #f3f4f6;
            --text-muted: #9ca3af;
        }

        body {
            font-family: 'Inter', system-ui, -apple-system, sans-serif;
            background-color: var(--bg-base);
            background-image: radial-gradient(circle at 50% 0%, #1e1b4b 0%, var(--bg-base) 70%);
            color: var(--text-main);
            margin: 0;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            overflow: hidden;
        }

        .app-container {
            width: 100%;
            max-width: 480px;
            height: 85vh;
            max-height: 700px;
            background: var(--surface-glass);
            backdrop-filter: blur(16px);
            border: 1px solid var(--border);
            border-radius: 20px;
            display: flex;
            flex-direction: column;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.6);
            overflow: hidden;
            transition: all 0.3s ease;
        }

        /* Auth View Styles */
        .auth-screen {
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            padding: 40px;
            height: 100%;
            text-align: center;
        }

        .logo-container {
            width: 64px;
            height: 64px;
            background: linear-gradient(135deg, rgba(16, 185, 129, 0.2), rgba(59, 130, 246, 0.2));
            border: 1px solid rgba(16, 185, 129, 0.4);
            border-radius: 16px;
            display: flex;
            justify-content: center;
            align-items: center;
            margin-bottom: 16px;
            box-shadow: 0 0 20px rgba(16, 185, 129, 0.15);
            overflow: hidden;
        }

        .logo-container img {
            width: 100%;
            height: 100%;
            object-fit: cover;
        }

        .auth-screen h1 {
            font-size: 1.8rem;
            margin-bottom: 8px;
            background: linear-gradient(to right, #34d399, #60a5fa);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .auth-screen p {
            color: var(--text-muted);
            font-size: 0.95rem;
            margin-bottom: 30px;
        }

        .auth-form {
            width: 100%;
            display: flex;
            flex-direction: column;
            gap: 15px;
        }

        /* Chat View Styles */
        .chat-screen {
            display: none;
            flex-direction: column;
            height: 100%;
        }

        .chat-header {
            padding: 20px;
            background: rgba(17, 24, 39, 0.9);
            border-bottom: 1px solid var(--border);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .header-title {
            font-weight: 600;
            font-size: 1.1rem;
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .header-logo {
            width: 30px;
            height: 30px;
            background: linear-gradient(135deg, rgba(16, 185, 129, 0.2), rgba(59, 130, 246, 0.2));
            border: 1px solid rgba(16, 185, 129, 0.4);
            border-radius: 8px;
            display: flex;
            justify-content: center;
            align-items: center;
            overflow: hidden;
        }

        .header-logo img {
            width: 100%;
            height: 100%;
            object-fit: cover;
        }

        .status-dot {
            width: 8px;
            height: 8px;
            background-color: var(--accent);
            border-radius: 50%;
            box-shadow: 0 0 8px var(--accent);
        }

        .user-badge {
            font-size: 0.8rem;
            color: var(--text-muted);
            background: var(--border);
            padding: 4px 10px;
            border-radius: 12px;
        }

        .chat-box {
            flex: 1;
            padding: 20px;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 16px;
            scroll-behavior: smooth;
        }

        .message {
            padding: 12px 16px;
            border-radius: 12px;
            max-width: 85%;
            font-size: 0.95rem;
            line-height: 1.5;
            animation: fadeIn 0.3s ease;
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(6px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .user-message {
            background: #2563eb;
            align-self: flex-end;
            color: white;
            border-bottom-right-radius: 4px;
        }

        .bot-message {
            background: #1f2937;
            align-self: flex-start;
            color: var(--text-main);
            border-bottom-left-radius: 4px;
            border: 1px solid var(--border);
        }

        .chat-input-area {
            display: flex;
            padding: 15px;
            background: rgba(17, 24, 39, 0.9);
            border-top: 1px solid var(--border);
            gap: 10px;
        }

        input {
            flex: 1;
            padding: 12px 16px;
            border-radius: 10px;
            border: 1px solid var(--border);
            background: #0b0f19;
            color: white;
            font-size: 0.95rem;
            transition: all 0.2s;
        }

        input:focus {
            outline: none;
            border-color: var(--accent);
            box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.15);
        }

        button {
            padding: 12px 20px;
            background: var(--accent);
            color: #000;
            border: none;
            border-radius: 10px;
            font-weight: 600;
            font-size: 0.95rem;
            cursor: pointer;
            transition: background 0.2s, transform 0.1s;
        }

        button:hover {
            background: var(--accent-hover);
        }

        button:active {
            transform: scale(0.98);
        }
    </style>
</head>
<body>
    <div class="app-container">
        <!-- Sign-In Screen -->
        <div class="auth-screen" id="authScreen">
            <div class="logo-container">
                <img src="https://raw.githubusercontent.com/aaizashakaib17-cyber/Trade-Bot/main/Gemini_Generated_Image_qunbdgqunbdgqunb.jpeg" alt="Trade Bot Logo">
            </div>
            <h1>Trade Bot</h1>
            <p>Sign in with your email to access your autonomous trading assistant.</p>
            <div class="auth-form">
                <input type="email" id="emailInput" placeholder="name@example.com" required>
                <button onclick="handleSignIn()">Continue with Email</button>
            </div>
        </div>

        <!-- Chat / Dashboard Screen -->
        <div class="chat-screen" id="chatScreen">
            <div class="chat-header">
                <div class="header-title">
                    <div class="header-logo">
                        <img src="https://raw.githubusercontent.com/aaizashakaib17-cyber/Trade-Bot/main/Gemini_Generated_Image_qunbdgqunbdgqunb.jpeg" alt="Logo">
                    </div>
                    <div class="status-dot"></div>
                    Trade Bot Assistant
                </div>
                <div class="user-badge" id="userEmailDisplay">user@app.com</div>
            </div>
            <div class="chat-box" id="chatBox">
                <div class="message bot-message">Hello! I am your Trade Bot assistant. How can I help you check your account or manage trades today?</div>
            </div>
            <div class="chat-input-area">
                <input type="text" id="userInput" placeholder="Ask about balance, positions, or markets..." onkeypress="handleKey(event)">
                <button onclick="sendMessage()">Send</button>
            </div>
        </div>
    </div>

    <script>
        function handleSignIn() {
            const email = document.getElementById('emailInput').value.trim();
            if (!email || !email.includes('@')) {
                alert('Please enter a valid email address.');
                return;
            }
            document.getElementById('userEmailDisplay').innerText = email;
            document.getElementById('authScreen').style.display = 'none';
            document.getElementById('chatScreen').style.display = 'flex';
        }

        async function sendMessage() {
            const inputField = document.getElementById('userInput');
            const chatBox = document.getElementById('chatBox');
            const text = inputField.value.trim();
            if (!text) return;

            chatBox.innerHTML += `<div class="message user-message">${text}</div>`;
            inputField.value = '';
            chatBox.scrollTop = chatBox.scrollHeight;

            const loadingId = 'loading-' + Date.now();
            chatBox.innerHTML += `<div class="message bot-message" id="${loadingId}">Analyzing markets...</div>`;
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
                document.getElementById(loadingId).innerText = "Error connecting to backend services.";
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
        You are an elite Trade Bot assistant connected to an Alpaca paper trading account.
        Context information: {context}
        User message: {request.message}
        Provide a helpful, precise response to the user based on the context.
        """
        response = model.generate_content(prompt)
        return {"reply": response.text.strip()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
