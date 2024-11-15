import logging
from logging.handlers import RotatingFileHandler
import os

def setup_logger(name, log_file, level=logging.INFO):
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    
    handler = RotatingFileHandler(log_file, maxBytes=10000000, backupCount=5)
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)

    return logger

# Create logs directory if it doesn't exist
if not os.path.exists('logs'):
    os.makedirs('logs')

# Setup loggers
main_logger = setup_logger('main', 'logs/main.log')
scraper_logger = setup_logger('scraper', 'logs/scraper.log')
api_logger = setup_logger('api', 'logs/api.log')
processor_logger = setup_logger('processor', 'logs/processor.log')
