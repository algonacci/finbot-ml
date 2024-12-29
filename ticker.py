from flask_smorest import Blueprint
from flask import jsonify, request
from auth import auth
from cache import cache
from rate_limiter import limiter
import yfinance as yf
import os
import matplotlib
from helpers import get_youtube_videos
from news import get_news
import pandas as pd
from forecast import *

matplotlib.use("Agg")
import matplotlib.pyplot as plt


bp = Blueprint("ticker", "items", description="Operations on ticker endpoint")

PLOTS_DIR = "static/plots"
if not os.path.exists(PLOTS_DIR):
    os.makedirs(PLOTS_DIR)


@bp.route("/ticker", methods=["POST"])
@auth.login_required()
def ticker():
    if request.method == "POST":
        input_data = request.get_json()
        ticker = input_data["ticker"]

        try:
            stock = yf.Ticker(ticker)
            stock_info = stock.info

            if not stock_info:
                return jsonify(
                    {
                        "status": {
                            "code": 404,
                            "message": f"Ticker '{ticker}' not found or invalid.",
                        },
                        "data": None,
                    }
                ), 404

            stock_data = stock.history(period="1y")
            if stock_data.empty:
                return jsonify(
                    {
                        "status": {
                            "code": 404,
                            "message": f"No historical data available for ticker '{ticker}'.",
                        },
                        "data": None,
                    }
                ), 404

            # Create basic price chart
            static_folder = "static"
            if not os.path.exists(static_folder):
                os.makedirs(static_folder)

            plt.figure(figsize=(10, 8))
            plt.plot(stock_data.index, stock_data["Close"], label="Close Price")
            plt.title(f"{ticker} Close Price Over Last Year")
            plt.xlabel("Date")
            plt.ylabel("Close Price")
            plt.legend()
            plt.xticks(rotation=45)

            image_path = os.path.join(static_folder, f"{ticker}_close_price.png")
            plt.savefig(image_path)
            plt.close()

            # Prepare data for forecasting
            stock_data_forecast = stock_data.copy()
            stock_data_forecast = stock_data_forecast.reset_index()
            stock_data_forecast["Date"] = pd.to_datetime(stock_data_forecast["Date"])
            stock_data_forecast["Date"] = stock_data_forecast["Date"].dt.tz_localize(
                None
            )

            # Split data while maintaining Date column
            train_data = stock_data_forecast.iloc[
                : int(len(stock_data_forecast) * 0.85)
            ]
            test_data = stock_data_forecast.iloc[int(len(stock_data_forecast) * 0.85) :]
            forecast_days = determine_forecast_days("1y")

            # Generate forecasts using Holt-Winters
            hw_test_predictions, hw_future_predictions, hw_model = holtwinters_forecast(
                train_data, test_data, forecast_days, "1y"
            )

            # Prepare forecast results
            last_date = stock_data_forecast["Date"].iloc[-1]
            future_dates = pd.date_range(
                start=last_date + timedelta(days=1), periods=forecast_days, freq="D"
            )

            results_hw = pd.DataFrame(
                {
                    "Date": future_dates,
                    "HoltWinters_Predicted_Close": hw_future_predictions,
                }
            )

            hw_last_row = results_hw.iloc[-1]

            # Generate evaluation metrics
            hw_evaluation = evaluate_model(test_data, hw_test_predictions)

            # Create forecast plots
            plot_file_hw = os.path.join(PLOTS_DIR, f"{ticker}_holtwinters.png")
            plot_predictions(
                stock_data_forecast,
                train_data,
                test_data,
                hw_test_predictions,
                results_hw,
                "Holt-Winters Prediction vs Actual",
                plot_file_hw,
            )

            # Get videos and news
            videos = get_youtube_videos(
                stock_info.get("longName", stock_info.get("shortName", ticker))
            )

            news = get_news(
                stock_info.get("longName", stock_info.get("shortName", ticker))
            )

            # Prepare response with forecasting data
            response = {
                "status": {
                    "code": 200,
                    "message": "Success",
                },
                "data": {
                    "stock_info": {
                        "name": stock_info.get(
                            "longName", stock_info.get("shortName", ticker)
                        ),
                        "current_price": stock_info.get(
                            "regularMarketPrice", stock_info.get("currentPrice")
                        ),
                        "symbol": stock_info.get("symbol", ticker),
                        "currency": stock_info.get(
                            "currency", "IDR" if ".JK" in ticker else "USD"
                        ),
                        "market_cap": stock_info.get("marketCap", "Not Available"),
                        "sector": stock_info.get("sector", "Not Available"),
                        "industry": stock_info.get("industry", "Not Available"),
                        "description": stock_info.get(
                            "longBusinessSummary", "No description available"
                        ),
                        "website": stock_info.get("website", "Not Available"),
                        "country": stock_info.get(
                            "country",
                            "Indonesia" if ".JK" in ticker else "Not Available",
                        ),
                        "phone": stock_info.get("phone", "Not Available"),
                        "address": stock_info.get("address1", "Not Available"),
                        "city": stock_info.get("city", "Not Available"),
                        "state": stock_info.get("state", "Not Available"),
                        "zip": stock_info.get("zip", "Not Available"),
                        "full_time_employees": stock_info.get(
                            "fullTimeEmployees", "Not Available"
                        ),
                        "chart_url": f"{request.host_url}{image_path}",
                    },
                    "stock_data": stock_data[["Close"]]
                    .reset_index()
                    .to_dict(orient="records"),
                    "forecasting": {
                        "charts": {
                            "holtwinters_chart": f"{request.host_url}{plot_file_hw}",
                        },
                        "metrics": {
                            "holtwinters": {
                                "mape": float(hw_evaluation["mape"]),
                                "rmse": float(hw_evaluation["rmse"]),
                            },
                        },
                        "last_prediction": {
                            "holtwinters": {
                                "date": hw_last_row["Date"].strftime("%Y-%m-%d"),
                                "predicted_close": float(
                                    hw_last_row["HoltWinters_Predicted_Close"]
                                ),
                            },
                        },
                    },
                },
                "videos": videos,
                "news": news,
            }

            return jsonify(response), 200

        except Exception as e:
            error_message = str(e)
            if "No data found" in error_message or "not found" in error_message.lower():
                message = f"Ticker '{ticker}' not found or may be delisted."
            else:
                message = f"Error processing ticker '{ticker}': {error_message}"

            return jsonify(
                {"status": {"code": 404, "message": message}, "data": None}
            ), 404

    return jsonify(
        {"status": {"code": 405, "message": "Invalid request method"}, "data": None}
    ), 405
