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
    published_time: datetime
    url: str
    content: str
    keywords: str


class SummaryRequestDTO(BaseModel):
    keyword: str
    press: List[PressName]
    period: int


class SummaryItem(BaseModel):
    title: str
    content: str


class SummaryResult(BaseModel):
    summaries: List[SummaryItem]


class ApiResponse(BaseModel):
    isSuccess: bool = True
    code: str = "COMMON200"
    message: str = "성공"
    result: Optional[SummaryResult] = None
