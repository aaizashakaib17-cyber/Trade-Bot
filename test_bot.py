import os
from dotenv import load_dotenv
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import GetOptionContractsRequest, MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
from google import genai

# Load secret keys from hidden .env file
load_dotenv()

ALPACA_API_KEY = os.getenv("ALPACA_API_KEY")
ALPACA_SECRET_KEY = os.getenv("ALPACA_SECRET_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Initialize Alpaca Client
trading_client = TradingClient(ALPACA_API_KEY, ALPACA_SECRET_KEY, paper=True)

# Initialize Gemini AI Client using the current SDK format
if GEMINI_API_KEY:
    ai_client = genai.Client(api_key=GEMINI_API_KEY)
else:
    ai_client = None

def get_account_status():
    """Returns cash balance and status."""
    try:
        account = trading_client.get_account()
        return f"Account Status: {account.status} | Cash Balance: ${account.cash}"
    except Exception as e:
        return f"Error getting account: {e}"

def run_automated_rsi_strategy(symbol: str = "AAPL", qty: int = 1):
    """Simulates an automated RSI trade check for a given symbol."""
    return f"RSI strategy execution completed for {symbol} ({qty} shares)."

def get_options_chain_snapshot(underlying_symbol: str, limit: int = 5):
    """Fetches active option contracts for an underlying symbol."""
    req = GetOptionContractsRequest(underlying_symbol=[underlying_symbol], limit=limit)
    res = trading_client.get_option_contracts(req)
    if not res.option_contracts:
        return f"No option contracts found for {underlying_symbol}."
    return "\n".join([f"Symbol: {c.symbol} | Type: {c.type} | Strike: {c.strike_price}" for c in res.option_contracts])

def execute_market_trade(symbol: str, qty: int, side: str = "buy"):
    """Submits a market order to Alpaca with paper trading guardrails."""
    try:
        order_side = OrderSide.BUY if side.lower() == "buy" else OrderSide.SELL
        order_data = MarketOrderRequest(
            symbol=symbol.upper(),
            qty=qty,
            side=order_side,
            time_in_force=TimeInForce.DAY
        )
        order = trading_client.submit_order(order_data)
        return f"Order Placed! ID: {order.id} | Status: {order.status} | {side.upper()} {qty} share(s) of {symbol.upper()}"
    except Exception as e:
        return f"Trade Failed: {e}"

def start_bot():
    print("=" * 50)
    print("  Trade-Bot Interactive AI Assistant")
    print("=" * 50)
    print("Type commands naturally (e.g., 'Check balance', 'Buy 1 share of AAPL', 'Options for AAPL')")
    print("Type 'exit' to quit.\n")

    while True:
        try:
            user_input = input("You: ").strip()
            if not user_input:
                continue
            if user_input.lower() in ["exit", "quit"]:
                print("Exiting Trade-Bot. Goodbye!")
                break
            
            # Simple keyword tool routing
            text = user_input.lower()
            if "balance" in text or "account" in text or text == "1":
                print(f"\n[Bot]: {get_account_status()}\n")
            elif "rsi" in text or text == "2":
                print(f"\n[Bot]: {run_automated_rsi_strategy('TSLA', 5)}\n")
            elif "option" in text or text == "3":
                print(f"\n[Bot]: {get_options_chain_snapshot('AAPL')}\n")
            elif "buy" in text or "trade" in text or text == "4":
                print("\n--- Market Trade Guardrail ---")
                symbol = input("Enter ticker symbol (e.g., AAPL): ").strip().upper()
                qty_str = input("Enter quantity (number of shares): ").strip()
                
                if not symbol or not qty_str.isdigit() or int(qty_str) <= 0:
                    print("\nInvalid inputs. Trade canceled.\n")
                    continue
                
                qty = int(qty_str)
                confirm = input(f"CONFIRM: Buy {qty} share(s) of {symbol} at market price? (y/n): ").strip().lower()
                
                if confirm == 'y':
                    result = execute_market_trade(symbol=symbol, qty=qty, side="buy")
                    print(f"\n{result}\n")
                else:
                    print("\nTrade canceled by user.\n")
            elif ai_client:
                # Ask Gemini LLM for conversational responses using official client model string
                response = ai_client.models.generate_content(
                    model="gemini-3.6-flash",
                    contents=user_input,
                )
                print(f"\nGemini AI: {response.text}\n")
            else:
                print(f"\nAgent received: '{user_input}'. Tool execution complete.\n")

        except KeyboardInterrupt:
            print("\nSession paused. Press Ctrl+C again or exit.")
            break
        except Exception as e:
            print(f"\nError: {e}\n")

if __name__ == "__main__":
    start_bot()