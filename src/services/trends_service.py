from typing import Any, Dict, List

from src.services.db.client import DBClient


def get_trends(limit: int = 10) -> Dict[str, Any]:
    with DBClient() as db:
        trends = db.fetch_all(
            """
            SELECT t.trend_name, t.summary, t.sentiment, c.domain,
                   sp.platform AS social_platform, em.source AS external_source
            FROM trends t
            JOIN content c ON t.content_id = c.id
            LEFT JOIN social_posts sp ON c.id = sp.content_id
            LEFT JOIN external_media em ON c.id = em.content_id
            ORDER BY c.created_at DESC
            LIMIT %s
        """,
            (limit,),
        )

    return {
        "summary": "Here are the latest trends from various social media and external sources.",
        "trends": [
            {
                "title": trend["trend_name"],
                "description": trend["summary"],
                "sentiment": trend["sentiment"],
                "domain": trend["domain"],
                "source": (
                    trend["social_platform"]
                    if trend["social_platform"]
                    else trend["external_source"]
                ),
            }
            for trend in trends
        ],
    }


def get_domain_trends(domain: str, limit: int = 10) -> Dict[str, Any]:
    with DBClient() as db:
        trends = db.fetch_all(
            """
            SELECT t.trend_name, t.summary, t.sentiment,
                   sp.platform AS social_platform, em.source AS external_source
            FROM trends t
            JOIN content c ON t.content_id = c.id
            LEFT JOIN social_posts sp ON c.id = sp.content_id
            LEFT JOIN external_media em ON c.id = em.content_id
            WHERE c.domain = %s
            ORDER BY c.created_at DESC
            LIMIT %s
        """,
            (domain, limit),
        )

    return {
        "summary": f"Here are the latest {domain.lower()} trends from various social media and external sources.",
        "trends": [
            {
                "title": trend["trend_name"],
                "description": trend["summary"],
                "sentiment": trend["sentiment"],
                "source": (
                    trend["social_platform"]
                    if trend["social_platform"]
                    else trend["external_source"]
                ),
            }
            for trend in trends
        ],
    }


def get_sports_trends():
    return get_domain_trends("Sports")


def get_cooking_trends():
    return get_domain_trends("Cooking")


def get_gaming_trends():
    return get_domain_trends("Gaming")


def get_finance_trends():
    return get_domain_trends("Finance")


def get_technology_trends():
    return get_domain_trends("Technology")


def get_ideas(limit: int = 5) -> Dict[str, Any]:
    with DBClient() as db:
        ideas = db.fetch_all(
            """
            SELECT i.idea_text, i.confidence_score, t.trend_name
            FROM ideas i
            JOIN trends t ON i.trend_id = t.id
            ORDER BY i.created_at DESC
            LIMIT %s
        """,
            (limit,),
        )

    return {
        "summary": "Here are the latest AI-generated insights based on current trends.",
        "ideas": [
            {
                "text": idea["idea_text"],
                "confidence": idea["confidence_score"],
                "related_trend": idea["trend_name"],
            }
            for idea in ideas
        ],
    }


def get_statistics(trend_name: str) -> Dict[str, Any]:
    with DBClient() as db:
        stats = db.fetch_all(
            """
            SELECT s.stat_name, s.stat_value
            FROM statistics s
            JOIN trends t ON s.trend_id = t.id
            WHERE t.trend_name = %s
            ORDER BY s.created_at DESC
        """,
            (trend_name,),
        )

    return {
        "trend": trend_name,
        "statistics": [{"name": stat["stat_name"], "value": stat["stat_value"]} for stat in stats],
    }
