from fastapi import APIRouter, HTTPException
from models.schemas import InsightResponse
from services.stock_service import get_price_history, get_current_price, get_market_cap_info
from services.news_service import fetch_news
from services.nlp_service import extract_keywords, summarize_with_llm

try:
    from pykrx import stock as pykrx_stock
    def get_company_name(ticker: str) -> str:
        try:
            return pykrx_stock.get_market_ticker_name(ticker)
        except Exception:
            return ticker
except ImportError:
    def get_company_name(ticker: str) -> str:
        return ticker

router = APIRouter(tags=["insight"])


@router.get("/insight/{ticker}", response_model=InsightResponse)
async def get_insight(ticker: str):
    ticker = ticker.upper()

    price_info = get_current_price(ticker)
    cap_info = get_market_cap_info(ticker)
    price_history = get_price_history(ticker, days=90)
    news_items = await fetch_news(ticker, page=1)

    company_name = get_company_name(ticker)
    titles = [n.title for n in news_items]

    keywords = extract_keywords(titles) if titles else []
    summary = await summarize_with_llm(ticker, company_name, titles) if titles else None

    return InsightResponse(
        ticker=ticker,
        name=company_name,
        market="KOSPI",
        sector="",
        price=price_info.get("price") if price_info else None,
        change=price_info.get("change") if price_info else None,
        change_amount=price_info.get("change_amount") if price_info else None,
        market_cap=cap_info.get("market_cap") if cap_info else None,
        per=cap_info.get("per") if cap_info else None,
        pbr=cap_info.get("pbr") if cap_info else None,
        eps=cap_info.get("eps") if cap_info else None,
        summary=summary,
        keywords=keywords,
        price_history=price_history,
    )
