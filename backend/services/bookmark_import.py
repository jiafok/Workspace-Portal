from bs4 import BeautifulSoup
from typing import List


def parse_bookmark_html(html_content: str) -> List[dict]:
    """Parse Chrome/Edge/Firefox bookmark HTML export."""
    soup = BeautifulSoup(html_content, "html.parser")
    categories = []
    current_category = None

    for dt in soup.find_all("dt"):
        h3 = dt.find("h3")
        if h3:
            name = h3.get_text(strip=True)
            current_category = {"name": name, "websites": []}
            categories.append(current_category)

        a_tag = dt.find("a")
        if a_tag:
            website = {
                "name": a_tag.get_text(strip=True),
                "url": a_tag.get("href", ""),
                "icon_url": a_tag.get("icon", ""),
            }
            if current_category:
                current_category["websites"].append(website)
            elif categories:
                categories[-1]["websites"].append(website)
            else:
                categories.append({"name": "导入收藏夹", "websites": [website]})

    return categories
