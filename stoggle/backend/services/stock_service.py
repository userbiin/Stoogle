"""
pykrx를 이용한 주가 데이터 수집 서비스
"""
from datetime import datetime, timedelta
from typing import Optional
import pandas as pd

try:
    from pykrx import stock as pykrx_stock
    PYKRX_AVAILABLE = True
except ImportError:
    PYKRX_AVAILABLE = False

from models.schemas import PricePoint, CompanyBrief


def _today() -> str:
    return datetime.today().strftime("%Y%m%d")


def _n_days_ago(n: int) -> str:
    return (datetime.today() - timedelta(days=n)).strftime("%Y%m%d")


def get_price_history(ticker: str, days: int = 90) -> list[PricePoint]:
    """
    주가 히스토리 조회. pykrx를 사용하며 없을 경우 빈 리스트 반환.
    """
    if not PYKRX_AVAILABLE:
        return []

    try:
        df = pykrx_stock.get_market_ohlcv_by_date(
            fromdate=_n_days_ago(days),
            todate=_today(),
            ticker=ticker,
        )
        if df is None or df.empty:
            return []

        result = []
        for date_idx, row in df.iterrows():
            result.append(PricePoint(
                date=str(date_idx)[:10],
                close=float(row["종가"]),
                volume=int(row["거래량"]),
            ))
        return result
    except Exception:
        return []


def get_current_price(ticker: str) -> Optional[dict]:
    """
    현재가 + 등락률 조회
    """
    if not PYKRX_AVAILABLE:
        return None

    try:
        df = pykrx_stock.get_market_ohlcv_by_date(
            fromdate=_n_days_ago(5),
            todate=_today(),
            ticker=ticker,
        )
        if df is None or df.empty:
            return None

        latest = df.iloc[-1]
        prev = df.iloc[-2] if len(df) > 1 else latest

        price = float(latest["종가"])
        prev_price = float(prev["종가"])
        change_amount = price - prev_price
        change_pct = (change_amount / prev_price * 100) if prev_price else 0

        return {
            "price": price,
            "change": round(change_pct, 2),
            "change_amount": round(change_amount, 0),
        }
    except Exception:
        return None


def get_market_cap_info(ticker: str) -> Optional[dict]:
    """
    시총, PER, PBR, EPS 조회
    """
    if not PYKRX_AVAILABLE:
        return None

    try:
        df = pykrx_stock.get_market_fundamental_by_date(
            fromdate=_n_days_ago(5),
            todate=_today(),
            ticker=ticker,
        )
        if df is None or df.empty:
            return None

        row = df.iloc[-1]
        cap_df = pykrx_stock.get_market_cap_by_date(
            fromdate=_n_days_ago(5),
            todate=_today(),
            ticker=ticker,
        )
        market_cap = float(cap_df.iloc[-1]["시가총액"]) if cap_df is not None and not cap_df.empty else None

        return {
            "market_cap": market_cap,
            "per": float(row.get("PER", 0)) or None,
            "pbr": float(row.get("PBR", 0)) or None,
            "eps": float(row.get("EPS", 0)) or None,
        }
    except Exception:
        return None


def search_companies(query: str) -> list[CompanyBrief]:
    """
    종목명 또는 종목코드로 기업 검색
    """
    if not PYKRX_AVAILABLE:
        return []

    results = []
    try:
        today = _today()
        for market in ["KOSPI", "KOSDAQ"]:
            tickers = pykrx_stock.get_market_ticker_list(today, market=market)
            for t in tickers:
                name = pykrx_stock.get_market_ticker_name(t)
                if query.lower() in name.lower() or query == t:
                    price_info = get_current_price(t)
                    results.append(CompanyBrief(
                        ticker=t,
                        name=name,
                        market=market,
                        sector="",
                        price=price_info.get("price") if price_info else None,
                        change=price_info.get("change") if price_info else None,
                    ))
                    if len(results) >= 10:
                        return results
    except Exception:
        pass

    return results
