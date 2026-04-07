# stoogle — 주식 종목 인사이트 플랫폼


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

## 프론트 실행 방법

```bash
cd stoggle/frontend
npm install
npm start
# → http://localhost:3000
```


---

### 백엔드 실행 방법

```bash
cd stoggle/backend

python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

pip install -r requirements.txt

cp .env.example .env
# .env 파일에서 OPENAI_API_KEY, DART_API_KEY 입력

python models/db_models.py

uvicorn main:app --reload --port 8000
# → http://localhost:8000/docs  (Swagger UI 자동 생성)
```

---

### Celery 자동화 (option)

Redis 필요

```bash
# Redis 실행 (Docker에서 실행)
docker run -d -p 6379:6379 redis:7

# Celery 워커 실행
cd stoggle/backend
celery -A tasks worker --loglevel=info

# Celery Beat 스케줄러 실행 
celery -A tasks beat --loglevel=info
```

---

## API 명세

| Method | URL | 설명 |
|--------|-----|------|
| GET | `/api/v1/search?q={query}` | 기업명·종목코드 검색 |
| GET | `/api/v1/insight/{ticker}` | 기업 종합 인사이트 |
| GET | `/api/v1/news/{ticker}` | 기업 뉴스 목록 |
| GET | `/api/v1/relations/{ticker}` | 연관 기업 관계도 |
| GET | `/health` | 서버 상태 확인 |


