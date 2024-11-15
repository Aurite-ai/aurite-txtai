import re

from utils.logging_config import processor_logger


class TextCleaner:
    @staticmethod
    def clean_text(text):
        try:
            # Convert to lowercase
            text = text.lower()

            # Remove special characters and digits
            text = re.sub(r"[^a-zA-Z\s]", "", text)

            # Remove extra whitespaces
            text = re.sub(r"\s+", " ", text).strip()

            processor_logger.info("Text cleaned successfully")
            return text
        except Exception as e:
            processor_logger.error(f"Error cleaning text: {str(e)}")
            return text
