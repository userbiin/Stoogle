"""
뉴스 크롤링 + 랭킹 서비스 (네이버 금융 뉴스 기반)
"""
import asyncio
import re
from datetime import datetime
from typing import Optional
import httpx
from bs4 import BeautifulSoup

from models.schemas import NewsItem


NAVER_NEWS_URL = "https://finance.naver.com/item/news_news.naver"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0 Safari/537.36"
    ),
    "Referer": "https://finance.naver.com",
}


async def fetch_news(ticker: str, page: int = 1) -> list[NewsItem]:
    """
    네이버 금융에서 종목 뉴스 크롤링
    """
    params = {"code": ticker, "page": page}
    try:
        async with httpx.AsyncClient(headers=HEADERS, timeout=10) as client:
            res = await client.get(NAVER_NEWS_URL, params=params)
            res.raise_for_status()
    except Exception:
        return []

    soup = BeautifulSoup(res.text, "html.parser")
    rows = soup.select("table.type5 tr")

    items = []
    for i, row in enumerate(rows):
        a_tag = row.select_one("td.title a")
        info_td = row.select_one("td.info")
        date_td = row.select_one("td.date")

        if not a_tag:
            continue

        title = a_tag.get_text(strip=True)
        href = a_tag.get("href", "")
        url = f"https://finance.naver.com{href}" if href.startswith("/") else href
        source = info_td.get_text(strip=True) if info_td else ""
        date_str = date_td.get_text(strip=True) if date_td else ""

        items.append(NewsItem(
            id=i + 1,
            title=title,
            source=source,
            published_at=_parse_date(date_str),
            url=url,
            sentiment="neutral",
            summary=None,
            category=_categorize(title),
        ))

    return items[:20]


def _parse_date(raw: str) -> str:
    """
    네이버 날짜 문자열 → ISO 형식
    """
    raw = raw.strip()
    for fmt in ("%Y.%m.%d %H:%M", "%Y.%m.%d"):
        try:
            dt = datetime.strptime(raw, fmt)
            return dt.isoformat()
        except ValueError:
            continue
    return datetime.now().isoformat()


def _categorize(title: str) -> str:
    mapping = {
        "실적": ["실적", "영업이익", "매출", "분기", "흑자", "적자", "어닝"],
        "기술": ["기술", "개발", "특허", "AI", "반도체", "공정", "수율"],
        "분석": ["목표주가", "리포트", "전망", "분석", "투자의견"],
        "이슈": ["규제", "제재", "소송", "사고", "리콜", "논란"],
    }
    for category, keywords in mapping.items():
        if any(kw in title for kw in keywords):
            return category
    return "일반"


def rank_news(items: list[NewsItem]) -> list[NewsItem]:
    """
    감성 분석 후 중요도 순 정렬 (간단 규칙 기반)
    """
    positive_words = ["상승", "급등", "호실적", "흑자", "확정", "수혜", "개선", "달성", "돌파"]
    negative_words = ["하락", "급락", "부진", "적자", "우려", "리스크", "제재", "소송", "하향"]

    def score(item: NewsItem) -> int:
        s = 0
        for w in positive_words:
            if w in item.title:
                s += 1
        for w in negative_words:
            if w in item.title:
                s -= 1
        return s

    for item in items:
        s = score(item)
        if s > 0:
            item.sentiment = "positive"
        elif s < 0:
            item.sentiment = "negative"
        else:
            item.sentiment = "neutral"

    return sorted(items, key=lambda x: abs(score(x)), reverse=True)
