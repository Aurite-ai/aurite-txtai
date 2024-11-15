import os
import sys

# Add the project root directory to sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, project_root)

from newsapi import NewsApiClient

from src.middleware.logging_config import api_logger


class NewsAPIClient:
    def __init__(self):
        api_key = os.environ.get("NEWS_API_KEY")
        if not api_key:
            api_logger.error("NEWS_API_KEY not found in environment variables")
            raise ValueError("NEWS_API_KEY not set")

        self.newsapi = NewsApiClient(api_key=api_key)
        api_logger.info("NewsAPI client initialized")

    def get_top_headlines(self, query, limit=5):
        try:
            headlines = self.newsapi.get_top_headlines(
                q=query,
                language="en",
                country="us",  # Added country parameter
                page_size=limit,
            )
            api_logger.info(f"API Response: {headlines}")
            if headlines["status"] == "ok":
                api_logger.info(
                    f"Successfully fetched {len(headlines['articles'])} headlines for query: {query}"
                )
                return headlines["articles"]
            else:
                api_logger.error(f"API returned status: {headlines['status']}")
                return []
        except Exception as e:
            api_logger.error(f"Error fetching news: {str(e)}")
            return []

    def get_everything(self, query, limit=5):
        try:
            articles = self.newsapi.get_everything(
                q=query, language="en", sort_by="publishedAt", page_size=limit
            )
            api_logger.info(f"API Response: {articles}")
            if articles["status"] == "ok":
                api_logger.info(
                    f"Successfully fetched {len(articles['articles'])} articles for query: {query}"
                )
                return articles["articles"]
            else:
                api_logger.error(f"API returned status: {articles['status']}")
                return []
        except Exception as e:
            api_logger.error(f"Error fetching news: {str(e)}")
            return []


# In the __main__ section:
if __name__ == "__main__":
    client = NewsAPIClient()
    articles = client.get_everything("python")
    for article in articles:
        print(f"Title: {article['title']}")
        print(f"Description: {article['description']}")
        print("---")
