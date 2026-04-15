"""
pykrx를 이용한 주가 데이터 수집 서비스

검색 흐름:
  1. Redis 레지스트리 조회 → O(1) 이름 매칭
  2. 레지스트리 없으면 pykrx 풀스캔 후 Redis에 저장 (초기 1회만)
  3. 가격 데이터도 Redis 캐시 우선, 없으면 pykrx 호출
"""
from datetime import datetime, timedelta
from typing import Optional
import logging

import pandas as pd

logger = logging.getLogger(__name__)

try:
    from pykrx import stock as pykrx_stock
    PYKRX_AVAILABLE = True
except ImportError:
    PYKRX_AVAILABLE = False
    logger.warning("pykrx 미설치 — 주가 기능 비활성화")

from models.schemas import PricePoint, CompanyBrief
from services.cache_service import (
    get_ticker_registry, set_ticker_registry,
    get_price_cache, set_price_cache,
    get_history_cache, set_history_cache,
)


def _today() -> str:
    return datetime.today().strftime("%Y%m%d")


def _n_days_ago(n: int) -> str:
    return (datetime.today() - timedelta(days=n)).strftime("%Y%m%d")


# ---------------------------------------------------------------------------
# 종목 레지스트리 (ticker → {ticker, name, market})
# ---------------------------------------------------------------------------

def build_ticker_registry() -> dict:
    """
    KRX 전종목 레지스트리를 pykrx로 구축한다.
    레지스트리 구조:
      {
        "005930": {"ticker": "005930", "name": "삼성전자", "market": "KOSPI"},
        ...
      }
    약 2,500~3,000 종목 처리 — 최초 1회 또는 Celery 주간 태스크로만 호출.
    """
    if not PYKRX_AVAILABLE:
        return {}

    registry: dict = {}
    today = _today()

    for market in ("KOSPI", "KOSDAQ", "KONEX"):
        try:
            tickers = pykrx_stock.get_market_ticker_list(today, market=market)
        except Exception as e:
            logger.warning(f"{market} 종목 리스트 조회 실패: {e}")
            continue

        for ticker in tickers:
            try:
                name = pykrx_stock.get_market_ticker_name(ticker)
            except Exception:
                name = ticker
            registry[ticker] = {"ticker": ticker, "name": name, "market": market}

    logger.info(f"종목 레지스트리 구축 완료: {len(registry)}종목")
    return registry


def get_or_build_registry() -> dict:
    """Redis에서 레지스트리 조회, 없으면 pykrx로 구축 후 캐싱."""
    cached = get_ticker_registry()
    if cached:
        return cached

    logger.info("레지스트리 캐시 없음 — pykrx 풀스캔 시작")
    registry = build_ticker_registry()
    if registry:
        set_ticker_registry(registry)
    return registry


# ---------------------------------------------------------------------------
# 주가 히스토리
# ---------------------------------------------------------------------------

def get_price_history(ticker: str, days: int = 90) -> list[PricePoint]:
    """
    주가 히스토리 조회. Redis 캐시 → pykrx 순으로 시도.
    """
    # 캐시 확인 (days=90 고정 키 사용, 더 짧은 요청엔 슬라이스)
    cached = get_history_cache(ticker)
    if cached is not None:
        points = [PricePoint(**p) for p in cached]
        return points[-days:] if len(points) > days else points

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

        # Redis 캐싱 (dict로 직렬화)
        set_history_cache(ticker, [p.model_dump() for p in result])
        return result

    except Exception as e:
        logger.warning(f"주가 히스토리 조회 실패 ({ticker}): {e}")
        return []


# ---------------------------------------------------------------------------
# 현재가
# ---------------------------------------------------------------------------

def get_current_price(ticker: str) -> Optional[dict]:
    """
    현재가 + 등락률 조회. Redis 캐시(60초) → pykrx 순으로 시도.
    """
    cached = get_price_cache(ticker)
    if cached is not None:
        return cached

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

        result = {
            "price": price,
            "change": round(change_pct, 2),
            "change_amount": round(change_amount, 0),
        }
        set_price_cache(ticker, result)
        return result

    except Exception as e:
        logger.warning(f"현재가 조회 실패 ({ticker}): {e}")
        return None


# ---------------------------------------------------------------------------
# 시총 · 펀더멘털
# ---------------------------------------------------------------------------

def get_market_cap_info(ticker: str) -> Optional[dict]:
    """시총, PER, PBR, EPS 조회"""
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
        market_cap = (
            float(cap_df.iloc[-1]["시가총액"])
            if cap_df is not None and not cap_df.empty
            else None
        )

        return {
            "market_cap": market_cap,
            "per": float(row.get("PER", 0)) or None,
            "pbr": float(row.get("PBR", 0)) or None,
            "eps": float(row.get("EPS", 0)) or None,
        }
    except Exception as e:
        logger.warning(f"시총 정보 조회 실패 ({ticker}): {e}")
        return None


# ---------------------------------------------------------------------------
# 종목 검색 (레지스트리 기반 O(1))
# ---------------------------------------------------------------------------

def search_companies(query: str) -> list[CompanyBrief]:
    """
    종목명 또는 종목코드로 기업 검색.

    Redis 레지스트리를 활용하여 O(N_matches) 로 검색한 뒤
    매칭 종목에 대해서만 현재가를 조회한다.
    (구 방식: 전종목 루프 × API 호출 → 수 분 소요)
    """
    query = query.strip()
    registry = get_or_build_registry()

    results: list[CompanyBrief] = []
    query_lower = query.lower()

    for ticker, meta in registry.items():
        name: str = meta.get("name", "")
        if query_lower in name.lower() or query == ticker:
            price_info = get_current_price(ticker)
            results.append(CompanyBrief(
                ticker=ticker,
                name=name,
                market=meta.get("market", ""),
                sector="",
                price=price_info.get("price") if price_info else None,
                change=price_info.get("change") if price_info else None,
            ))
            if len(results) >= 20:
                break

    # 정확 일치(종목코드 or 이름)를 최상위로 정렬
    results.sort(key=lambda r: (
        0 if r.ticker == query or r.name == query else 1
    ))
    return results


# ---------------------------------------------------------------------------
# 단일 종목 메타 조회 (ticker → CompanyBrief)
# ---------------------------------------------------------------------------

def get_company_brief(ticker: str) -> Optional[CompanyBrief]:
    """레지스트리에서 단일 종목 정보를 반환한다."""
    registry = get_or_build_registry()
    meta = registry.get(ticker.upper())
    if not meta:
        return None

    price_info = get_current_price(ticker)
    return CompanyBrief(
        ticker=ticker,
        name=meta.get("name", ticker),
        market=meta.get("market", ""),
        sector="",
        price=price_info.get("price") if price_info else None,
        change=price_info.get("change") if price_info else None,
    )
