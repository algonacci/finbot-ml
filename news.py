from gnews import GNews

google_news = GNews(
    language="id",
    country="ID",
    max_results=10,
)

def get_news(ticker):
    news = google_news.get_news(ticker)
    return news