import matplotlib.pyplot as plt


def split_data(stock_data, period):
    if period == "1mo":
        train_size = int(len(stock_data) * 0.75)  # 3 minggu untuk train
    elif period == "3mo":
        train_size = int(len(stock_data) * 0.85)  # 10 minggu untuk train
    elif period == "6mo":
        train_size = int(len(stock_data) * 0.85)  # 5 bulan untuk train
    elif period == "1y":
        train_size = int(len(stock_data) * 0.85)  # 10 bulan untuk train
    elif period == "2y":
        train_size = int(len(stock_data) * 0.85)  # 20 bulan untuk train
    elif period == "5y":
        train_size = int(len(stock_data) * 0.80)  # 4 tahun untuk train
    elif period == "10y":
        train_size = int(len(stock_data) * 0.80)  # 8 tahun untuk train
    elif period == "ytd":
        train_size = int(len(stock_data) * 0.80)  # 80% YTD untuk train
    else:
        raise ValueError("Period tidak dikenali")

    train_data = stock_data.iloc[:train_size]
    test_data = stock_data.iloc[train_size:]

    return train_data, test_data


from statsmodels.tsa.holtwinters import ExponentialSmoothing
from prophet import Prophet
import pandas as pd
from sklearn.metrics import mean_absolute_percentage_error, mean_squared_error
import numpy as np
from datetime import timedelta


def determine_forecast_days(period):
    """Menentukan jumlah hari forecast berdasarkan periode data"""
    if period == "1mo":
        return 7  # 1 minggu ke depan
    elif period == "3mo":
        return 21  # 1 bulan ke depan
    elif period == "6mo":
        return 30  # 1.5 bulan ke depan
    elif period == "1y":
        return 60  # 2 bulan ke depan
    elif period == "2y":
        return 90  # 3 bulan ke depan
    elif period == "5y":
        return 180  # 6 bulan ke depan
    elif period == "10y":
        return 365  # 1 tahun ke depan
    elif period == "ytd":
        return 90  # 3 bulan ke depan
    else:
        return 30  # default


def determine_seasonal_period(period):
    """Menentukan seasonal period berdasarkan timeframe data"""
    if period in ["1mo", "3mo"]:
        return 5  # Weekly seasonality
    elif period in ["6mo", "1y"]:
        return 21  # Monthly seasonality
    else:
        return 63  # Quarterly seasonality


def holtwinters_forecast(train_data, test_data, future_days, period):
    """Implementasi forecasting menggunakan Holt-Winters"""
    seasonal_period = determine_seasonal_period(period)

    model = ExponentialSmoothing(
        train_data["Close"],
        seasonal_periods=seasonal_period,
        trend="add",
        seasonal="add",
        initialization_method="estimated",
    )
    fitted_model = model.fit()

    # Predictions
    test_predictions = fitted_model.forecast(len(test_data))
    future_predictions = fitted_model.forecast(future_days)

    return test_predictions, future_predictions, fitted_model


def prophet_forecast(train_data, test_data, future_days):
    """Implementasi forecasting menggunakan Prophet"""
    # Prepare data for Prophet
    train_prophet = train_data[["Date", "Close"]].copy()
    train_prophet.columns = ["ds", "y"]

    # Create the Prophet model
    model = Prophet(
        daily_seasonality=True,  # kalau benar-benar butuh harian
        yearly_seasonality=True,  # yearly masih dinyalakan
        weekly_seasonality=False,  # mematikan mingguan jika tidak perlu
        n_changepoints=5,  # default ~25, coba turunkan
        seasonality_mode="additive",  # gunakan 'additive' daripada 'multiplicative' jika pola data sesuai
    )

    # Lalu saat fit, tambahkan control param
    model.fit(
        train_prophet,
        control={
            "max_treedepth": 10,  # menurunkan tree depth (default 10, bisa lebih rendah)
            "adapt_delta": 0.8,  # menyesuaikan threshold adaptasi
        },
    )

    # Create future dataframe
    future_dates = pd.date_range(
        start=train_data["Date"].iloc[-1] + timedelta(days=1),
        periods=len(test_data) + future_days,
        freq="D",
    )
    future_df = pd.DataFrame({"ds": future_dates})

    # Make predictions
    forecast = model.predict(future_df)
    test_predictions = forecast["yhat"][: len(test_data)].values
    future_predictions = forecast["yhat"][len(test_data) :].values

    return test_predictions, future_predictions, model


def evaluate_model(test_data, predictions):
    """Menghitung metrik evaluasi untuk model"""
    mape = mean_absolute_percentage_error(test_data["Close"], predictions)
    rmse = np.sqrt(mean_squared_error(test_data["Close"], predictions))
    return {"mape": mape, "rmse": rmse}


def plot_predictions(
    stock_data,
    train_data,
    test_data,
    test_predictions,
    prediction_data,
    title,
    save_path,
):
    """Plot actual stock data with train, test, and future predictions."""
    plt.figure(figsize=(14, 8))

    # Plot the training data
    plt.plot(
        train_data["Date"],
        train_data["Close"],
        label="Train Data",
        color="blue",
        linewidth=2,
    )

    # Plot the actual test data
    plt.plot(
        test_data["Date"],
        test_data["Close"],
        label="Actual Test Data",
        color="purple",
        linewidth=2,
    )

    # Plot the test predictions
    plt.plot(
        test_data["Date"],
        test_predictions,
        label="Test Predictions",
        linestyle="--",
        color="orange",
        marker="o",
        linewidth=2,
    )

    # Plot the future predictions
    plt.plot(
        prediction_data["Date"],
        prediction_data.iloc[:, 1],
        label="Future Predictions",
        linestyle=":",
        color="green",
        linewidth=2,
    )

    plt.title(title, fontsize=16)
    plt.xlabel("Date", fontsize=14)
    plt.ylabel("Stock Price", fontsize=14)
    plt.legend(fontsize=12)
    plt.grid(True)
    plt.xticks(rotation=45)

    plt.tight_layout()
    plt.savefig(save_path)
    plt.close()
