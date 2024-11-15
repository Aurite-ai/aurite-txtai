-- Enum types for categories and platforms
CREATE TYPE domain AS ENUM ('General', 'Cooking', 'Gaming', 'Finance', 'Sports', 'Technology');
CREATE TYPE platform AS ENUM ('Twitter', 'YouTube', 'Reddit', 'Instagram', 'TikTok', 'Other');

-- Base table for all content
CREATE TABLE content (
    id SERIAL PRIMARY KEY,
    domain domain NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Table for social media posts
CREATE TABLE social_posts (
    content_id INTEGER PRIMARY KEY REFERENCES content(id),
    platform platform NOT NULL,
    post_id VARCHAR(255) NOT NULL,
    author VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    posted_at TIMESTAMP NOT NULL,
    likes INTEGER,
    shares INTEGER,
    comments INTEGER,
    views INTEGER
);

-- Table for external media
CREATE TABLE external_media (
    content_id INTEGER PRIMARY KEY REFERENCES content(id),
    source VARCHAR(255) NOT NULL,
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    published_at TIMESTAMP NOT NULL,
    url VARCHAR(512) NOT NULL
);

-- Table for trends
CREATE TABLE trends (
    id SERIAL PRIMARY KEY,
    content_id INTEGER REFERENCES content(id),
    trend_name VARCHAR(255) NOT NULL,
    summary TEXT NOT NULL,
    sentiment FLOAT,
    relevance_score FLOAT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Table for statistics
CREATE TABLE statistics (
    id SERIAL PRIMARY KEY,
    trend_id INTEGER REFERENCES trends(id),
    stat_name VARCHAR(255) NOT NULL,
    stat_value FLOAT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Table for ideas (AI-generated insights)
CREATE TABLE ideas (
    id SERIAL PRIMARY KEY,
    trend_id INTEGER REFERENCES trends(id),
    idea_text TEXT NOT NULL,
    confidence_score FLOAT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Table for keywords
CREATE TABLE keywords (
    id SERIAL PRIMARY KEY,
    content_id INTEGER REFERENCES content(id),
    keyword VARCHAR(255) NOT NULL
);

-- Create indexes for frequently accessed columns
CREATE INDEX idx_content_domain ON content(domain);
CREATE INDEX idx_social_posts_platform ON social_posts(platform);
CREATE INDEX idx_trends_trend_name ON trends(trend_name);
CREATE INDEX idx_keywords_keyword ON keywords(keyword);
