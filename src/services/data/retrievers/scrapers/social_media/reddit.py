import os

import praw
from prawcore import ResponseException

from utils.logging_config import scraper_logger


class RedditScraper:
    def __init__(self):
        client_id = os.environ.get("REDDIT_CLIENT_ID")
        client_secret = os.environ.get("REDDIT_CLIENT_SECRET")
        user_agent = "python:ai.aurite.trendai:v1.0 (by /u/Intelligent_Pay4364)"

        if not client_id or not client_secret:
            scraper_logger.error(
                "Reddit API credentials not found in environment variables"
            )
            raise ValueError("Reddit API credentials not set")

        self.reddit = praw.Reddit(
            client_id=client_id, client_secret=client_secret, user_agent=user_agent
        )
        scraper_logger.info("Reddit API initialized")

    def scrape_posts(self, subreddit, limit=10):
        try:
            # Test authentication
            username = self.reddit.user.me()
            scraper_logger.info(f"Authentication successful for user: {username}")

            subreddit = self.reddit.subreddit(subreddit)
            posts = subreddit.new(limit=limit)

            scraped_posts = []
            for post in posts:
                scraped_posts.append(
                    {
                        "title": post.title,
                        "author": post.author.name if post.author else "[deleted]",
                        "score": post.score,
                        "url": post.url,
                        "created_utc": post.created_utc,
                        "id": post.id,  # Add this line
                        "selftext": post.selftext,  # Add this line for the content
                    }
                )

            scraper_logger.info(
                f"Successfully scraped {len(scraped_posts)} posts from r/{subreddit}"
            )
            return scraped_posts
        except ResponseException as e:
            scraper_logger.error(
                f"Reddit API ResponseException: {e.response.status_code} - {e.response.reason}"
            )
            return []
        except Exception as e:
            scraper_logger.error(f"Error scraping Reddit: {str(e)}")
            return []


if __name__ == "__main__":
    scraper = RedditScraper()
    posts = scraper.scrape_posts("python", 5)
    for post in posts:
        print(post)
