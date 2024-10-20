import json
from typing import List
from app.config.env import settings
from app.summary.accumulated_summarizer import AccumulatedSummarizer
from app.models.dto import NewsArticleDTO
from app.core.exceptions import SummaryError
import logging
import asyncio
import aiohttp

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

    async def _generate_individual_summary(
        self, articles: List[NewsArticleDTO]
    ) -> List[str]:
        async with aiohttp.ClientSession() as session:
            tasks = [self._summarize_article(session, article) for article in articles]
            summaries = await asyncio.gather(*tasks, return_exceptions=True)

        valid_summaries = [summary for summary in summaries if isinstance(summary, str)]

        if not valid_summaries:
            error_message = "모든 기사 요약 실패"
            logger.error(error_message)
            raise SummaryError(error_message, details={"article_count": len(articles)})

        logger.info(f"Generated {len(valid_summaries)} individual summaries")
        return valid_summaries

    async def _summarize_article(
        self, session: aiohttp.ClientSession, article: NewsArticleDTO
    ) -> str:
        url = "https://naveropenapi.apigw.ntruss.com/text-summary/v1/summarize"
        headers = {
            "Content-Type": "application/json",
            "X-NCP-APIGW-API-KEY-ID": self.naver_client_id,
            "X-NCP-APIGW-API-KEY": self.naver_client_secret,
        }
        data = {
            "document": {"title": article.title, "content": article.content},
            "option": {
                "language": "ko",
                "model": "news",
                "tone": 2,
                "summaryCount": 3,
            },
        }

        try:
            async with session.post(
                url, headers=headers, data=json.dumps(data)
            ) as response:
                response.raise_for_status()
                result = await response.json()
                return result["summary"]
        except Exception as e:
            logger.error(f"Failed to summarize article {article.title}: {str(e)}")
            return None
