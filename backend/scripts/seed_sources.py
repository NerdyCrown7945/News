from app.database import SessionLocal
from app.models import Source

SOURCES = [
    {"name": "OpenAI Blog", "feed_url": "https://openai.com/news/rss.xml", "topic": "ai"},
    {"name": "Google AI Blog", "feed_url": "https://blog.google/technology/ai/rss/", "topic": "ai"},
    {"name": "MIT News AI", "feed_url": "https://news.mit.edu/rss/topic/artificial-intelligence2", "topic": "ai"},
    {"name": "DeepMind Blog", "feed_url": "https://deepmind.google/blog/rss.xml", "topic": "ai"},
    {"name": "The Gradient", "feed_url": "https://thegradient.pub/rss/", "topic": "ai"},
    {"name": "Ars Technica", "feed_url": "https://feeds.arstechnica.com/arstechnica/index", "topic": "scitech"},
    {"name": "ScienceDaily", "feed_url": "https://www.sciencedaily.com/rss/all.xml", "topic": "scitech"},
    {"name": "Nature News", "feed_url": "https://www.nature.com/nature.rss", "topic": "scitech"},
    {"name": "NASA Breaking News", "feed_url": "https://www.nasa.gov/rss/dyn/breaking_news.rss", "topic": "scitech"},
    {"name": "The Verge Science", "feed_url": "https://www.theverge.com/rss/science/index.xml", "topic": "scitech"},
]


def seed():
    db = SessionLocal()
    try:
        for src in SOURCES:
            exists = db.query(Source).filter(Source.feed_url == src["feed_url"]).first()
            if not exists:
                db.add(Source(**src, enabled=True))
        db.commit()
        print("Seeded sources.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
