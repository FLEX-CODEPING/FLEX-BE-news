import logging
from fastapi import FastAPI, APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer
from typing import List
from app.config.eureka_client import eureka_lifespan
from app.services.news_service import NewsService
from app.config.settings import settings
from app.models.enums import PressName
from app.models.dtos import (
    SummaryRequestDTO,
    ApiResponseDTO,
)
from app.config.swagger_config import setup_swagger

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename="app.log",
    encoding="utf-8",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger(__name__)

# FastAPI 인스턴스 생성
app = FastAPI(
    docs_url="/api/news-service/swagger-ui.html",
    openapi_url="/api/news-service/openapi.json",
    title="AI News Controller",
    lifespan=eureka_lifespan,
)


@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"isSuccess": False, "code": "COMMON500", "message": str(exc.detail)},
    )


from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
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
    주어진 키워드와 언론사에 대한 뉴스를 크롤링하고 요약합니다. "종합" 키워드는 데이터가 너무 많아 1일치만 불러옵니다.

    - keyword: 검색할 키워드, 종합 키워드는 "종합"으로 입력
    - press: 검색할 언론사 코드 목록 (hk: 한국경제, mk: 매일경제, sed: 서울경제), 여러 언론사를 선택할 경우 쿼리 스트링 예)press=hk&press=mk
    - period: 기간(일) (default: 1)
    """

    try:
        request_dto = SummaryRequestDTO(keyword=keyword, press=press, period=period)

        news_articles = await news_service.summarized_news(request_dto)

        return ApiResponseDTO(
            isSuccess=True, code="COMMON200", message="성공", result=news_articles
        )

    except Exception as e:
        logging.error(f"Error occurred while processing task: {str(e)}")
        raise HTTPException(status_code=500, detail=f"뉴스 요약 중 오류 발생: {str(e)}")


@news_router.get("/todaynews", response_model=ApiResponseDTO)
async def today_news():
    """
    메인 페이지에 띄울 뉴스 헤드라인을 목록으로 띄웁니다.
    """

    try:
        final_news_articles = await news_service.headline_news()

        return ApiResponseDTO(
            isSuccess=True,
            code="COMMON200",
            message="성공",
            result={"sources": final_news_articles},
        )
    except Exception as e:
        logging.error(f"Error occurred while processing task: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"뉴스 헤드라인 불러오기 중 오류 발생: {str(e)}",
        )


app.include_router(news_router)
