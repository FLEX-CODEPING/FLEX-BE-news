from typing import List
from app.models.dto import NewsArticleDTO
from app.summary.individual_summarizer import IndividualSummarizer
from app.core.exceptions import SummaryError
import logging

logger = logging.getLogger(__name__)


class NewsSummaryService:
    def __init__(self):
        self.individual_summarizer = IndividualSummarizer()

    def summarize_news(self, news_articles: List[NewsArticleDTO], keyword: str):
        try:
            return self.individual_summarizer.summarize(news_articles, keyword)
        except SummaryError as e:
            raise e
        except Exception as e:
            logger.error(f"Error occurred while summarizing news: {str(e)}")
            raise SummaryError(
                "뉴스 요약 서비스 오류",
                details={
                    "keyword": keyword,
                    "article_count": len(news_articles),
                    "error": str(e),
                },
            )
