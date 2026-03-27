from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

load_dotenv()

from routers import search, insight, news, relations

app = FastAPI(
    title="stoggle API",
    description="주식 종목 인사이트 범용 백엔드",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(search.router,    prefix="/api/v1", tags=["search"])
app.include_router(insight.router,   prefix="/api/v1", tags=["insight"])
app.include_router(news.router,      prefix="/api/v1", tags=["news"])
app.include_router(relations.router, prefix="/api/v1", tags=["relations"])


@app.get("/health")
def health():
    return {"status": "ok"}
