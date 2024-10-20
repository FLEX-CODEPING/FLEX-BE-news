import requests
import json
from typing import List
from app.config.env import settings
from app.summary.accumulated_summarizer import AccumulatedSummarizer
from app.models.dto import NewsArticleDTO
from app.core.exceptions import SummaryError
import logging

logger = logging.getLogger(__name__)


class IndividualSummarizer:
    def __init__(self):
        self.naver_client_id = settings.naver_client_id
        self.naver_client_secret = settings.naver_client_secret
        self.accumulated_summarizer = AccumulatedSummarizer()

    def summarize(self, articles: List[NewsArticleDTO], keyword: str) -> str:
        try:
            individual_summaries = self._generate_individual_summary(articles)
            accumulated_summary = self.accumulated_summarizer.accumulated_summary(
                keyword, individual_summaries
            )
            return accumulated_summary
        except Exception as e:
            error_message = f"기사 요약 실패: {str(e)}"
            logger.error(error_message, exc_info=True)
            raise SummaryError(
                error_message,
                details={
                    "keyword": keyword,
                    "article_count": len(articles),
                },
            )

    def _generate_individual_summary(self, articles: List[NewsArticleDTO]) -> List[str]:
        summaries = []
        for article in articles:
            try:
                summary = self._summarize_article(article)
                summaries.append(summary)
            except Exception as e:
                logger.warning(
                    f"개별 기사 요약 실패: {article.title} - {str(e)}", exc_info=True
                )

        if not summaries:
            error_message = "모든 기사 요약 실패"
            logger.error(error_message)
            raise SummaryError(error_message, details={"article_count": len(articles)})
        logger.info(f"Generated {len(summaries)} individual summaries")
        return summaries

    def _summarize_article(self, article: NewsArticleDTO) -> str:
        title = article.title
        content = article.content
        try:
            response = requests.post(
                "https://naveropenapi.apigw.ntruss.com/text-summary/v1/summarize",
                headers={
                    "Content-Type": "application/json",
                    "X-NCP-APIGW-API-KEY-ID": self.naver_client_id,
                    "X-NCP-APIGW-API-KEY": self.naver_client_secret,
                },
                data=json.dumps(
                    {
                        "document": {"title": title, "content": content},
                        "option": {
                            "language": "ko",
                            "model": "news",
                            "tone": 2,
                            "summaryCount": 3,
                        },
                    }
                ),
            )
            response.raise_for_status()
            summary = response.json()["summary"]
            return summary
        except Exception as e:
            logger.error(f"Failed to summarize article {title}: {str(e)}")
            return None
