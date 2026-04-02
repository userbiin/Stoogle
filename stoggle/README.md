# stoggle — 주식 종목 인사이트 플랫폼

> 어떤 기업을 검색해도 동일한 품질의 인사이트를 제공하는 "주식 전용 구글"

---

## 프로젝트 구조

```
stoggle/
├── frontend/                  # React 앱
│   ├── public/
│   │   └── index.html
│   ├── src/
│   │   ├── App.js             # 라우팅
│   │   ├── index.js           # 엔트리포인트
│   │   ├── pages/
│   │   │   ├── MainPage.js            # 구글 스타일 검색 홈
│   │   │   ├── SearchResultsPage.js   # 검색 결과 (동명기업 선택)
│   │   │   └── CompanyDetailPage.js   # 기업 상세 인사이트
│   │   ├── components/
│   │   │   ├── TopBar.js              # 상단 고정 검색바
│   │   │   ├── PriceChart.js          # Recharts 주가 차트
│   │   │   ├── WordCloudSection.js    # 키워드 시각화
│   │   │   ├── NewsSection.js         # 뉴스 목록 + 탭 필터
│   │   │   ├── RelationGraph.js       # D3 포스 그래프
│   │   │   ├── RelationList.js        # 연관 기업 목록
│   │   │   └── ImpactList.js          # 영향 종목 리스트
│   │   ├── utils/
│   │   │   └── mockData.js            # 백엔드 없이 개발용 목 데이터
│   │   └── styles/
│   │       └── global.css             # CSS 변수 + 리셋
│   └── package.json
│
├── backend/                   # FastAPI 앱
│   ├── main.py                # 앱 진입점 + CORS
│   ├── tasks.py               # Celery 자동화 스케줄러
│   ├── requirements.txt
│   ├── .env.example
│   ├── routers/
│   │   ├── search.py          # GET /api/v1/search?q=
│   │   ├── insight.py         # GET /api/v1/insight/{ticker}
│   │   ├── news.py            # GET /api/v1/news/{ticker}
│   │   └── relations.py       # GET /api/v1/relations/{ticker}
│   ├── services/
│   │   ├── stock_service.py   # pykrx 범용 주가 수집
│   │   ├── news_service.py    # 뉴스 크롤링 + 랭킹
│   │   ├── nlp_service.py     # 키워드 추출 + LLM 요약
│   │   └── relation_service.py # 상관계수 기반 관계 도출
│   ├── models/
│   │   ├── schemas.py         # Pydantic 응답 스키마
│   │   └── db_models.py       # SQLAlchemy ORM
│   └── agents/
│       └── news_agent.py      # LangChain 뉴스 에이전트
│
└── README.md
```

---

## 빠른 시작 (Claude Code에서 실행)

### 1단계 — 프론트엔드 실행

```bash
cd stoggle/frontend
npm install
npm start
# → http://localhost:3000
```

백엔드 없이도 mockData.js로 UI 전체를 확인할 수 있습니다.

---

### 2단계 — 백엔드 실행

```bash
cd stoggle/backend

# 가상환경 생성
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# 환경변수 설정
cp .env.example .env
# .env 파일에서 OPENAI_API_KEY, DART_API_KEY 입력

# DB 테이블 생성
python models/db_models.py

# 서버 시작
uvicorn main:app --reload --port 8000
# → http://localhost:8000/docs  (Swagger UI 자동 생성)
```

---

### 3단계 — Celery 자동화 (선택)

Redis가 필요합니다.

```bash
# Redis 실행 (Docker)
docker run -d -p 6379:6379 redis:7

# Celery 워커 실행
cd stoggle/backend
celery -A tasks worker --loglevel=info

# Celery Beat 스케줄러 실행 (별도 터미널)
celery -A tasks beat --loglevel=info
```

---

## API 엔드포인트

| Method | URL | 설명 |
|--------|-----|------|
| GET | `/api/v1/search?q={query}` | 기업명·종목코드 검색 |
| GET | `/api/v1/insight/{ticker}` | 기업 종합 인사이트 |
| GET | `/api/v1/news/{ticker}` | 기업 뉴스 목록 |
| GET | `/api/v1/relations/{ticker}` | 연관 기업 관계도 |
| GET | `/health` | 서버 상태 확인 |

---

## 외부 API 키 발급

| 서비스 | 발급 URL | 용도 |
|--------|---------|------|
| OpenAI | https://platform.openai.com | LLM 요약·관계 추출 |
| DART | https://opendart.fss.or.kr | 공시 데이터 |

---

## 개발 우선순위

1. **Phase 1** — `npm start`로 프론트 UI 확인 (mockData 사용)
2. **Phase 2** — FastAPI 백엔드 실행 + `/api/v1/search` 연동
3. **Phase 3** — 뉴스·주가 실데이터 연결
4. **Phase 4** — LLM 요약 + 관계 그래프 자동화
5. **Phase 5** — Celery로 전종목 자동 업데이트
