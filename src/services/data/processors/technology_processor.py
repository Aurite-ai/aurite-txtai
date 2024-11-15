from .base_processor import BaseProcessor


class TechnologyProcessor(BaseProcessor):
    def __init__(self, txtai_client):
        super().__init__(txtai_client)
        self.tech_keywords = [
            "AI",
            "machine learning",
            "blockchain",
            "cloud computing",
            "cybersecurity",
            "IoT",
            "5G",
            "robotics",
            "quantum computing",
            "VR",
            "AR",
        ]

    def process(self, data):
        text = data.get("content", data.get("text", ""))
        title = data.get("title", "")

        base_processed = super().process(data)

        tech_processed = {
            "is_tech_related": self._is_tech_related(base_processed["keywords"]),
            "tech_category": self._categorize_tech(text),
            "tech_sentiment": self._analyze_tech_sentiment(text),
            "key_tech_entities": self._extract_tech_entities(text),
            "tech_summary": self._generate_tech_summary(title, text),
            "future_impact": self._predict_future_impact(text),
        }

        processed_data = {**data, **base_processed, **tech_processed}
        return processed_data

    def _is_tech_related(self, keywords):
        return any(
            keyword.lower() in [tk.lower() for tk in self.tech_keywords]
            for keyword in keywords
        )

    def _categorize_tech(self, text):
        categories = [
            "Software",
            "Hardware",
            "AI/ML",
            "Cybersecurity",
            "Networking",
            "Other",
        ]
        return self.txtai_client.label(text, categories)

    def _analyze_tech_sentiment(self, text):
        return self.compute_sentiment(text)

    def _extract_tech_entities(self, text):
        entities = self.txtai_client.keywords(text, count=10)
        return [
            entity
            for entity in entities
            if entity.lower() in [tk.lower() for tk in self.tech_keywords]
        ]

    def _generate_tech_summary(self, title, text):
        return self.summarize(f"{title}\n\n{text}")

    def _predict_future_impact(self, text):
        impact = self.txtai_client.generate(
            f"Predict the future impact of the technology described in this text: {text}"
        )
        return impact.strip()
