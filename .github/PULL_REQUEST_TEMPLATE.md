## 작업 내용
### cache_service.py
<!-- Redis Client 구현  
- reigstry (전종목 레지스트리 7일 간격)
- price:{ticker} (주가 변동 장 중에는 60초 간격) 
- history:{ticker} (주가 히스토리 10분 간격)
- news:{ticker} (뉴스 1시간 간격)-->

### stock_service.py
<!-- KRX 주가 수집 모듈 구현 
- 주가 종목 레지스트리 Redis 에 캐싱 
- search_companies() 함수 재작성 : Redis caching 해 놓고 search -> 서치 시간 감소 
- get_current_price(), get_prcie_history() : Redis cache 우선 조회 -->
### tasks.py 
<!-- Celery Scheduler 재작성
- fetch_top200_prices() 에서 기존 종목별로 주가를 60초 마다 갱신하면 API 과다 사용됨 -> pykrx 라이브러리 사용해서 전종목을 날짜 기준으로 한꺼번에 가져옴
- crawl_all_new : 1시간 주기로 전종목 뉴스 수집 추가 -->
### news_agent.py 
<!-- run_impact_analysis() : GPT-4o-mini 연동하여 1차 필터링 -->
### relation_service.py / realtions.py 
<!-- 삼성, 하이닉스로 하드코딩 되어있던 것 LLM 에이전트와 연동 가능하도록 교체 -->


## 관련 이슈
closes #

## 체크리스트
- [ ] 로컬에서 테스트 완료
- [ ] 기존 기능 깨지지 않음
- [ ] 환경변수 env에 추가한 항목 없음 (있으면 Notion에 업데이트)

## 참고 사항
<!-- Naver News 의 finance 부분만 수집할건지? → services/news_services.py  -->
