import aiohttp
import feedparser
import json
from bs4 import BeautifulSoup
from readability import Document
from urllib.parse import urljoin

SOURCES = [
    "https://crypto.news/feed",
    "https://www.coindesk.com/arc/outboundfeeds/rss",
]
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; NewsParser/1.0)"}

def load_seen():
    try:
        with open("storage.json", "r", encoding="utf-8") as f:
            return set(json.load(f))
    except Exception:
        return set()

def save_seen(seen):
    with open("storage.json", "w", encoding="utf-8") as f:
        json.dump(list(seen), f, ensure_ascii=False, indent=2)

async def fetch_text_from_url(session, url: str) -> tuple[str, str | None]:
    """Возвращает (plain_text, image_url_or_none) для статьи."""
    try:
        async with session.get(url, headers=HEADERS, timeout=20) as resp:
            base = str(resp.url)
            html = await resp.text()
    except Exception:
        return "", None

    image_url = None
    # 1) попробовать OG/Twitter image
    try:
        soup = BeautifulSoup(html, "html.parser")
        for p in ("og:image", "twitter:image", "og:image:url"):
            tag = soup.find("meta", attrs={"property": p}) or soup.find("meta", attrs={"name": p})
            if tag and tag.get("content"):
                image_url = urljoin(base, tag["content"].strip())
                break
        # 2) если нет — первая картинка в <article>
        if not image_url:
            art = soup.find("article") or soup
            img = art.find("img")
            if img and img.get("src"):
                image_url = urljoin(base, img["src"])
    except Exception:
        pass

    # Текст через readability
    try:
        doc = Document(html)
        article_html = doc.summary()
        text = BeautifulSoup(article_html, "html.parser").get_text(separator="\n", strip=True)
    except Exception:
        text = ""

    return text, image_url

def _image_from_entry(entry) -> str | None:
    """Достаём картинку из RSS entry."""
    # media:content / media:thumbnail
    try:
        if hasattr(entry, "media_content") and entry.media_content:
            for mc in entry.media_content:
                url = mc.get("url")
                if url: return url
        if hasattr(entry, "media_thumbnail") and entry.media_thumbnail:
            for mt in entry.media_thumbnail:
                url = mt.get("url")
                if url: return url
    except Exception:
        pass
    # enclosures
    try:
        if hasattr(entry, "enclosures") and entry.enclosures:
            for enc in entry.enclosures:
                url = getattr(enc, "href", None) or enc.get("href")
                typ = getattr(enc, "type", None) or enc.get("type")
                if url and (not typ or typ.startswith("image/")):
                    return url
    except Exception:
        pass
    return None

async def fetch_latest_articles():
    """[{title, link, content, image_url}]"""
    new_articles = []
    seen = load_seen()

    async with aiohttp.ClientSession() as session:
        for feed_url in SOURCES:
            async with session.get(feed_url, headers=HEADERS, timeout=20) as resp:
                data = await resp.text()
                feed = feedparser.parse(data)

                for entry in feed.entries[:5]:
                    link = getattr(entry, "link", None)
                    if not link or link in seen:
                        continue
                    seen.add(link)

                    title = getattr(entry, "title", "")
                    summary = getattr(entry, "summary", "")
                    image_url = _image_from_entry(entry)

                    content = summary
                    if not content or len(BeautifulSoup(content, "html.parser").get_text(strip=True)) < 200:
                        full_text, og_img = await fetch_text_from_url(session, link)
                        if full_text:
                            content = full_text
                        if not image_url and og_img:
                            image_url = og_img

                    new_articles.append({
                        "title": title,
                        "link": link,
                        "content": content,
                        "image_url": image_url,
                    })

    save_seen(seen)
    return new_articles
