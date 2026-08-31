import os
import streamlit as st
from dotenv import load_dotenv
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
from google import genai

# Page Configuration
st.set_page_config(page_title="Trade-Bot", layout="wide")
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# Add your uploaded logo here
st.logo("Gemini_Generated_Image_plxvuplxvuplxvup.jpeg")

# Simple Email Sign-In Gate
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.user_email = ""

if not st.session_state.authenticated:
    st.subheader("Sign In to Trade-Bot")
    email_input = st.text_input("Enter your Email Address")
    
    if st.button("Continue"):
        if "@" in email_input and "." in email_input:
            st.session_state.authenticated = True
            st.session_state.user_email = email_input
            st.rerun()
        else:
            st.error("Please enter a valid email address.")
    st.stop()

# Load environment variables
load_dotenv()

# API Keys setup
ALPACA_API_KEY = os.getenv("ALPACA_API_KEY")
ALPACA_SECRET_KEY = os.getenv("ALPACA_SECRET_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Initialize Alpaca Client (Paper Trading)
trading_client = None
if ALPACA_API_KEY and ALPACA_SECRET_KEY:
    try:
        trading_client = TradingClient(ALPACA_API_KEY, ALPACA_SECRET_KEY, paper=True)
    except Exception as e:
        st.error(f"Error initializing Alpaca client: {e}")

# Initialize Gemini AI Client
ai_client = None
if GEMINI_API_KEY:
    try:
        ai_client = genai.Client(api_key=GEMINI_API_KEY)
    except Exception as e:
        st.error(f"Error initializing Gemini client: {e}")

# App Header
st.title("Trade-Bot: AI Trading Assistant")
st.markdown(f"Welcome, **{st.session_state.user_email}** | Powered by Google Gemini AI & Alpaca Paper Trading")

# Sidebar Controls
st.sidebar.markdown("### Quick Controls")

if st.sidebar.button("Check Account Balance"):
    if trading_client:
        try:
            account = trading_client.get_account()
            st.sidebar.success(f"Account Status: {account.status} | Cash Balance: ${float(account.cash):,.2f}")
        except Exception as e:
            st.sidebar.error(f"Failed to fetch account: {e}")
    else:
        st.sidebar.error("Alpaca credentials missing.")

st.sidebar.markdown("---")
st.sidebar.markdown("### Place Paper Trade")
trade_symbol = st.sidebar.text_input("Ticker Symbol", value="AAPL")
trade_qty = st.sidebar.number_input("Quantity", min_value=1, value=1, step=1)

if st.sidebar.button("Submit Buy Order"):
    if trading_client:
        try:
            market_order_data = MarketOrderRequest(
                symbol=trade_symbol.upper(),
                qty=trade_qty,
                side=OrderSide.BUY,
                time_in_force=TimeInForce.IOC
            )
            market_order = trading_client.submit_order(order_data=market_order_data)
            st.sidebar.success(f"Successfully bought {trade_qty} share(s) of {trade_symbol.upper()}!")
        except Exception as e:
            st.sidebar.error(f"Order failed: {e}")
    else:
        st.sidebar.error("Alpaca client not initialized.")

# Chat Interface with Gemini AI
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
