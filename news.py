from gnews import GNews

google_news = GNews(
    language="id",
    country="ID",
    max_results=10,
)
news = google_news.get_news("BREN")
print(news)
