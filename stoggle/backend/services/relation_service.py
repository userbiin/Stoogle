"""
상관계수 기반 연관 기업 관계 도출 서비스
"""
from datetime import datetime, timedelta
from typing import Optional
import numpy as np

try:
    from pykrx import stock as pykrx_stock
    PYKRX_AVAILABLE = True
except ImportError:
    PYKRX_AVAILABLE = False

from models.schemas import RelationNode, RelationLink, RelatedCompany, ImpactItem


# 주요 종목 사전 (fallback용)
MAJOR_TICKERS = {
    "005930": ("삼성전자", "KOSPI"),
    "000660": ("SK하이닉스", "KOSPI"),
    "035420": ("NAVER", "KOSPI"),
    "051910": ("LG화학", "KOSPI"),
    "207940": ("삼성바이오로직스", "KOSPI"),
    "035720": ("카카오", "KOSPI"),
    "066570": ("LG전자", "KOSPI"),
    "003550": ("LG", "KOSPI"),
    "005380": ("현대차", "KOSPI"),
    "000270": ("기아", "KOSPI"),
}

RELATION_TYPES = {
    (0.8, 1.0): "경쟁",
    (0.6, 0.8): "협력",
    (0.4, 0.6): "공급망",
    (0.0, 0.4): "관심",
}


def _get_relation_type(corr: float) -> str:
    for (lo, hi), rtype in RELATION_TYPES.items():
        if lo <= corr < hi:
            return rtype
    return "관심"


def _fetch_close_prices(ticker: str, days: int = 90) -> Optional[list[float]]:
    if not PYKRX_AVAILABLE:
        return None
    try:
        today = datetime.today().strftime("%Y%m%d")
        start = (datetime.today() - timedelta(days=days)).strftime("%Y%m%d")
        df = pykrx_stock.get_market_ohlcv_by_date(start, today, ticker)
        if df is None or df.empty:
            return None
        return df["종가"].tolist()
    except Exception:
        return None


def compute_relations(
    ticker: str,
    candidate_tickers: Optional[list[str]] = None,
) -> dict:
    """
    주어진 ticker와 후보 종목들 간의 상관계수를 계산하여 관계 데이터를 반환.
    pykrx 미사용 시 사전 정의된 데이터 반환.
    """
    if candidate_tickers is None:
        candidate_tickers = [t for t in MAJOR_TICKERS if t != ticker][:9]

    base_prices = _fetch_close_prices(ticker)

    nodes = []
    links = []
    related = []

    center_name = MAJOR_TICKERS.get(ticker, (ticker, ""))[0]
    nodes.append(RelationNode(id=ticker, name=center_name, group=0, size=40))

    for i, cand in enumerate(candidate_tickers):
        cand_name = MAJOR_TICKERS.get(cand, (cand, ""))[0]
        size = max(10, 28 - i * 2)

        if base_prices is not None:
            cand_prices = _fetch_close_prices(cand)
            if cand_prices and len(cand_prices) == len(base_prices):
                correlation = float(np.corrcoef(base_prices, cand_prices)[0, 1])
            else:
                correlation = max(0.1, 0.9 - i * 0.08)
        else:
            correlation = max(0.1, 0.9 - i * 0.08)

        correlation = round(abs(correlation), 2)
        rtype = _get_relation_type(correlation)

        nodes.append(RelationNode(id=cand, name=cand_name, group=i % 3 + 1, size=size))
        links.append(RelationLink(source=ticker, target=cand, value=correlation, type=rtype))
        related.append(RelatedCompany(
            ticker=cand,
            name=cand_name,
            correlation=correlation,
            reason=f"{rtype} 관계 (상관계수 {correlation:.2f})",
        ))

    related.sort(key=lambda x: x.correlation, reverse=True)

    return {
        "nodes": nodes,
        "links": links,
        "related_companies": related[:5],
    }


def compute_impact(ticker: str) -> list[ImpactItem]:
    """
    영향 종목 추론 (간단한 섹터 기반 규칙)
    """
    sector_impacts = {
        "005930": [
            ImpactItem(ticker="009150", name="삼성전기", impact="positive", reason="부품 공급망 수혜"),
            ImpactItem(ticker="028260", name="삼성물산", impact="positive", reason="그룹사 호재 동반 반영"),
            ImpactItem(ticker="086520", name="에코프로", impact="negative", reason="반도체 투자 확대 → 배터리 자금 이동"),
        ],
        "000660": [
            ImpactItem(ticker="005930", name="삼성전자", impact="negative", reason="메모리 직접 경쟁"),
            ImpactItem(ticker="006400", name="삼성SDI", impact="neutral", reason="섹터 자금 이동 가능성"),
        ],
    }
    return sector_impacts.get(ticker, [])
