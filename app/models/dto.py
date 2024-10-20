from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from .enums import PressName


class PressDTO(BaseModel):
    code: str
    name: str
    domain: str


class NewsArticleDTO(BaseModel):
    title: str
    source: str
    published_date: datetime
    url: str
    content: str
    keywords: str


class SummaryRequestDTO(BaseModel):
    keyword: str
    press: List[PressName]
    period: int


class SummaryResultDTO(BaseModel):
    task_id: str
    status: str
    result: Optional[str] = None
