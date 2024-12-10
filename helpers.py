import yfinance as yf
import pandas as pd

def get_stock_data(ticker):
    try:
        # Get stock info
        stock = yf.Ticker(ticker)
        
        # Get key data
        info = stock.info
        
        # Get historical data (1 year)
        hist = stock.history(period="1mo")
        
        # Calculate some basic metrics
        latest_price = hist['Close'].iloc[-1]
        price_change = hist['Close'].iloc[-1] - hist['Close'].iloc[-2]
        price_change_percent = (price_change / hist['Close'].iloc[-2]) * 100
        
        # Create a structured response
        data = {
            "error": False,
            "data": {
                "symbol": ticker,
                "company_name": info.get('longName', ''),
                "current_price": latest_price,
                "currency": info.get('currency', ''),
                "daily_change": {
                    "value": round(price_change, 2),
                    "percentage": round(price_change_percent, 2)
                },
                "market_cap": info.get('marketCap', None),
                "volume": info.get('volume', None),
                "pe_ratio": info.get('trailingPE', None),
                "earnings_per_share": info.get('trailingEps', None),
                "52_week": {
                    "high": info.get('fiftyTwoWeekHigh', None),
                    "low": info.get('fiftyTwoWeekLow', None)
                },
                "historical_data": {
                    "dates": hist.index.strftime('%Y-%m-%d').tolist(),
                    "prices": hist['Close'].round(2).tolist(),
                    "volumes": hist['Volume'].tolist()
                }
            }
        }
        
        return data
        
    except Exception as e:
        print(f"Error fetching data for {ticker}: {str(e)}")
        return {
            "error": True,
            "message": f"Unable to fetch stock data for {ticker}. Error: {str(e)}",
            "ticker": ticker
        }