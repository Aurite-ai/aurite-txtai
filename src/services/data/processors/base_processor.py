class BaseProcessor:
    def __init__(self, txtai_client):
        self.txtai_client = txtai_client

    def keywords(self, text, count=5):
        return self.txtai_client.keywords(text, count)

    def summarize(self, text):
        return self.txtai_client.summarize(text)

    def process(self, data):
        text = data.get("content", data.get("text", ""))
        processed_data = {
            "category": self.txtai_client.label(
                text, ["technology", "finance", "sports", "politics", "entertainment"]
            ),
            "keywords": self.keywords(text),
            "summary": self.summarize(text),
        }
        return processed_data

    def label_text(self, text):
        categories = ["technology", "finance", "sports", "politics", "entertainment"]
        return self.txtai_client.label(text, categories)

    def compute_sentiment(self, text):
        return self.txtai_client.label(text, ["positive", "negative", "neutral"])
