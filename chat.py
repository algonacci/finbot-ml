from flask_smorest import Blueprint
from flask import jsonify, request
from auth import auth
from cache import cache
from rate_limiter import limiter
from helpers import get_stock_data
from langchain_core.chat_history import BaseChatMessageHistory, InMemoryChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_openai import ChatOpenAI
import json

bp = Blueprint("chat", "items", description="Operations on ticker endpoint")

# Store for chat histories and ticker data
chat_store = {}
ticker_store = {}

def get_session_history(session_id: str) -> BaseChatMessageHistory:
    """Get or create chat history for a session"""
    if session_id not in chat_store:
        chat_store[session_id] = InMemoryChatMessageHistory()
    return chat_store[session_id]

# Initialize ChatOpenAI model
model = ChatOpenAI(temperature=0)

# Create runnable with message history
with_message_history = RunnableWithMessageHistory(model, get_session_history)

@bp.route("/get_ticker_data", methods=["GET"])
def get_ticker_data():
    session_id = request.args.get("session_id")
    tickers = request.args.get("tickers")
    
    if not session_id:
        return jsonify({
            "status": {
                "code": 400,
                "message": "Session ID is required"
            },
            "data": None
        }), 400
        
    # Get and store stock data for the session
    stock_data = get_stock_data(tickers)
    print("Stock Data Response:", stock_data)  # Debug print
    
    # Store the data
    ticker_store[session_id] = {
        "tickers": tickers,
        "data": stock_data
    }
    print("Stored ticker data for session:", session_id, ticker_store[session_id])  # Debug print
    
    return jsonify({
        "status": {
            "code": 200,
            "message": "Success"
        },
        "data": stock_data
    }), 200

@bp.route("/chat", methods=["POST"])
@auth.login_required()
def chat():
    if request.method == "POST":
        input_data = request.get_json()
        messages = input_data["messages"]
        session_id = input_data.get("session_id")
        
        if not session_id:
            return jsonify({
                "status": {
                    "code": 400,
                    "message": "Session ID is required"
                },
                "data": None
            }), 400
            
        # Get stored ticker data for the session
        ticker_data = ticker_store.get(session_id)
        print("Retrieved ticker data for session:", session_id, ticker_data)  # Debug print
        
        if not ticker_data:
            return jsonify({
                "status": {
                    "code": 400,
                    "message": "No ticker data found for this session. Please call /get_ticker_data first"
                },
                "data": None
            }), 400
        
        # Prepare context for the AI
        context = f"""
        You are a helpful financial analyst. You are analyzing stock data for {ticker_data['tickers']}.
        Here is the current data:
        {json.dumps(ticker_data['data'], indent=2)}
        
        Previous conversation context is maintained automatically.
        Please analyze this data and provide insights based on the user's question.
        If there's missing or invalid data, politely inform the user and work with whatever data is available.
        """
        
        print("Context for AI:", context)  # Debug print
        
        try:
            # Get response using the runnable with history
            ai_response = with_message_history.invoke(
                {"input": f"{context}\n\nUser: {messages[-1]}"},
                config={"configurable": {"session_id": session_id}}
            )
            
            # Extract the content from AIMessage
            response_content = ai_response.content if hasattr(ai_response, 'content') else str(ai_response)
            print("AI Response:", response_content)  # Debug print
            
            return jsonify({
                "status": {
                    "code": 200,
                    "message": "Success"
                },
                "data": {
                    "response": response_content,
                    "stock_data": ticker_data['data']
                }
            }), 200
            
        except Exception as e:
            print(f"Error processing chat: {str(e)}")
            return jsonify({
                "status": {
                    "code": 500,
                    "message": "Error processing chat request"
                },
                "data": None
            }), 500
            
    else:
        return jsonify({
            "status": {
                "code": 405,
                "message": "Invalid request method"
            },
            "data": None
        }), 405