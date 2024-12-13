from pydantic import BaseModel
from typing import List, Literal, Optional, Union
from datetime import datetime
from .enums import PressName


class PressDTO(BaseModel):
    code: str
    name: str
    domain: str


class NewsArticleDTO(BaseModel):
    title: str
    published_date: datetime
    url: str
    content: str
    keyword: str
    press: str
    summary: Optional[str] = None


class NewsArticleSourceDTO(BaseModel):
    date: datetime
    title: str
    content: str
    url: str
    press: str


class SummaryRequestDTO(BaseModel):
    type: Literal["summary"] = "summary"
    keyword: str
    press: List[PressName]
    period: int = 1


class SummaryItemDTO(BaseModel):
    title: str
    content: str


class SummaryResponseDTO(BaseModel):
    summaries: Optional[List[SummaryItemDTO]] = None
    sources: Optional[List[NewsArticleSourceDTO]] = None


class NewsListResponseDTO(BaseModel):
    type: Literal["news_list"] = "news_list"
    sources: List[NewsArticleSourceDTO]


class ApiResponseDTO(BaseModel):
    isSuccess: bool = True
    code: str = "COMMON200"
    message: str = "성공"
    result: Optional[Union[SummaryResponseDTO, List[NewsListResponseDTO]]] = None
