import logging
from fastapi import FastAPI, APIRouter, Query
from fastapi.security import HTTPBearer
from typing import List
from app.services.news_service import NewsService
from app.models.enums import PressName
from app.models.dtos import (
    SummaryRequestDTO,
    ApiResponseDTO,
    NewsArticleSourceDTO,
    SummaryItemDTO,
)
from app.config.swagger_config import setup_swagger

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename="app.log",
    encoding="utf-8",
)

logger = logging.getLogger(__name__)

# FastAPI 인스턴스 생성
app = FastAPI(
    docs_url="/api/news-service/swagger-ui.html",
    openapi_url="/api/news-service/openapi.json",
    title="AI News Controller"
)

from fastapi.middleware.cors import CORSMiddleware

origins = [
    "http://localhost:8080",
    "http://localhost:3000",
    "http://do-flex.co.kr:3000",
    "http://dev.do-flex.co.kr:8080"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

setup_swagger(app)

security = HTTPBearer()

news_router = APIRouter(prefix="/api/news-summary", tags=["news"])

news_service = NewsService()


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
    주어진 키워드와 언론사에 대한 뉴스를 크롤링하고 요약합니다.

    - keyword: 검색할 키워드
    - press: 검색할 언론사 코드 목록 (hk: 한국경제, mk: 매일경제, sed: 서울경제), 여러 언론사를 선택할 경우 쿼리 스트링 예)press=hk&press=mk
    - period: 기간(일) (default: 1)
    """

    try:
        request_dto = SummaryRequestDTO(keyword=keyword, press=press, period=period)

        news_articles = await news_service.get_news_articles(request_dto)
        summary_items = await news_service.summarize_news(
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
