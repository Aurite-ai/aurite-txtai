import matplotlib.pyplot as plt
import numpy as np
from utils.logging_config import processor_logger


class DataVisualizer:
    @staticmethod
    def _get_sentiment_data(data):
        reddit_sentiment = [
            item["sentiment"]["score"] for item in data if item["source"] == "reddit"
        ]
        news_sentiment = [
            item["sentiment"]["score"] for item in data if item["source"] == "news_api"
        ]
        return reddit_sentiment, news_sentiment

    @staticmethod
    def create_sentiment_histogram(data, output_file):
        try:
            reddit_sentiment, news_sentiment = DataVisualizer._get_sentiment_data(data)

            plt.figure(figsize=(10, 6))
            bins = np.linspace(-1, 1, 21)  # 20 bins from -1 to 1

            if reddit_sentiment:
                plt.hist(reddit_sentiment, bins=bins, alpha=0.5, label="Reddit")
            if news_sentiment:
                plt.hist(news_sentiment, bins=bins, alpha=0.5, label="News API")

            plt.xlabel("Sentiment Score")
            plt.ylabel("Frequency")
            plt.title("Sentiment Distribution: Reddit vs News API")
            plt.legend(loc="upper right")
            plt.savefig(output_file)
            plt.close()

            processor_logger.info(
                f"Sentiment histogram created and saved as {output_file}"
            )
        except Exception as e:
            processor_logger.error(f"Error creating sentiment histogram: {str(e)}")

    @staticmethod
    def create_source_pie_chart(data, output_file):
        try:
            source_counts = {"Reddit": 0, "News API": 0}
            for item in data:
                if item["source"] == "reddit":
                    source_counts["Reddit"] += 1
                elif item["source"] == "news_api":
                    source_counts["News API"] += 1

            if sum(source_counts.values()) == 0:
                processor_logger.warning(
                    "No data available for source distribution pie chart"
                )
                return

            plt.figure(figsize=(8, 8))
            plt.pie(
                source_counts.values(), labels=source_counts.keys(), autopct="%1.1f%%"
            )
            plt.title("Data Source Distribution")
            plt.savefig(output_file)
            plt.close()

            processor_logger.info(
                f"Source distribution pie chart created and saved as {output_file}"
            )
        except Exception as e:
            processor_logger.error(f"Error creating source pie chart: {str(e)}")

    @staticmethod
    def create_sentiment_boxplot(data, output_file):
        try:
            reddit_sentiment, news_sentiment = DataVisualizer._get_sentiment_data(data)

            plt.figure(figsize=(10, 6))
            box_data = [reddit_sentiment, news_sentiment]

            # Filter out empty lists
            box_data = [d for d in box_data if d]
            labels = ["Reddit", "News API"][: len(box_data)]

            if not box_data:
                processor_logger.warning("No data available for sentiment boxplot")
                return

            plt.boxplot(box_data, labels=labels)
            plt.ylabel("Sentiment Score")
            plt.title("Sentiment Distribution: Reddit vs News API")
            plt.savefig(output_file)
            plt.close()

            processor_logger.info(
                f"Sentiment boxplot created and saved as {output_file}"
            )
        except Exception as e:
            processor_logger.error(f"Error creating sentiment boxplot: {str(e)}")

    @staticmethod
    def create_all_visualizations(data):
        DataVisualizer.create_sentiment_histogram(
            data, "output/sentiment_histogram.png"
        )
        DataVisualizer.create_source_pie_chart(data, "output/source_pie_chart.png")
        DataVisualizer.create_sentiment_boxplot(data, "output/sentiment_boxplot.png")
