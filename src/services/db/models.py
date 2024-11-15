from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Float, Text, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .client import DatabaseClient
import enum

Base = DatabaseClient().Base

class Platform(enum.Enum):
    TWITTER = "Twitter"
    YOUTUBE = "YouTube"
    REDDIT = "Reddit"
    INSTAGRAM = "Instagram"
    TIKTOK = "TikTok"
    OTHER = "Other"

class Domain(enum.Enum):
    GENERAL = "General"
    COOKING = "Cooking"
    GAMING = "Gaming"
    FINANCE = "Finance"
    SPORTS = "Sports"
    TECHNOLOGY = "Technology"

class Content(Base):
    __tablename__ = "content"
    
    id = Column(Integer, primary_key=True, index=True)
    domain = Column(Enum(Domain), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    social_posts = relationship("SocialPost", back_populates="content")
    external_media = relationship("ExternalMedia", back_populates="content")
    trends = relationship("Trend", back_populates="content")

class SocialPost(Base):
    __tablename__ = "social_posts"
    
    id = Column(Integer, primary_key=True, index=True)
    content_id = Column(Integer, ForeignKey("content.id"))
    platform = Column(String)
    post_id = Column(String)
    author = Column(String)
    url = Column(String)
    
    content = relationship("Content", back_populates="social_posts")

class ExternalMedia(Base):
    __tablename__ = "external_media"
    
    content_id = Column(Integer, ForeignKey("content.id"), primary_key=True)
    source = Column(String(255), nullable=False)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    published_at = Column(DateTime, nullable=False)
    url = Column(String(512), nullable=False)
    
    content_ref = relationship("Content", back_populates="external_media")

class Trend(Base):
    __tablename__ = "trends"
    
    id = Column(Integer, primary_key=True, index=True)
    content_id = Column(Integer, ForeignKey("content.id"))
    trend = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    content = relationship("Content", back_populates="trends")