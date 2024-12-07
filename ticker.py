from flask_smorest import Blueprint
from flask import jsonify, request
from auth import auth
from cache import cache
from rate_limiter import limiter
import yfinance as yf
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt





bp = Blueprint("ticker", "items", description="Operations on ticker endpoint")


@bp.route("/ticker", methods=["POST"])
@auth.login_required()
def ticker():
    if request.method == "POST":
        input_data = request.get_json()
        ticker = input_data["ticker"]
        
        try:
            stock = yf.Ticker(ticker)
            
            # Get stock info
            stock_info = stock.info
            
            # Basic validation - hanya cek apakah ada data dasar
            if not stock_info:
                return jsonify({
                    "status": {
                        "code": 404,
                        "message": f"Ticker '{ticker}' not found or invalid."
                    },
                    "data": None
                }), 404
            
            # Get historical data
            stock_data = stock.history(period="1y")
            if stock_data.empty:
                return jsonify({
                    "status": {
                        "code": 404,
                        "message": f"No historical data available for ticker '{ticker}'."
                    },
                    "data": None
                }), 404
            
            # Create plot
            static_folder = 'static'
            if not os.path.exists(static_folder):
                os.makedirs(static_folder)
                
            plt.figure(figsize=(10, 8))
            plt.plot(stock_data.index, stock_data['Close'], label='Close Price')
            plt.title(f'{ticker} Close Price Over Last Year')
            plt.xlabel('Date')
            plt.ylabel('Close Price')
            plt.legend()
            plt.xticks(rotation=45)
            
            image_path = os.path.join(static_folder, f'{ticker}_close_price.png')
            plt.savefig(image_path)
            plt.close()
            
            # Prepare response with more flexible field handling
            response = {
                "status": {
                    "code": 200,
                    "message": "Success",
                },
                "data": {
                    "stock_info": {
                        "name": stock_info.get('longName', stock_info.get('shortName', ticker)),
                        "current_price": stock_info.get('regularMarketPrice', stock_info.get('currentPrice')),
                        "symbol": stock_info.get('symbol', ticker),
                        "currency": stock_info.get('currency', 'IDR' if '.JK' in ticker else 'USD'),
                        "market_cap": stock_info.get('marketCap', 'Not Available'),
                        "sector": stock_info.get('sector', 'Not Available'),
                        "industry": stock_info.get('industry', 'Not Available'),
                        "description": stock_info.get('longBusinessSummary', 'No description available'),
                        "website": stock_info.get('website', 'Not Available'),
                        "country": stock_info.get('country', 'Indonesia' if '.JK' in ticker else 'Not Available'),
                        "phone": stock_info.get('phone', 'Not Available'),
                        "address": stock_info.get('address1', 'Not Available'),
                        "city": stock_info.get('city', 'Not Available'),
                        "state": stock_info.get('state', 'Not Available'),
                        "zip": stock_info.get('zip', 'Not Available'),
                        "full_time_employees": stock_info.get('fullTimeEmployees', 'Not Available'),
                        "chart_url": f'{request.host_url}{image_path}'
                    },
                    "stock_data": stock_data[['Close']].reset_index().to_dict(orient='records')
                }
            }
            
            return jsonify(response), 200
            
        except Exception as e:
            error_message = str(e)
            if "No data found" in error_message or "not found" in error_message.lower():
                message = f"Ticker '{ticker}' not found or may be delisted."
            else:
                message = f"Error processing ticker '{ticker}': {error_message}"
                
            return jsonify({
                "status": {
                    "code": 404,
                    "message": message
                },
                "data": None
            }), 404
            
    return jsonify({
        "status": {
            "code": 405,
            "message": "Invalid request method"
        },
        "data": None
    }), 405
