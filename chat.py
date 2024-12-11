from flask_smorest import Blueprint
from flask import jsonify, request
from auth import auth
from cache import cache
from rate_limiter import limiter
from helpers import get_stock_data, format_analysis_for_chat
from langchain_core.chat_history import BaseChatMessageHistory, InMemoryChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_openai import ChatOpenAI
import json
import os

bp = Blueprint("chat", "items", description="Operations on ticker endpoint")

# Store for chat histories and ticker data
chat_store = {}
ticker_store = {}

def get_session_history(session_id: str) -> BaseChatMessageHistory:
    """Get or create chat history for a session"""
    if session_id not in chat_store:
        chat_store[session_id] = InMemoryChatMessageHistory()
    return chat_store[session_id]

# Initialize Groq model
model = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0,
    max_tokens=1000
)

# Create runnable with message history
with_message_history = RunnableWithMessageHistory(model, get_session_history)

@bp.route("/get_ticker_data", methods=["GET"])
@limiter.limit("30 per minute")
@cache.cached(timeout=300)  # Cache for 5 minutes
def get_ticker_data():
    """Get stock data for specified tickers"""
    session_id = request.args.get("session_id")
    tickers = request.args.get("tickers")
    
    if not session_id or not tickers:
        return jsonify({
            "status": {
                "code": 400,
                "message": "Session ID and tickers are required"
            },
            "data": None
        }), 400
        
    try:
        # Get and store stock data for the session
        stock_data = get_stock_data(tickers)
        
        if stock_data.get("error", False):
            return jsonify({
                "status": {
                    "code": 400,
                    "message": stock_data.get("message", "Error fetching stock data")
                },
                "data": None
            }), 400
        
        # Store the data
        ticker_store[session_id] = {
            "tickers": tickers,
            "data": stock_data
        }
        
        return jsonify({
            "status": {
                "code": 200,
                "message": "Success"
            },
            "data": stock_data
        }), 200
        
    except Exception as e:
        return jsonify({
            "status": {
                "code": 500,
                "message": f"Server error: {str(e)}"
            },
            "data": None
        }), 500

@bp.route("/chat", methods=["POST"])
@auth.login_required()
@limiter.limit("60 per minute")
def chat():
    """Process chat messages with stock analysis context"""
    if request.method != "POST":
        return jsonify({
            "status": {
                "code": 405,
                "message": "Invalid request method"
            },
            "data": None
        }), 405
        
    try:
        input_data = request.get_json()
        messages = input_data.get("messages")
        session_id = input_data.get("session_id")
        
        if not session_id or not messages:
            return jsonify({
                "status": {
                    "code": 400,
                    "message": "Session ID and messages are required"
                },
                "data": None
            }), 400
            
        # Get stored ticker data
        ticker_data = ticker_store.get(session_id)
        
        if not ticker_data:
            return jsonify({
                "status": {
                    "code": 400,
                    "message": "No ticker data found for this session. Please call /get_ticker_data first"
                },
                "data": None
            }), 400
        
        # Format the analysis for the chat context
        analysis = format_analysis_for_chat(ticker_data['data'])
        
        # Prepare context
        context = f"""
        You are a helpful financial analyst. You are analyzing stock data for {ticker_data['tickers']}.
        
        Here is the current analysis:
        {analysis}
        
        Previous conversation context is maintained automatically.
        Please provide insights based on the user's question, using the data provided.
        If any data is missing or invalid, acknowledge this and work with the available information.
        """
        
        # Get AI response
        ai_response = with_message_history.invoke(
            {"input": f"{context}\n\nUser: {messages[-1]}"},
            config={"configurable": {"session_id": session_id}}
        )
        
        response_content = ai_response.content if hasattr(ai_response, 'content') else str(ai_response)
        
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
        return jsonify({
            "status": {
                "code": 500,
                "message": f"Error processing chat request: {str(e)}"
            },
            "data": None
        }), 500