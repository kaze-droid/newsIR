from typing import List

from pydantic import BaseModel

class Article(BaseModel):
    url: str
    title: str
    content: str
    language: str
    location: str
    site: str
    date: str
    tags: List[str] = []
