from typing import List
from app.models.dtos import NewsArticleDTO, SummaryItemDTO
from app.summary.individual_summarizer import IndividualSummarizer
from app.core.exceptions import SummaryError
import logging
import re

logger = logging.getLogger(__name__)


class NewsService:
    def __init__(self):
        self.individual_summarizer = IndividualSummarizer()

    def get_news_articles(self, keyword: str) -> List[NewsArticleDTO]:
        pass

    async def summarize_news(
        self, news_articles: List[NewsArticleDTO], keyword: str
    ) -> List[SummaryItemDTO]:
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
        summaries = []
        # 정규 표현식을 사용하여 번호가 매겨진 항목들을 분리
        items = re.split(r"(\d+\.)", accumulated_summary)[1:]  # 첫 번째 빈 문자열 제거

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
