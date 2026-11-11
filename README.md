<div align="center">

# Stoogle

**주식 전용 인사이트 검색엔진**

종목을 검색하면 주가 · 뉴스 · 공시 · 기업 관계를 한 화면에 모으고,<br>
LLM이 _"이 뉴스가 어떤 종목에, 어떤 기업 관계를 타고 영향을 주는가"_ 를 분석합니다.

![Python](https://img.shields.io/badge/Python_3.12-3776AB?style=flat-square&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white)
![Celery](https://img.shields.io/badge/Celery-37814A?style=flat-square&logo=celery&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL_+_pgvector-4169E1?style=flat-square&logo=postgresql&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-DC382D?style=flat-square&logo=redis&logoColor=white)
![React](https://img.shields.io/badge/React_18-20232A?style=flat-square&logo=react&logoColor=61DAFB)
![D3.js](https://img.shields.io/badge/D3.js-F9A03C?style=flat-square&logo=d3&logoColor=white)
![Claude](https://img.shields.io/badge/Claude_API-D97757?style=flat-square&logo=anthropic&logoColor=white)
![Ollama](https://img.shields.io/badge/Ollama_·_EXAONE_3.5-000000?style=flat-square&logo=ollama&logoColor=white)

<img src="docs/images/screen-dashboard.png" width="90%" alt="Stoogle 인사이트 대시보드">

</div>

<br>

## Overview

- **기간** : 2026.03 – 2026.06 (10주) · 숭실대학교 고급캡스톤디자인
- **팀** : 2인 · [민수빈](https://github.com/userbiin) (팀장), [최다연](https://github.com/Choedayeon)
- **대상** :  KRX 전 종목 검색, KOSPI200 실시간 분석
- **구조** : 로컬 sLLM으로 뉴스를 대량 필터링하고, 통과한 기사만 Claude로 구조화 분석하는 **2단 LLM 파이프라인**

<br>

## Features

| 메인 검색 | 감성 뉴스 피드 |
|:---:|:---:|
| <img src="docs/images/screen-main.png" alt="메인 검색"> | <img src="docs/images/screen-news.png" alt="뉴스 피드"> |
| Google 스타일 검색 · 종목명/코드 입력 | LLM 관련도 랭킹 · 긍정/중립/부정 필터 |

<p align="center"><img src="docs/images/screen-relation.png" width="100%" alt="기업 관계 그래프"></p>
<p align="center"><sub>기업 관계 그래프 — 5가지 관계 유형을 D3 force graph로 표시하고, 관계마다 근거 문장 제공</sub></p>

- **AI 인사이트** — 최신 뉴스를 종합해 3~4문장 요약과 감성(긍정/중립/부정)을 제공
- **기업 관계 그래프** — DART 공시 파싱과 LLM 관계 발굴(뉴스 · 공시 근거)을 결합해 경쟁 · 계열 · 협력 · 공급망 관계를 시각화
- **영향 종목 예측** — 관계 그래프를 따라 1-hop / 2-hop으로 영향을 전파하고, 종목별 방향과 신뢰도 제시
- **예측 검증 루프** — D+3 실제 주가로 매일 자동 채점하고, 신뢰도 점수를 재보정

<br>

## Architecture

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/images/architecture-dark.png">
  <img src="docs/images/architecture-light.png" alt="System Architecture">
</picture>

- **Batch / Serving 분리** — 수집 · 분석은 Celery Beat 13개 정기 작업이 미리 수행하고, FastAPI는 캐시된 결과를 바로 반환
- **Redis 캐싱** — 데이터별 TTL 차등(가격 60s · 인사이트 1h · 관계 엣지 24h), 장외 시간에는 종가 캐시로 주말 조회 대응
- **Observability** — 에이전트 호출마다 토큰 · 지연 · 상태를 JSON 로그로 남기고 Prometheus · Grafana · Loki · Sentry로 모니터링

<br>

## AI Models

| 모델 | 실행 환경 | 역할 |
|---|---|---|
| **EXAONE 3.5 7.8B** | Ollama 오픈 소스 모델 사용 (서버 구축 후 Tailscale) | 뉴스 관련성 판별. 경제 기사 선별, 기사→종목 매핑, 0~5점 스코어링 |
| **Claude Sonnet 4.6** | Anthropic API | 뉴스 통합 분석 · 기업 관계 발굴 |
| **Claude Haiku 4.5** | Anthropic API | 기사 요약 · 뉴스 랭킹 |
| **voyage-3** | Voyage AI API | 뉴스 중복 제거, 공시 청크 검색 |
| **Isotonic Regression** | scikit-learn | 과거 적중 기록으로 예측 confidence 재보정 |

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/images/pipeline-dark.png">
  <img src="docs/images/pipeline-light.png" alt="News to Insight LLM Pipeline">
</picture>

> 대량 처리(관련성 판별)는 호출 비용이 없는 로컬 모델(Ollama)이, 정밀 분석(영향 추론 · 관계 발굴)은 Claude가 담당합니다. 통과 기사가 0건이면 Claude를 호출하지 않습니다.

<br>

<br>

## Results

| 지표 | 결과 |
|---|---|
| **Magnitude Hit Rate** | **87.5%** (21/24) (예측 종목의 D+3 주가 변동폭이 ±2% 이상인 비율) |
| **API 응답 시간** | 8,146 ms → **21.5 ms** (Redis 캐시 적중 시, 삼성전자 인사이트 기준) |
| **관련성 판별 시간** | 4~5분 → **약 1분** (종목 × 기사 반복 호출 → 3단 배치 구조로 재설계) |
| **Look-ahead 누출** | **0건** (`verify_lookahead.py`로 검증) |

<sub>백테스트 기간 2026.05.20 – 06.03 (채점 24건). 표본이 작아 통계적 결론보다는 파이프라인 동작 검증 성격의 결과입니다.</sub>

<br>

<br>

## Project Structure

<details>
<summary>펼쳐보기</summary>

```
Stoogle
├── stoogle/
│   ├── backend/
│   │   ├── main.py              # FastAPI 앱 진입점
│   │   ├── tasks.py             # Celery Beat 스케줄 · 태스크
│   │   ├── routers/             # search · insight · news · relations
│   │   ├── services/            # stock · news · nlp · relation · cache
│   │   ├── agents/              # relevance · analysis · relation_discovery · calibrator · crawlers
│   │   ├── evaluation/          # backtest · look-ahead 검증 · 할루시네이션 · 메트릭 API
│   │   ├── models/              # SQLAlchemy ORM · Pydantic 스키마
│   │   └── scripts/             # 백테스트 실행 · 분석 스크립트
│   └── frontend/
│       └── src/
│           ├── pages/           # MainPage · SearchResultsPage · CompanyDetailPage
│           └── components/      # PriceChart · RelationGraph · NewsSection · ImpactList
├── docs/                        # README 이미지 · 다이어그램 원본
├── readme/                      # 모듈별 상세 설계 문서
└── docker-compose.yml           # PostgreSQL · Prometheus · Grafana · Loki
```

</details>

<br>

## Getting Started

<details>
<summary>펼쳐보기</summary>

**1. 환경 변수** — `stoogle/backend/.env`

```bash
DATABASE_URL=postgresql://stoogle:stoogle1234@localhost:5432/stoogle  # 미설정 시 SQLite 폴백
REDIS_URL=redis://localhost:6379/0
ANTHROPIC_API_KEY=...
VOYAGE_API_KEY=...
NAVER_CLIENT_ID=...
NAVER_CLIENT_SECRET=...
DART_API_KEY=...
OLLAMA_BASE_URL=http://localhost:11434   # EXAONE 서버 주소
OLLAMA_MODEL=exaone3.5:7.8b
```

**2. 인프라** (PostgreSQL + 모니터링, Redis)

```bash
docker-compose up -d
docker run -d -p 6379:6379 redis:7
```

**3. Backend**

```bash
pip install -r requirements.txt
cd stoogle/backend
uvicorn main:app --reload --port 8000        # Swagger: http://localhost:8000/docs
celery -A tasks worker --loglevel=info
celery -A tasks beat --loglevel=info
```

**4. Frontend**

```bash
cd stoogle/frontend
npm install
REACT_APP_USE_MOCK=false npm start           # http://localhost:3000
```

</details>

<br>

## Docs

| 문서 | 내용 |
|---|---|
| [News_README.md](readme/News_README.md) | 뉴스 영향 분석 모듈 설계 |
| [Relation_README.md](readme/Relation_README.md) | 기업 관계 모듈 설계 |
| [EVALUATION.md](readme/EVALUATION.md) | 백테스트 · 평가 체계 |
| [MONITORING.md](readme/MONITORING.md) | 관측성 · Prometheus 설정 |
