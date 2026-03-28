"""
LangChain 기반 뉴스 에이전트
뉴스 크롤링 → 요약 → 감성 분석을 자동화하는 에이전트
"""
import os
from typing import Optional

try:
    from langchain_openai import ChatOpenAI
    from langchain.agents import AgentExecutor, create_openai_functions_agent
    from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
    from langchain.tools import tool
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False

from services.news_service import fetch_news, rank_news
import asyncio


@tool
def fetch_stock_news(ticker: str) -> str:
    """주식 종목 코드를 받아 최신 뉴스를 가져옵니다."""
    items = asyncio.run(fetch_news(ticker))
    ranked = rank_news(items)
    return "\n".join(
        f"[{i.sentiment}] {i.title} ({i.source})"
        for i in ranked[:5]
    )


@tool
def analyze_sentiment(text: str) -> str:
    """뉴스 텍스트의 투자 관점 감성을 분석합니다."""
    positive_words = ["상승", "급등", "호실적", "흑자", "확정", "수혜"]
    negative_words = ["하락", "급락", "부진", "적자", "우려", "제재"]

    pos = sum(1 for w in positive_words if w in text)
    neg = sum(1 for w in negative_words if w in text)

    if pos > neg:
        return f"긍정적 ({pos}개 긍정 키워드)"
    elif neg > pos:
        return f"부정적 ({neg}개 부정 키워드)"
    return "중립적"


def build_news_agent() -> Optional[object]:
    """
    LangChain 뉴스 에이전트 생성.
    OPENAI_API_KEY 미설정 시 None 반환.
    """
    if not LANGCHAIN_AVAILABLE or not os.getenv("OPENAI_API_KEY"):
        return None

    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0,
        api_key=os.getenv("OPENAI_API_KEY"),
    )

    tools = [fetch_stock_news, analyze_sentiment]

    prompt = ChatPromptTemplate.from_messages([
        ("system", (
            "당신은 한국 주식 시장 전문 애널리스트입니다. "
            "주어진 종목의 최신 뉴스를 분석하고 투자자에게 유용한 인사이트를 제공합니다. "
            "항상 한국어로 응답하고, 투자 권유는 하지 않습니다."
        )),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])

    agent = create_openai_functions_agent(llm, tools, prompt)
    return AgentExecutor(agent=agent, tools=tools, verbose=True, max_iterations=3)


async def run_news_analysis(ticker: str, company_name: str) -> Optional[str]:
    """
    에이전트를 실행하여 종목 뉴스 분석 결과 반환
    """
    agent = build_news_agent()
    if agent is None:
        return None

    try:
        result = await agent.ainvoke({
            "input": f"{company_name}({ticker}) 종목의 최신 뉴스를 분석하고 투자자 관점의 핵심 인사이트 2~3문장을 작성해주세요."
        })
        return result.get("output")
    except Exception:
        return None
