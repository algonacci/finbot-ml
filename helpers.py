import yfinance as yf
import pandas as pd
from typing import Dict, Any, Optional
import numpy as np

def fetch_stock_data(stock: str) -> yf.Ticker:
    """Fetch stock data"""
    return yf.Ticker(stock)

def get_stock_history(stock: str) -> Dict[str, Any]:
    """Get stock price history for the last month"""
    try:
        stock_data = fetch_stock_data(stock)
        hist = stock_data.history(period="1mo")
        return {
            "error": False,
            "data": hist.to_dict()
        }
    except Exception as e:
        return {
            "error": True,
            "message": f"Error fetching history for {stock}: {str(e)}"
        }

def get_stock_info(stock: str) -> Dict[str, Any]:
    """Get general stock information and metrics"""
    try:
        stock_data = fetch_stock_data(stock)
        return {
            "error": False,
            "data": stock_data.info
        }
    except Exception as e:
        return {
            "error": True,
            "message": f"Error fetching info for {stock}: {str(e)}"
        }

def get_balance_sheet(stock: str) -> Dict[str, Any]:
    """Get stock balance sheet data"""
    try:
        stock_data = fetch_stock_data(stock)
        balance_sheet = stock_data.balance_sheet.fillna(np.nan).replace({np.nan: None})
        return {
            "error": False,
            "data": balance_sheet.to_dict()
        }
    except Exception as e:
        return {
            "error": True,
            "message": f"Error fetching balance sheet for {stock}: {str(e)}"
        }

def get_stock_data(ticker: str) -> Dict[str, Any]:
    """Get comprehensive stock data"""
    try:
        # Fetch all data components
        info_result = get_stock_info(ticker)
        history_result = get_stock_history(ticker)
        balance_result = get_balance_sheet(ticker)
        
        if info_result["error"] or history_result["error"] or balance_result["error"]:
            return {
                "error": True,
                "message": "Error fetching some data components",
                "details": {
                    "info": info_result.get("message", ""),
                    "history": history_result.get("message", ""),
                    "balance": balance_result.get("message", "")
                }
            }
        
        # Get key data
        info = info_result["data"]
        hist = pd.DataFrame(history_result["data"])
        balance = balance_result["data"]
        
        # Calculate metrics
        latest_price = hist['Close'].iloc[-1] if not hist.empty else None
        price_change = (hist['Close'].iloc[-1] - hist['Close'].iloc[-2]) if not hist.empty else None
        price_change_percent = ((price_change / hist['Close'].iloc[-2]) * 100) if price_change is not None else None
        
        # Get most recent balance sheet data
        recent_balance = list(balance.values())[0] if balance else {}
        
        return {
            "error": False,
            "data": {
                "symbol": ticker,
                "company_name": info.get('longName', ''),
                "current_price": latest_price,
                "currency": info.get('currency', ''),
                "daily_change": {
                    "value": round(price_change, 2) if price_change is not None else None,
                    "percentage": round(price_change_percent, 2) if price_change_percent is not None else None
                },
                "address": {
                    "line1": info.get('address1', ''),
                    "line2": info.get('address2', ''),
                    "city": info.get('city', ''),
                    "zip": info.get('zip', ''),
                    "country": info.get('country', '')
                },
                "contact": {
                    "phone": info.get('phone', ''),
                    "fax": info.get('fax', ''),
                    "website": info.get('website', '')
                },
                "company_info": {
                    "industry": info.get('industry', ''),
                    "sector": info.get('sector', ''),
                    "long_business_summary": info.get('longBusinessSummary', '')
                },
                "officers": [
                    {
                        "name": officer.get('name', ''),
                        "age": officer.get('age', None),
                        "title": officer.get('title', ''),
                        "year_born": officer.get('yearBorn', None),
                        "exercised_value": officer.get('exercisedValue', 0),
                        "unexercised_value": officer.get('unexercisedValue', 0)
                    } for officer in info.get('companyOfficers', [])
                ],
                "ir_website": info.get('irWebsite', ''),
                "max_age": info.get('maxAge', 0),
                "price_hint": info.get('priceHint', 0),
                "previous_close": info.get('previousClose', 0),
                "open": info.get('open', 0),
                "day_low": info.get('dayLow', 0),
                "day_high": info.get('dayHigh', 0),
                "regular_market_previous_close": info.get('regularMarketPreviousClose', 0),
                "regular_market_open": info.get('regularMarketOpen', 0),
                "regular_market_day_low": info.get('regularMarketDayLow', 0),
                "regular_market_day_high": info.get('regularMarketDayHigh', 0),
                "dividend_rate": info.get('dividendRate', 0),
                "dividend_yield": info.get('dividendYield', 0),
                "ex_dividend_date": info.get('exDividendDate', 0),
                "payout_ratio": info.get('payoutRatio', 0),
                "five_year_avg_dividend_yield": info.get('fiveYearAvgDividendYield', 0),
                "beta": info.get('beta', 0),
                "trailing_pe": info.get('trailingPE', 0),
                "forward_pe": info.get('forwardPE', 0),
                "volume": info.get('volume', 0),
                "regular_market_volume": info.get('regularMarketVolume', 0),
                "average_volume": info.get('averageVolume', 0),
                "average_volume_10days": info.get('averageVolume10days', 0),
                "average_daily_volume_10day": info.get('averageDailyVolume10Day', 0),
                "bid": info.get('bid', 0),
                "ask": info.get('ask', 0),
                "market_cap": info.get('marketCap', 0),
                "fifty_two_week_low": info.get('fiftyTwoWeekLow', 0),
                "fifty_two_week_high": info.get('fiftyTwoWeekHigh', 0),
                "price_to_sales_trailing_12_months": info.get('priceToSalesTrailing12Months', 0),
                "fifty_day_average": info.get('fiftyDayAverage', 0),
                "two_hundred_day_average": info.get('twoHundredDayAverage', 0),
                "trailing_annual_dividend_rate": info.get('trailingAnnualDividendRate', 0),
                "trailing_annual_dividend_yield": info.get('trailingAnnualDividendYield', 0),
                "currency": info.get('currency', ''),
                "enterprise_value": info.get('enterpriseValue', 0),
                "profit_margins": info.get('profitMargins', 0),
                "float_shares": info.get('floatShares', 0),
                "shares_outstanding": info.get('sharesOutstanding', 0),
                "held_percent_insiders": info.get('heldPercentInsiders', 0),
                "held_percent_institutions": info.get('heldPercentInstitutions', 0),
                "implied_shares_outstanding": info.get('impliedSharesOutstanding', 0),
                "book_value": info.get('bookValue', 0),
                "price_to_book": info.get('priceToBook', 0),
                "last_fiscal_year_end": info.get('lastFiscalYearEnd', 0),
                "next_fiscal_year_end": info.get('nextFiscalYearEnd', 0),
                "most_recent_quarter": info.get('mostRecentQuarter', 0),
                "earnings_quarterly_growth": info.get('earningsQuarterlyGrowth', 0),
                "net_income_to_common": info.get('netIncomeToCommon', 0),
                "trailing_eps": info.get('trailingEps', 0),
                "forward_eps": info.get('forwardEps', 0),
                "last_split_factor": info.get('lastSplitFactor', ''),
                "last_split_date": info.get('lastSplitDate', 0),
                "enterprise_to_revenue": info.get('enterpriseToRevenue', 0),
                "52_week_change": info.get('52WeekChange', 0),
                "sand_p_52_week_change": info.get('SandP52WeekChange', 0),
                "lastDividendValue": info.get('lastDividendValue', 0),
                "lastDividendDate": info.get('lastDividendDate', 0),
                "exchange": info.get('exchange', ''),
                "quoteType": info.get('quoteType', ''),
                "symbol": info.get('symbol', ''),
                "underlyingSymbol": info.get('underlyingSymbol', ''),
                "shortName": info.get('shortName', ''),
                "longName": info.get('longName', ''),
                "firstTradeDateEpochUtc": info.get('firstTradeDateEpochUtc', 0),
                "timeZoneFullName": info.get('timeZoneFullName', ''),
                "timeZoneShortName": info.get('timeZoneShortName', ''),
                "uuid": info.get('uuid', ''),
                "messageBoardId": info.get('messageBoardId', ''),
                "gmtOffSetMilliseconds": info.get('gmtOffSetMilliseconds', 0),
                "currentPrice": info.get('currentPrice', 0),
                "targetHighPrice": info.get('targetHighPrice', 0),
                "targetLowPrice": info.get('targetLowPrice', 0),
                "targetMeanPrice": info.get('targetMeanPrice', 0),
                "targetMedianPrice": info.get('targetMedianPrice', 0),
                "recommendationMean": info.get('recommendationMean', 0),
                "recommendationKey": info.get('recommendationKey', ''),
                "numberOfAnalystOpinions": info.get('numberOfAnalystOpinions', 0),
                "totalCash": info.get('totalCash', 0),
                "totalCashPerShare": info.get('totalCashPerShare', 0),
                "totalDebt": info.get('totalDebt', 0),
                "totalRevenue": info.get('totalRevenue', 0),
                "revenuePerShare": info.get('revenuePerShare', 0),
                "returnOnAssets": info.get('returnOnAssets', 0),
                "returnOnEquity": info.get('returnOnEquity', 0),
                "operatingCashflow": info.get('operatingCashflow', 0),
                "earningsGrowth": info.get('earningsGrowth', 0),
                "revenueGrowth": info.get('revenueGrowth', 0),
                "operatingMargins": info.get('operatingMargins', 0),
                "financialCurrency": info.get('financialCurrency', ''),
                "trailingPegRatio": info.get('trailingPegRatio', 0),
                "market_metrics": {
                    "market_cap": info.get('marketCap', None),
                    "volume": info.get('volume', None),
                    "pe_ratio": info.get('trailingPE', None),
                    "forward_pe": info.get('forwardPE', None),
                    "price_to_book": info.get('priceToBook', None),
                    "dividend_yield": info.get('dividendYield', None)
                },
                "52_week": {
                    "high": info.get('fiftyTwoWeekHigh', None),
                    "low": info.get('fiftyTwoWeekLow', None)
                },
                "balance_sheet": {
                    "total_assets": recent_balance.get('Total Assets', None),
                    "total_liabilities": recent_balance.get('Total Liabilities Net Minority Interest', None),
                    "total_equity": recent_balance.get('Total Equity Gross Minority Interest', None),
                    "cash_and_equivalents": recent_balance.get('Cash And Cash Equivalents', None)
                },
                "historical_data": {
                    "dates": hist.index.strftime('%Y-%m-%d').tolist() if not hist.empty else [],
                    "prices": hist['Close'].round(2).tolist() if not hist.empty else [],
                    "volumes": hist['Volume'].tolist() if not hist.empty else []
                }
            }
        }
        
    except Exception as e:
        return {
            "error": True,
            "message": f"Error analyzing {ticker}: {str(e)}",
            "ticker": ticker
        }

def format_analysis_for_chat(stock_data: Dict[str, Any]) -> str:
    """Format stock data for chat context"""
    if stock_data.get("error", True):
        return f"Error: {stock_data.get('message', 'Unknown error occurred')}"
    
    data = stock_data["data"]
    
    analysis = f"""
Stock Analysis for {data['symbol']}:

1. Basic Information:
- Company Name: {data['company_name']}
- Current Price: {data['current_price']} {data['currency']}
- Daily Change: {data['daily_change']['value']} ({data['daily_change']['percentage']}%)

2. Market Metrics:
- Market Cap: {data['market_metrics']['market_cap']}
- P/E Ratio: {data['market_metrics']['pe_ratio']}
- Forward P/E: {data['market_metrics']['forward_pe']}
- Price to Book: {data['market_metrics']['price_to_book']}
- Dividend Yield: {data['market_metrics']['dividend_yield']}
- Enterprise Value: {data['enterprise_value']}
- Profit Margins: {data['profit_margins']}
- Float Shares: {data['float_shares']}
- Shares Outstanding: {data['shares_outstanding']}
- Held Percent Insiders: {data['held_percent_insiders']}
- Held Percent Institutions: {data['held_percent_institutions']}

3. Trading Range:
- 52-Week High: {data['52_week']['high']}
- 52-Week Low: {data['52_week']['low']}

4. Balance Sheet Highlights:
- Total Assets: {data['balance_sheet']['total_assets']}
- Total Liabilities: {data['balance_sheet']['total_liabilities']}
- Total Equity: {data['balance_sheet']['total_equity']}
- Cash and Equivalents: {data['balance_sheet']['cash_and_equivalents']}
- Book Value: {data['book_value']}
- Price to Book: {data['price_to_book']}

5. Additional Metrics:
- Revenue Per Share: {data['revenuePerShare']}
- Return on Assets: {data['returnOnAssets']}
- Return on Equity: {data['returnOnEquity']}
- Operating Cashflow: {data['operatingCashflow']}
- Earnings Growth: {data['earningsGrowth']}
- Revenue Growth: {data['revenueGrowth']}
- Operating Margins: {data['operatingMargins']}
- Financial Currency: {data['financialCurrency']}
- Trailing PEG Ratio: {data['trailingPegRatio']}

6. Historical Data:
- Dates: {data['historical_data']['dates']}
- Prices: {data['historical_data']['prices']}
- Volumes: {data['historical_data']['volumes']}
"""
    return analysis