import httpx
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import hashlib
import os

ICONS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data", "icons")
os.makedirs(ICONS_DIR, exist_ok=True)


async def fetch_site_info(url: str) -> dict:
    """Fetch website title, description and favicon URL."""
    result = {"name": "", "description": "", "icon_url": ""}

    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    parsed = urlparse(url)
    base_url = f"{parsed.scheme}://{parsed.netloc}"

    try:
        async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
            response = await client.get(url, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            })
            soup = BeautifulSoup(response.text, "lxml")

            title_tag = soup.find("title")
            if title_tag:
                result["name"] = title_tag.get_text(strip=True)

            meta_desc = soup.find("meta", attrs={"name": "description"}) or \
                        soup.find("meta", {"property": "og:description"})
            if meta_desc and meta_desc.get("content"):
                result["description"] = meta_desc["content"]

            icon_url = None
            for link in soup.find_all("link"):
                rel = link.get("rel", [])
                if isinstance(rel, list):
                    rel = [r.lower() for r in rel if r]
                if "icon" in rel or "shortcut icon" in rel or "apple-touch-icon" in rel:
                    icon_url = link.get("href")
                    break

            if icon_url:
                if icon_url.startswith("//"):
                    icon_url = f"{parsed.scheme}:{icon_url}"
                elif icon_url.startswith("/"):
                    icon_url = urljoin(base_url, icon_url)
                elif not icon_url.startswith("http"):
                    icon_url = urljoin(base_url, icon_url)
            else:
                icon_url = f"{base_url}/favicon.ico"

            result["icon_url"] = icon_url

    except Exception:
        parsed = urlparse(url)
        base = f"{parsed.scheme}://{parsed.netloc}"
        result["icon_url"] = f"{base}/favicon.ico"
        if not result["name"]:
            result["name"] = parsed.netloc

    return result


async def download_icon(url: str) -> str | None:
    """Download icon and save locally, return local path."""
    if not url:
        return None
    try:
        async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
            response = await client.get(url)
            if response.status_code == 200:
                filename = hashlib.md5(url.encode()).hexdigest()[:12]
                ext = ".ico"
                content_type = response.headers.get("content-type", "")
                if "png" in content_type:
                    ext = ".png"
                elif "svg" in content_type:
                    ext = ".svg"
                elif "jpeg" in content_type or "jpg" in content_type:
                    ext = ".jpg"
                filepath = os.path.join(ICONS_DIR, filename + ext)
                with open(filepath, "wb") as f:
                    f.write(response.content)
                return f"/api/icons/{filename}{ext}"
    except Exception:
        pass
    return None
