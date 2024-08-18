from typing import List

from pydantic import BaseModel

class Tag(BaseModel):
    tag: str
    count: int
