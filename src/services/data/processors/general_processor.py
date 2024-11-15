from .base_processor import BaseProcessor


class GeneralProcessor(BaseProcessor):
    def process(self, data):
        text = data.get("content", data.get("cleaned_title", ""))

        keywords = self.keywords(text)
        sentiment = self.compute_sentiment(text)
        summary = self.summarize(text)

        # Ensure sentiment is in the correct format
        if isinstance(sentiment, list) and sentiment:
            sentiment_score = sentiment[0].get("score", 0)
        else:
            sentiment_score = 0

        processed_data = {
            "domain": data.get("domain", "unknown"),
            "content": text,
            "keywords": keywords,
            "sentiment": {"score": sentiment_score},
            "summary": summary,
            "trend": self.extract_trend(text),
            "relevance_score": 0.5,
        }

        return {**data, **processed_data}

    def extract_trend(self, text):
        keywords = self.keywords(text)
        return keywords[0] if keywords else "Unknown trend"

    def summarize(self, text):
        return self.txtai_client.summarize(text)
