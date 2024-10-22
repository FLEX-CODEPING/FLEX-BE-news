import logging
from fastapi import FastAPI, APIRouter, Query
from typing import List
from datetime import datetime
from app.services.news_crawling_service import NewsCrawlingService
from app.services.news_summary_service import NewsSummaryService
from app.models.enums import PressName
from app.models.dtos import (
    SummaryRequestDTO,
    ApiResponseDTO,
    NewsArticleSourceDTO,
    SummaryItemDTO,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename="app.log",
    encoding="utf-8",
)

logger = logging.getLogger(__name__)

app = FastAPI(news_router = APIRouter(docs_url="/api/news-service/swagger-ui.html",
                                          openapi_url="/api/news-service/openapi.json", title="AI News Controller")

news_router = APIRouter(prefix="/api/news-summary", tags=["news"])

# 작업 상태를 저장할 딕셔너리
tasks = {}

news_crawling_service = NewsCrawlingService()
news_summary_service = NewsSummaryService()


@news_router.get("/", response_model=ApiResponseDTO)
async def summarize(
    keyword: str = Query(...),
    press: List[PressName] = Query(
        default=["hk"],
        description="한국경제: hk, 매일경제: mk, 서울경제: sed<br><i>여러 언론사 선택 가능(컨트롤+클릭 혹은 쉬프트+클릭)</i>",
    ),
    period: int = Query(default=1, description="기간(일)"),
):
    """
    <h3><strong>clova summary는 하루 50회 제한이 있습니다. chatgpt는 크레딧이 5달러이므로 유념해주세요.</strong></h3> 주어진 키워드와 언론사에 대한 뉴스를 크롤링하고 요약합니다.

    - keyword: 검색할 키워드
    - press: 검색할 언론사 코드 목록 (hk: 한국경제, mk: 매일경제, sed: 서울경제), 여러 언론사를 선택할 경우 쿼리 스트링 예)press=hk&press=mk
    - period: 검색할 기간 (일)

    결과로 작업 ID가 반환되며, 이를 통해 작업 상태와 결과를 조회할 수 있습니다.
    """

    try:
        request_dto = SummaryRequestDTO(keyword=keyword, press=press, period=period)

        news_articles = await news_crawling_service.crawl_news(request_dto)
        summary_items = await news_summary_service.summarize_news(
            news_articles, request_dto.keyword
        )

        summary_text = [
            SummaryItemDTO(title=item.title, content=item.content)
            for item in summary_items
        ]

        articles_dto = []
        for row in news_articles:
            try:
                # row의 published_time과 published_date를 합쳐 NewsArticleSourceDTO로 변환
                date_combined = datetime.combine(
                    row.published_date.date(), row.published_time.time()
                )
                articles_dto.append(
                    NewsArticleSourceDTO(
                        date=date_combined,
                        title=row.title,
                        # content를 100자로 제한
                        content=row.content[:100] + "..."
                        if len(row.content) > 50
                        else row.content,
                        url=row.url,
                    )
                )
            except Exception as e:
                logger.error(
                    f"행을 NewsArticleSourceDTO로 변환 중 오류: {str(e)}", exc_info=True
                )

        logger.info(f"summaries: {summary_text}")
        logger.info(f"articles_dto: {articles_dto}")

        return ApiResponseDTO(
            isSuccess=True,
            code="COMMON200",
            message="성공",
            result={"summaries": summary_text, "sources": articles_dto},
        )

    except Exception as e:
        logging.error(f"Error occurred while processing task: {str(e)}")
        return ApiResponseDTO(
            isSuccess=False, code="COMMON500", message=f"처리 중 오류 발생: {str(e)}"
        )


app.include_router(news_router)
