"""
Atlas Personal OS - Social Media Calendar (CON-003)

Event-sourced social media content planning:
- Schedule posts across platforms
- Track content status and engagement
- Manage content series and campaigns
- Link to ideas from idea bank
"""

from __future__ import annotations
from datetime import datetime, date, time
from typing import Optional, List
from enum import Enum

from modules.core.database import Database, get_database
from modules.core.event_store import EventStore, get_event_store


# Event Types
POST_PLANNED = "POST_PLANNED"
POST_UPDATED = "POST_UPDATED"
POST_SCHEDULED = "POST_SCHEDULED"
POST_PUBLISHED = "POST_PUBLISHED"
POST_ENGAGEMENT_LOGGED = "POST_ENGAGEMENT_LOGGED"
SERIES_CREATED = "SERIES_CREATED"
POST_ADDED_TO_SERIES = "POST_ADDED_TO_SERIES"
POST_ARCHIVED = "POST_ARCHIVED"


class Platform(Enum):
    """Social media platforms."""
    TWITTER = "twitter"
    LINKEDIN = "linkedin"
    INSTAGRAM = "instagram"
    FACEBOOK = "facebook"
    THREADS = "threads"
    BLUESKY = "bluesky"
    MASTODON = "mastodon"
    TIKTOK = "tiktok"
    YOUTUBE = "youtube"  # For community posts
    OTHER = "other"


class PostStatus(Enum):
    """Post statuses."""
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class PostType(Enum):
    """Types of social media posts."""
    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    CAROUSEL = "carousel"
    THREAD = "thread"
    STORY = "story"
    REEL = "reel"
    POLL = "poll"
    LINK = "link"


class SocialCalendar:
    """
    Event-sourced social media content calendar.

    Plans and tracks social media posts across
    multiple platforms with engagement tracking.
    """

    ENTITY_TYPE = "social_post"
    SERIES_ENTITY = "content_series"

    def __init__(
        self,
        db: Optional[Database] = None,
        event_store: Optional[EventStore] = None
    ):
        self.db = db or get_database()
        self.event_store = event_store or get_event_store()
        self._next_id = self._compute_next_id()

    def _compute_next_id(self) -> int:
        """Compute next post ID from events."""
        events = self.event_store.query(
            entity_type=self.ENTITY_TYPE,
            event_type=POST_PLANNED
        )
        if not events:
            return 1
        return max(int(e["entity_id"]) for e in events) + 1

    # ========================================================================
    # POST COMMANDS
    # ========================================================================

    def plan_post(
        self,
        content: str,
        platform: Platform,
        post_type: PostType = PostType.TEXT,
        title: str = "",
        hashtags: Optional[List[str]] = None,
        media_urls: Optional[List[str]] = None,
        link_url: str = "",
        idea_id: Optional[int] = None,
    ) -> int:
        """
        Plan a new social media post.

        Args:
            content: Post content/text
            platform: Target platform
            post_type: Type of post
            title: Optional title
            hashtags: List of hashtags
            media_urls: URLs to media files
            link_url: Link to include
            idea_id: Link to idea bank

        Returns:
            Post ID
        """
        post_id = self._next_id
        self._next_id += 1

        self.event_store.emit(
            event_type=POST_PLANNED,
            entity_type=self.ENTITY_TYPE,
            entity_id=post_id,
            payload={
                "content": content,
                "platform": platform.value,
                "post_type": post_type.value,
                "title": title,
                "hashtags": hashtags or [],
                "media_urls": media_urls or [],
                "link_url": link_url,
                "idea_id": idea_id,
                "status": PostStatus.DRAFT.value,
            }
        )
        return post_id

    def update(
        self,
        post_id: int,
        content: Optional[str] = None,
        title: Optional[str] = None,
        hashtags: Optional[List[str]] = None,
        media_urls: Optional[List[str]] = None,
        link_url: Optional[str] = None,
    ) -> bool:
        """Update post content."""
        post = self.get(post_id)
        if not post:
            return False

        payload = {}
        if content is not None:
            payload["content"] = content
        if title is not None:
            payload["title"] = title
        if hashtags is not None:
            payload["hashtags"] = hashtags
        if media_urls is not None:
            payload["media_urls"] = media_urls
        if link_url is not None:
            payload["link_url"] = link_url

        if payload:
            self.event_store.emit(
                event_type=POST_UPDATED,
                entity_type=self.ENTITY_TYPE,
                entity_id=post_id,
                payload=payload
            )
        return True

    def schedule(
        self,
        post_id: int,
        scheduled_date: date,
        scheduled_time: Optional[time] = None,
    ) -> bool:
        """Schedule a post for publication."""
        post = self.get(post_id)
        if not post:
            return False

        self.event_store.emit(
            event_type=POST_SCHEDULED,
            entity_type=self.ENTITY_TYPE,
            entity_id=post_id,
            payload={
                "scheduled_date": scheduled_date.isoformat(),
                "scheduled_time": scheduled_time.isoformat() if scheduled_time else None,
                "status": PostStatus.SCHEDULED.value,
            }
        )
        return True

    def publish(
        self,
        post_id: int,
        published_url: str = "",
        published_at: Optional[datetime] = None,
    ) -> bool:
        """Mark post as published."""
        post = self.get(post_id)
        if not post:
            return False

        self.event_store.emit(
            event_type=POST_PUBLISHED,
            entity_type=self.ENTITY_TYPE,
            entity_id=post_id,
            payload={
                "published_url": published_url,
                "published_at": (published_at or datetime.now()).isoformat(),
                "status": PostStatus.PUBLISHED.value,
            }
        )
        return True

    def log_engagement(
        self,
        post_id: int,
        likes: int = 0,
        comments: int = 0,
        shares: int = 0,
        views: int = 0,
        clicks: int = 0,
    ) -> bool:
        """Log engagement metrics for a published post."""
        post = self.get(post_id)
        if not post:
            return False

        self.event_store.emit(
            event_type=POST_ENGAGEMENT_LOGGED,
            entity_type=self.ENTITY_TYPE,
            entity_id=post_id,
            payload={
                "likes": likes,
                "comments": comments,
                "shares": shares,
                "views": views,
                "clicks": clicks,
                "logged_at": datetime.now().isoformat(),
            }
        )
        return True

    def archive(self, post_id: int) -> bool:
        """Archive a post."""
        post = self.get(post_id)
        if not post:
            return False

        self.event_store.emit(
            event_type=POST_ARCHIVED,
            entity_type=self.ENTITY_TYPE,
            entity_id=post_id,
            payload={"status": PostStatus.ARCHIVED.value}
        )
        return True

    # ========================================================================
    # CONTENT SERIES
    # ========================================================================

    def create_series(
        self,
        name: str,
        description: str = "",
        hashtags: Optional[List[str]] = None,
    ) -> int:
        """Create a content series for related posts."""
        s_events = self.event_store.query(
            entity_type=self.SERIES_ENTITY,
            event_type=SERIES_CREATED
        )
        s_id = max((int(e["entity_id"]) for e in s_events), default=0) + 1

        self.event_store.emit(
            event_type=SERIES_CREATED,
            entity_type=self.SERIES_ENTITY,
            entity_id=s_id,
            payload={
                "name": name,
                "description": description,
                "hashtags": hashtags or [],
            }
        )
        return s_id

    def add_to_series(self, post_id: int, series_id: int) -> bool:
        """Add a post to a content series."""
        post = self.get(post_id)
        if not post:
            return False

        self.event_store.emit(
            event_type=POST_ADDED_TO_SERIES,
            entity_type=self.ENTITY_TYPE,
            entity_id=post_id,
            payload={"series_id": series_id}
        )
        return True

    def get_series(self, series_id: int) -> Optional[dict]:
        """Get series details."""
        events = self.event_store.explain(self.SERIES_ENTITY, series_id)
        if not events:
            return None

        state = {
            "id": series_id,
            "name": "",
            "description": "",
            "hashtags": [],
        }

        for event in events:
            payload = event["payload"]
            if event["event_type"] == SERIES_CREATED:
                state["name"] = payload.get("name", "")
                state["description"] = payload.get("description", "")
                state["hashtags"] = payload.get("hashtags", [])

        return state

    def get_series_posts(self, series_id: int) -> List[dict]:
        """Get all posts in a series."""
        posts = self.list_posts(limit=1000)
        return [p for p in posts if p.get("series_id") == series_id]

    # ========================================================================
    # PROJECTIONS
    # ========================================================================

    def get(self, post_id: int) -> Optional[dict]:
        """Get post state by projecting from events."""
        events = self.event_store.explain(self.ENTITY_TYPE, post_id)
        if not events:
            return None

        return self._project(post_id, events)

    def _project(self, post_id: int, events: list[dict]) -> dict:
        """Project state from events."""
        state = {
            "id": post_id,
            "content": "",
            "platform": "",
            "post_type": "text",
            "title": "",
            "hashtags": [],
            "media_urls": [],
            "link_url": "",
            "idea_id": None,
            "series_id": None,
            "status": "draft",
            "scheduled_date": None,
            "scheduled_time": None,
            "published_url": "",
            "published_at": None,
            "created_at": None,
            "engagement": None,
        }

        for event in events:
            payload = event["payload"]
            timestamp = event["timestamp"]

            if event["event_type"] == POST_PLANNED:
                state.update({
                    "content": payload.get("content", ""),
                    "platform": payload.get("platform", ""),
                    "post_type": payload.get("post_type", "text"),
                    "title": payload.get("title", ""),
                    "hashtags": payload.get("hashtags", []),
                    "media_urls": payload.get("media_urls", []),
                    "link_url": payload.get("link_url", ""),
                    "idea_id": payload.get("idea_id"),
                    "status": payload.get("status", "draft"),
                    "created_at": timestamp,
                })

            elif event["event_type"] == POST_UPDATED:
                for key in ["content", "title", "hashtags", "media_urls", "link_url"]:
                    if key in payload:
                        state[key] = payload[key]

            elif event["event_type"] == POST_SCHEDULED:
                state["scheduled_date"] = payload.get("scheduled_date")
                state["scheduled_time"] = payload.get("scheduled_time")
                state["status"] = payload.get("status", "scheduled")

            elif event["event_type"] == POST_PUBLISHED:
                state["published_url"] = payload.get("published_url", "")
                state["published_at"] = payload.get("published_at")
                state["status"] = payload.get("status", "published")

            elif event["event_type"] == POST_ENGAGEMENT_LOGGED:
                state["engagement"] = {
                    "likes": payload.get("likes", 0),
                    "comments": payload.get("comments", 0),
                    "shares": payload.get("shares", 0),
                    "views": payload.get("views", 0),
                    "clicks": payload.get("clicks", 0),
                    "logged_at": payload.get("logged_at"),
                }

            elif event["event_type"] == POST_ADDED_TO_SERIES:
                state["series_id"] = payload.get("series_id")

            elif event["event_type"] == POST_ARCHIVED:
                state["status"] = "archived"

        return state

    def list_posts(
        self,
        platform: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
    ) -> List[dict]:
        """List posts with optional filters."""
        created_events = self.event_store.query(
            entity_type=self.ENTITY_TYPE,
            event_type=POST_PLANNED,
            limit=1000
        )

        posts = []
        for event in created_events:
            post_id = int(event["entity_id"])
            post = self.get(post_id)
            if post:
                if platform and post["platform"] != platform:
                    continue
                if status and post["status"] != status:
                    continue
                posts.append(post)

        return posts[:limit]

    def get_scheduled(self, days: int = 7) -> List[dict]:
        """Get posts scheduled for the next N days."""
        from datetime import timedelta
        today = date.today()
        end_date = today + timedelta(days=days)

        posts = self.list_posts(status="scheduled", limit=1000)
        upcoming = []
        for post in posts:
            if post["scheduled_date"]:
                sched_date = date.fromisoformat(post["scheduled_date"])
                if today <= sched_date <= end_date:
                    upcoming.append(post)

        return sorted(upcoming, key=lambda x: x["scheduled_date"])

    def get_today(self) -> List[dict]:
        """Get posts scheduled for today."""
        today = date.today().isoformat()
        posts = self.list_posts(status="scheduled", limit=1000)
        return [p for p in posts if p["scheduled_date"] == today]

    def get_by_platform(self, platform: Platform) -> List[dict]:
        """Get all posts for a platform."""
        return self.list_posts(platform=platform.value, limit=1000)

    def get_stats(self) -> dict:
        """Get social media statistics."""
        posts = self.list_posts(limit=1000)

        by_platform = {}
        by_status = {}
        total_engagement = {"likes": 0, "comments": 0, "shares": 0, "views": 0}

        for post in posts:
            plat = post["platform"]
            stat = post["status"]
            by_platform[plat] = by_platform.get(plat, 0) + 1
            by_status[stat] = by_status.get(stat, 0) + 1

            if post["engagement"]:
                total_engagement["likes"] += post["engagement"].get("likes", 0)
                total_engagement["comments"] += post["engagement"].get("comments", 0)
                total_engagement["shares"] += post["engagement"].get("shares", 0)
                total_engagement["views"] += post["engagement"].get("views", 0)

        return {
            "total_posts": len(posts),
            "by_platform": by_platform,
            "by_status": by_status,
            "total_engagement": total_engagement,
        }

    def explain(self, post_id: int) -> List[dict]:
        """Get event history for a post."""
        return self.event_store.explain(self.ENTITY_TYPE, post_id)
