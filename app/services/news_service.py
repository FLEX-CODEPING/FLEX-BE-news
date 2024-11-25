from typing import List
from app.models.dtos import (
    NewsArticleDTO,
    NewsArticleSourceDTO,
    SummaryItemDTO,
    SummaryRequestDTO,
)
from app.summary.individual_summarizer import IndividualSummarizer
from app.data.news_data_manager import NewsDataManager
from app.core.exceptions import SummaryError
import logging
import re
from app.config.settings import settings

logger = logging.getLogger(__name__)


class NewsService:
    def __init__(self):
        self.individual_summarizer = IndividualSummarizer()
        self.news_data_manager = NewsDataManager()

    async def get_news_articles(
        self, request: SummaryRequestDTO
    ) -> List[NewsArticleDTO]:
        """저장된 뉴스 기사 키워드에 맞춰 불러오기

        Args:
            request (SummaryRequestDTO): 요청 DTO
                keyword (str): 원하는 키워드
                press (List[PressName]): 원하는 언론사 리스트

        Returns:
            List[NewsArticleDTO]: 뉴스 기사 리스트
        """
        try:
            if request.keyword == "종합":
                all_articles = []
                for keyword in settings.NEWS_KEYWORD:
                    modified_dto = SummaryRequestDTO(
                        keyword=keyword, press=request.press, period=request.period
                    )
                    articles = await self.news_data_manager.retrieve_news_articles(
                        modified_dto, is_combined=True
                    )
                    all_articles.extend(articles)
                return all_articles
            else:
                articles = self.news_data_manager.retrieve_news_articles(request)
            if not articles:
                raise SummaryError(
                    "저장된 뉴스 기사가 없습니다.",
                    details={
                        "keyword": request.keyword,
                    },
                )
            return articles
        except Exception as e:
            error_message = f"뉴스 기사 불러오기 실패: {str(e)}"
            logger.error(error_message, exc_info=True)
            raise SummaryError(
                error_message,
                details={
                    "keyword": request.keyword,
                },
            )

    def convert_news_articles(
        self, articles: List[NewsArticleDTO]
    ) -> List[NewsArticleSourceDTO]:
        """데이터베이스 조회 결과를 API 응답 형식으로 변환

        NewsArticleDTO의 content를 100자로 제한하고 필요한 필드만 추출하여
        NewsArticleSourceDTO 형식으로 변환합니다.

        Args:
            articles (List[NewsArticleDTO]): DB 조회로 얻은 뉴스 기사 목록

        Returns:
            List[NewsArticleSourceDTO]: 변환된 뉴스 기사 목록

        Raises:
            DataProcessingError: 데이터 변환 중 오류 발생 시
        """
        return self.news_data_manager.convert_articles(articles)

    async def summarize_news(
        self, news_articles: List[NewsArticleDTO], keyword: str
    ) -> List[SummaryItemDTO]:
        """뉴스 기사 요약

        Args:
            news_articles (List[NewsArticleDTO]): 뉴스 기사 리스트
            keyword (str): 요약할 키워드

        Returns:
            List[SummaryItemDTO]: 요약된 뉴스 기사 리스트
        """
        try:
            accumulated_summary = await self.individual_summarizer.summarize(
                news_articles, keyword
            )
            return self._parse_summary(accumulated_summary)
        except Exception as e:
            error_message = f"기사 요약 실패: {str(e)}"
            logger.error(error_message, exc_info=True)
            raise SummaryError(
                error_message,
                details={
                    "keyword": keyword,
                    "article_count": len(news_articles),
                },
            )

    def _parse_summary(self, accumulated_summary: str) -> List[SummaryItemDTO]:
        """요약된 텍스트를 파싱하여 SummaryItemDTO 리스트로 반환

        Args:
            accumulated_summary (str): 요약된 텍스트

        Returns:
            List[SummaryItemDTO]: 파싱된 요약 리스트
        """
        summaries = []
        # 정규 표현식을 사용하여 번호가 매겨진 항목들을 분리
        items = re.split(r"(\d+\.\s)", accumulated_summary)[
            1:
        ]  # 첫 번째 빈 문자열 제거

        for i in range(0, len(items), 2):
            if i + 1 < len(items):
                number = items[i].strip()
                content = items[i + 1].strip()

                if ":" in content:
                    title, description = content.split(":", 1)
                    summaries.append(
                        SummaryItemDTO(
                            title=f"{number} {title.strip()}",
                            content=description.strip(),
                        )
                    )
                else:
                    # ':' 구분자가 없는 경우 전체를 content로 처리
                    summaries.append(SummaryItemDTO(title=number, content=content))

        return summaries
