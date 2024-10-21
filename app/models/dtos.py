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


class NewsArticleSourceDTO(BaseModel):
    date: datetime
    title: str
    content: str
    url: str


class SummaryRequestDTO(BaseModel):
    keyword: str
    press: List[PressName]
    period: int


class SummaryItemDTO(BaseModel):
    title: str
    content: str


class SummaryResponseDTO(BaseModel):
    summaries: Optional[List[SummaryItemDTO]] = None
    sources: Optional[List[NewsArticleSourceDTO]] = None
    status: Optional[str] = None
    task_id: Optional[str] = None


class ApiResponseDTO(BaseModel):
    isSuccess: bool = True
    code: str = "COMMON200"
    message: str = "성공"
    result: Optional[SummaryResponseDTO] = None
