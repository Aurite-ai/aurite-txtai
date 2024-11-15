from textblob import TextBlob
from utils.logging_config import processor_logger

class SentimentAnalyzer:
    @staticmethod
    def analyze_sentiment(text):
        try:
            blob = TextBlob(text)
            sentiment = blob.sentiment.polarity
            
            if sentiment > 0:
                sentiment_category = "positive"
            elif sentiment < 0:
                sentiment_category = "negative"
            else:
                sentiment_category = "neutral"
            
            processor_logger.info(f"Sentiment analysis completed. Score: {sentiment}, Category: {sentiment_category}")
            return {"score": sentiment, "category": sentiment_category}
        except Exception as e:
            processor_logger.error(f"Error in sentiment analysis: {str(e)}")
            return {"score": 0, "category": "error"}

if __name__ == "__main__":
    sample_text = "Python is an amazing programming language!"
    result = SentimentAnalyzer.analyze_sentiment(sample_text)
    print(f"Text: {sample_text}")
    print(f"Sentiment: {result}")
