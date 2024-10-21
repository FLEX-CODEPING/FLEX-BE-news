import openai
from typing import List
from app.config.env import settings
from app.core.exceptions import SummaryError
import logging

logger = logging.getLogger(__name__)


class AccumulatedSummarizer:
    def __init__(self):
        self.openai_api_key = settings.openai_api_key

    def accumulated_summary(self, keyword: str, summaries: List[str]) -> str:
        try:
            openai.api_key = self.openai_api_key

            summaries = [summary for summary in summaries if summary is not None]
            summaries_str = "\n".join(summaries)

            messages = f"""동일 주제 복수의 기사, 주제: {keyword}
            {summaries_str}"""

            persona_data = """당신은 금융 전문 분석가입니다. 키워드와 요약 기사를 바탕으로 주요 정보를 나열하십시오. 각 항목은 간결하고 사실적으로 기술하며 격식체를 사용하십시오. 예시:
            "1. 코스피 급락: 코스피 지수가 전 거래일 대비 8.77% 하락한 2,441.55로 마감했습니다.
            2. 코스닥 폭락: 코스닥 지수는 11.30% 하락한 691.28로 마감하며 700선이 무너졌습니다.
            3. 시가총액 감소: 하루 만에 235조 원의 시가총액이 증발했습니다.
            4. 주요 기업 주가 하락: 삼성전자는 10.30%, SK하이닉스는 9.87% 하락했습니다.
            5. 시장 조치 발동: '사이드카'와 '서킷브레이커'가 4년 5개월 만에 발동되었습니다"
            중복 없이 간결하게 요약 내용만 기술하십시오. 부연 설명은 생략하십시오."""

            response = openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": persona_data,
                    },
                    {
                        "role": "user",
                        "content": messages,
                    },
                ],
                max_tokens=250,
                temperature=1.0,
            )

            return response.choices[0].message.content
        except openai.APIError as e:
            error_msg = f"OpenAI API 오류: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return SummaryError(error_msg, details={"keyword": keyword})
        except Exception as e:
            error_msg = f"종합 요약 생성 실패: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise SummaryError(
                error_msg, details={"keyword": keyword, "summary_count": len(summaries)}
            )
