import json
from typing import List
from app.config.settings import settings
from app.summary.accumulated_summarizer import AccumulatedSummarizer
from app.models.dtos import NewsArticleDTO
from app.core.exceptions import SummaryError
import logging
import asyncio
import aiohttp
import openai

logger = logging.getLogger(__name__)


class IndividualSummarizer:
    def __init__(self):
        self.openai_api_key = settings.openai_api_key
        self.accumulated_summarizer = AccumulatedSummarizer()

    async def summarize(self, articles: List[NewsArticleDTO], keyword: str) -> str:
        try:
            individual_summaries = await self._generate_individual_summary(
                articles, keyword
            )
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
        self, articles: List[NewsArticleDTO], keyword: str
    ) -> List[str]:
        if not articles:
            error_message = "기사 목록이 비어 있습니다."
            logger.error(error_message)
            raise SummaryError(error_message, details={"keyword": keyword})

        async with aiohttp.ClientSession() as session:
            tasks = [
                self._summarize_article(session, article, keyword)
                for article in articles
            ]
            summaries = await asyncio.gather(*tasks, return_exceptions=True)

        valid_summaries = [summary for summary in summaries if isinstance(summary, str)]

        if not valid_summaries:
            error_message = "모든 기사 요약 실패"
            logger.error(error_message)
            raise SummaryError(error_message, details={"article_count": len(articles)})

        logger.info(f"Generated {len(valid_summaries)} individual summaries")
        return valid_summaries

    async def _summarize_article(
        self, session: aiohttp.ClientSession, article: NewsArticleDTO, keyword: str
    ) -> str:

        try:
            openai.api_key = self.openai_api_key

            persona_data = """
            뉴스 기사를 분야별 핵심 정보 중심으로 3문장 이내로 요약해주세요.

            공통 요약 규칙:
            - '~했다'로 문장 종결
            - 객관적 사실만 포함 (분석/전망/해석 제외)
            - 구체적 날짜와 수치 유지

            분야별 포함할 핵심 정보:
            금융/증권: 지수 변동(등락폭/비율), 거래 주체별 매매 동향, 주요 거래 금액
            산업/기업: 기업명, 핵심 사건, 규모/금액
            정치/정책: 정책/법안 내용, 관련 기관/인물, 시행 시기
            국제/글로벌: 발생 국가/지역, 핵심 당사자, 국내 영향
            """

            response = openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": persona_data,
                    },
                    {
                        "role": "user",
                        "content": article.content,
                    },
                ],
                max_tokens=250,
                temperature=1.0,
            )

            return response.choices[0].message.content
        except openai.APIError as e:
            error_msg = f"OpenAI API 오류: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return SummaryError(error_msg)
        except Exception as e:
            error_msg = f"단문 요약 생성 실패: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise SummaryError(error_msg, details={"keyword": keyword})
