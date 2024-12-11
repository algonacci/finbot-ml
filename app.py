import os

from flask import Flask
from flask_cors import CORS
from flask_smorest import Api

from cache import init_cache_app
from rate_limiter import init_rate_limiter
from config import CONFIG
from errors import bp as errors_bp
from index import bp as index_bp
from ticker import bp as ticker_bp
from chat import bp as chat_bp


def create_app():
    app = Flask(__name__, static_folder="static")
    app.config.update(CONFIG)
    CORS(
        app,
        resources={
            r"/*": {
                "origins": ["http://localhost:5173", "https://finbot-fe.vercel.app"]
            },
            r"/static/*": {
                "origins": ["http://localhost:5173", "https://finbot-fe.vercel.app"]
            },
        },
        supports_credentials=True,
        methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
    )
    api = Api(app)

    api.register_blueprint(index_bp)
    api.register_blueprint(errors_bp)
    api.register_blueprint(ticker_bp)
    api.register_blueprint(chat_bp)

    init_cache_app(app)
    init_rate_limiter(app)

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
