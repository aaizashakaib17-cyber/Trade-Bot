import os
import streamlit as st
from dotenv import load_dotenv
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import GetOptionContractsRequest, MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
from google import genai

# Page Configuration
st.set_page_config(page_title="Trade-Bot AI", page_icon="📈", layout="centered")

# Load environment variables
load_dotenv()

ALPACA_API_KEY = os.getenv("ALPACA_API_KEY")
ALPACA_SECRET_KEY = os.getenv("ALPACA_SECRET_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Initialize Clients
@st.cache_resource
def get_clients():
    t_client = TradingClient(ALPACA_API_KEY, ALPACA_SECRET_KEY, paper=True) if ALPACA_API_KEY else None
    g_client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None
    return t_client, g_client

trading_client, ai_client = get_clients()

# Helper Functions
def get_account_status():
    try:
        account = trading_client.get_account()
        return f"Account Status: **{account.status}** | Cash Balance: **${account.cash}**"
    except Exception as e:
        return f"Error: {e}"

def execute_market_trade(symbol: str, qty: int, side: str = "buy"):
    try:
        order_side = OrderSide.BUY if side.lower() == "buy" else OrderSide.SELL
        order_data = MarketOrderRequest(
            symbol=symbol.upper(),
            qty=qty,
            side=order_side,
            time_in_force=TimeInForce.DAY
        )
        order = trading_client.submit_order(order_data)
        return f"Order Placed! ID: `{order.id}` | Status: **{order.status}** | {side.upper()} {qty} share(s) of **{symbol.upper()}**"
    except Exception as e:
        return f"Trade Failed: {e}"

# UI Header
st.title("📈 Trade-Bot: AI Trading Assistant")
st.caption("Powered by Google Gemini AI & Alpaca Paper Trading")

# Sidebar Controls
st.sidebar.header("Quick Controls")
if st.sidebar.button("Check Account Balance"):
    st.sidebar.info(get_account_status())

with st.sidebar.expander("Place Paper Trade"):
    trade_symbol = st.text_input("Ticker Symbol", "AAPL").upper()
    trade_qty = st.number_input("Quantity", min_value=1, value=1)
    if st.button("Submit Buy Order"):
        res = execute_market_trade(trade_symbol, trade_qty, "buy")
        st.sidebar.success(res)

# Interactive Chat Interface
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if user_prompt := st.chat_input("Ask Gemini about market concepts or trading strategies..."):
    st.chat_message("user").markdown(user_prompt)
    st.session_state.messages.append({"role": "user", "content": user_prompt})

    with st.chat_message("assistant"):
        if ai_client:
            try:
                response = ai_client.models.generate_content(
                    model="gemini-3.6-flash",
                    contents=user_prompt,
                )
                bot_reply = response.text
            except Exception as e:
                bot_reply = f"Error generating response: {e}"
        else:
            bot_reply = "Gemini API key is not configured."
        
        st.markdown(bot_reply)
        st.session_state.messages.append({"role": "assistant", "content": bot_reply})