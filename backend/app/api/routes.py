import logging
from typing import List, Dict, Tuple, Annotated
from datetime import datetime

from app.services.elasticsearch import ElasticsearchService
from app.models import Article, Tag
from datetime import datetime

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

class TagAggregationError(Exception):
    def __init__(self, start_date: str, end_date: str):
        self.message = f"Error aggregating tags from {start_date} to {end_date}"
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
    keywords: Annotated[List[str], Query()],
    ES_Service: ElasticsearchService = Depends(get_es_service),
):
    query = {
        "query": {
            "bool": {
                "should": [
                    item
                    for keyword in keywords
                    for item in [
                        {"match_phrase": {"content": {"query": keyword, "boost": 3}}},
                        {
                            "match": {
                                "content": {
                                    "query": keyword,
                                    "fuzziness": "AUTO",
                                    "prefix_length": 2,
                                }
                            }
                        },
                        {
                            "match": {
                                "tags": {
                                    "query": keyword,
                                    "fuzziness": "AUTO",
                                    "prefix_length": 2,
                                }
                            }
                        },
                    ]
                ],
                "minimum_should_match": 1,
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

    # Sort by the score
    retrieved_articles["hits"]["hits"] = sorted(
        retrieved_articles["hits"]["hits"], key=lambda x: x["_score"], reverse=True
    )

    return retrieved_articles


async def retrieve_tags(
    start_date: str,
    end_date: str,
    ES_Service: ElasticsearchService = Depends(get_es_service),
):
    non_tags = [
        "Singapore SINGAPORE",
        "Star Media Group Berhad",
        "KUALA LUMPUR",
        "ST SINGAPORE",
        "FILE SINGAPORE",
        "Report it to us",
        "Astro Awani",
        "Report it",
        "ST FILE SINGAPORE",
        "pleaded guilty",
        "pleading guilty",
        "plead guilty",
        "Astro AWANI",
    ]

    # Ensure the format is in yyyy-MM-dd
    try:
        start_date = datetime.strptime(start_date, "%Y-%m-%d")
        end_date = datetime.strptime(end_date, "%Y-%m-%d")

        if start_date > end_date:
            raise HTTPException(
                status_code=400,
                detail="Start date is after end date. Please ensure start_date is before end_date",
            )

    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid date format. Please use yyyy-MM-dd format E.g. 2024-03-31",
        )

    query = {
        "size": 0,
        "query": {
            "bool": {
                "must": [
                    {"range": {"date_obj": {"gte": start_date, "lte": end_date}}}
                ],
                "must_not": [
                    {"regexp": {"tags": "[\s\S]*\d+-D[\s\S]*"}},
                    {"regexp": {"tags": "\d+"}},
                    {"terms": {"tags": non_tags}},
                ],
            }
        },
        "aggs": {"tags": {"terms": {"field": "tags", "size": 1000}}},
    }

    retrieved_tags = ES_Service.search_document(query=query)
    if (
        not retrieved_tags
        or "hits" not in retrieved_tags
        or retrieved_tags["hits"]["total"]["value"] == 0
    ):
        raise TagAggregationError(start_date, end_date)
    
    tags = retrieved_tags['aggregations']['tags']['buckets']
    return tags



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
        fields=[
            "url",
            "title",
            "content",
            "language",
            "location",
            "site",
            "date",
            "tags",
        ],
    )

    if not retrieved_articles_results:
        raise HTTPException(status_code=404, detail="No articles found")

    logger.info(f"Retrieved articles: {retrieved_articles_results}")
    return [Article(**article) for article in retrieved_articles_results]

@router.get("/tags", tags=["tags"])
async def get_tags(
    start_date: str = "2024-05-01",
    end_date: str = "2024-06-30",
    top_n: int = 25,
    tags_data: Tuple[Dict, Dict] = Depends(retrieve_tags),
    ES_Service: ElasticsearchService = Depends(get_es_service),
):
    tags = tags_data
    if len(tags) == 0:
        raise HTTPException(status_code=404, detail="No tags found")
    
    if top_n > len(tags):
        top_n = len(tags)

    tags = tags[:top_n]
    return [Tag(tag=item['key'], count=item['doc_count']) for item in tags]


@router.get("/health")
async def health_check():
    return {"status": "healthy"}
