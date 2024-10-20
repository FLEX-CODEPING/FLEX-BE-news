from typing import List
from app.models.dto import PressDTO, NewsArticleDTO, SummaryRequestDTO
from app.crawler.news_crawler import NewsCrawler
from app.config.press_config import PRESS_CODE_MAP


class NewsCrawlingService:
    def __init__(self):
        self.news_crawler = NewsCrawler()

    async def crawl_news(self, request: SummaryRequestDTO) -> List[NewsArticleDTO]:
        press_list: List[PressDTO] = [
            PRESS_CODE_MAP[press.value]
            for press in request.press
            if press.value in PRESS_CODE_MAP
        ]
        return await self.news_crawler.crawl_and_save(
            request.period, request.keyword, press_list
        )
