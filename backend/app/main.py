from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.config import settings
from app.services.elasticsearch import ElasticsearchService


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Setup
    index_name = settings.INDEX_NAME
    bi_encoder = settings.BI_ENCODER
    elastic_password: str = settings.ELASTIC_PASSWORD
    router.es_service = ElasticsearchService(bi_encoder, index_name, elastic_password)

    yield
    # Teardown

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=settings.ALLOWED_HOSTS
)

app.include_router(router)
