import logging
from typing import List, Dict, Tuple, Annotated
from datetime import datetime

from app.services.elasticsearch import ElasticsearchService
from app.models.article import Article

from pydantic import BaseModel
from fastapi import APIRouter, HTTPException, Depends, Query

router = APIRouter()
logger = logging.getLogger(__name__)


# Exceptions
class URLNotFoundError(Exception):
    def __init__(self, url: str):
        self.url = url
        self.message = f"No article found with URL: {url}"
        super().__init__(self.message)

class KeywordNotFoundError(Exception):
    def __init__(self, keywords: List[str]):
        self.keywords = keywords
        self.message = f"No articles found with keywords: {keywords}"
        super().__init__(self.message)


# Helper functions
async def get_es_service() -> ElasticsearchService:
    """
    Dependency function to get ElasticsearchService instance
    """
    return router.es_service


async def get_similar_articles(
    url: str, ES_Service: ElasticsearchService = Depends(get_es_service)
):

    query = {
        "query": {"term": {"url": url}},
    }

    retrieved_article = ES_Service.search_document(query=query)

    # Check if the article was retrieved
    if (
        not retrieved_article
        or "hits" not in retrieved_article
        or retrieved_article["hits"]["total"]["value"] == 0
    ):
        raise URLNotFoundError(url)

    try:
        query_vector = ES_Service.get_field(
            response=retrieved_article, field="article_embedding"
        )[0]
    # No article was retrieve
    except Exception as e:
        logger.error(e)
        raise URLNotFoundError(url)

    # Get all similar articles using ANN
    query = {
        "knn": {
            "field": "article_embedding",
            "k": 20,
            "num_candidates": 100,
            "query_vector": query_vector,
            # Minimum Similarity Threshold
            "similarity": 0.75,
        },
        # Sort by the score
        "sort": [{"_score": "desc"}],
    }

    similar_articles = ES_Service.search_document(query=query)

    return (retrieved_article, similar_articles)


async def get_article_by_keywords(
    keywords: Annotated[List[str], Query()], ES_Service: ElasticsearchService = Depends(get_es_service)
):
    query = {
        "query": {
            "bool": {
                "should": [
                    {"multi_match": {"query": keyword, "fields": ["content", "tags"], "operator": "and", "fuzziness": "2"}}
                    for keyword in keywords
                ]
            }
        }
    }

    retrieved_articles = ES_Service.search_document(query=query)
    if (
        not retrieved_articles
        or "hits" not in retrieved_articles
        or retrieved_articles["hits"]["total"]["value"] == 0
    ):
        raise KeywordNotFoundError(keywords)

    return retrieved_articles


@router.get("/filter/date", tags=["filter"])
async def filter_date(
    url: str,
    filter_duration: int = 30,
    articles_data: Tuple[Dict, Dict] = Depends(get_similar_articles),
    ES_Service: ElasticsearchService = Depends(get_es_service),
):
    if filter_duration <= 0:
        raise HTTPException(
            status_code=400, detail="filter duration must be a positive integer"
        )

    target_article, similar_articles = articles_data

    try:
        current_date_text = ES_Service.get_field(response=target_article, field="date")[
            0
        ]
        current_date = datetime.strptime(current_date_text, "%d %b %Y")
    except (IndexError, ValueError):
        raise HTTPException(status_code=500, detail="Error parsing article date")

    similar_ids = ES_Service.get_ids(response=similar_articles)
    if len(similar_ids) == 0:
        raise HTTPException(status_code=404, detail="No similar articles found")

    dates_str = ES_Service.get_field(response=similar_articles, field="date")
    article_dates = [datetime.strptime(date_str, "%d %b %Y") for date_str in dates_str]

    filtered_ids = [
        article_id
        for article_id, article_date in zip(similar_ids, article_dates)
        if abs((current_date - article_date).days) <= filter_duration
    ]

    # Get all articles from the ids
    query = {"query": {"ids": {"values": filtered_ids}}}
    filtered_articles = ES_Service.search_document(query=query)
    if not filtered_articles:
        raise HTTPException(
            status_code=500, detail="Error retrieving filtered articles"
        )

    filtered_articles_results = ES_Service.get_fields(
        response=filtered_articles,
        fields=["url", "title", "content", "language", "location", "site", "date"],
    )
    if not filtered_articles_results:
        raise HTTPException(status_code=404, detail="No articles found after filtering")

    # Sort filtered articles by date
    filtered_articles_results = sorted(
        filtered_articles_results,
        key=lambda x: datetime.strptime(x["date"], "%d %b %Y"),
        reverse=True,
    )

    logger.info(f"Filtered articles: {filtered_articles_results}")
    return [Article(**article) for article in filtered_articles_results]


@router.get("/filter/site", tags=["filter"])
async def filter_site(
    url: str,
    articles_data: Tuple[Dict, Dict] = Depends(get_similar_articles),
    ES_Service: ElasticsearchService = Depends(get_es_service),
):

    target_article, similar_articles = articles_data

    current_site = ES_Service.get_field(response=target_article, field="site")[0]

    similar_ids = ES_Service.get_ids(response=similar_articles)
    if len(similar_ids) == 0:
        raise HTTPException(status_code=404, detail="No similar articles found")

    article_sites = ES_Service.get_field(response=similar_articles, field="site")

    filtered_ids = [
        article_id
        for article_id, article_site in zip(similar_ids, article_sites)
        if article_site == current_site
    ]

    # Get all articles from the ids
    query = {"query": {"ids": {"values": filtered_ids}}}

    filtered_articles = ES_Service.search_document(query=query)
    if not filtered_articles:
        raise HTTPException(
            status_code=500, detail="Error retrieving filtered articles"
        )

    filtered_articles_results = ES_Service.get_fields(
        response=filtered_articles,
        fields=["url", "title", "content", "language", "location", "site", "date"],
    )
    if not filtered_articles_results:
        raise HTTPException(status_code=404, detail="No articles found after filtering")

    logger.info(f"Filtered articles: {filtered_articles_results}")
    return [Article(**article) for article in filtered_articles_results]


@router.get("/search", tags=["search"])
async def keywordSearch(
    keywords: Annotated[List[str], Query()],
    articles_data: Tuple[Dict, Dict] = Depends(get_article_by_keywords),
    ES_Service: ElasticsearchService = Depends(get_es_service),
):
    retrieved_articles = articles_data

    retrieved_articles_results = ES_Service.get_fields(
        response=retrieved_articles,
        fields=["url", "title", "content", "language", "location", "site", "date", "tags"],
    )

    if not retrieved_articles_results:
        raise HTTPException(status_code=404, detail="No articles found")
    
    logger.info(f"Retrieved articles: {retrieved_articles_results}")
    return [Article(**article) for article in retrieved_articles_results]

@router.get("/health")
async def health_check():
    return {"status": "healthy"}
