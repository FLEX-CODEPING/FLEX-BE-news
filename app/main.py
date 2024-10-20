import logging
from fastapi import FastAPI, APIRouter, Query, BackgroundTasks
from typing import List
import uuid
from datetime import datetime
from app.services.news_crawling_service import NewsCrawlingService
from app.services.news_summary_service import NewsSummaryService
from app.models.enums import PressName
from app.models.dtos import SummaryRequestDTO, ApiResponseDTO

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename="app.log",
    encoding="utf-8",
)

logger = logging.getLogger(__name__)

app = FastAPI(title="News Summarizer")

news_router = APIRouter(prefix="/api/news", tags=["news"])

# 작업 상태를 저장할 딕셔너리
tasks = {}

news_crawling_service = NewsCrawlingService()
news_summary_service = NewsSummaryService()


@news_router.get("/summarize", response_model=ApiResponseDTO)
async def summarize(
    background_tasks: BackgroundTasks,
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
    task_id = str(uuid.uuid4())
    tasks[task_id] = {"status": "pending", "result": None}

    request_dto = SummaryRequestDTO(keyword=keyword, press=press, period=period)
    background_tasks.add_task(process_summary_task, task_id, request_dto)

    return ApiResponseDTO(
        isSuccess=True, code="COMMON200", message="성공", result={"task_id": task_id}
    )


@news_router.get("/status/{task_id}", response_model=ApiResponseDTO)
async def get_status(task_id: str):
    task = tasks.get(task_id)
    if not task:
        return ApiResponseDTO(
            isSuccess=False, code="COMMON404", message="Task not found"
        )
    return ApiResponseDTO(
        isSuccess=True,
        code="COMMON200",
        message="성공",
        result={"status": task["status"]},
    )


@news_router.get("/result/{task_id}", response_model=ApiResponseDTO)
async def get_result(task_id: str):
    task = tasks.get(task_id)
    if not task:
        return ApiResponseDTO(
            isSuccess=False, code="COMMON404", message="Task not found"
        )
    if task["status"] != "completed":
        return ApiResponseDTO(
            isSuccess=False,
            code="COMMON404",
            message="Task not completed",
            result={"status": task["status"]},
        )
    return ApiResponseDTO(
        isSuccess=True,
        code="COMMON200",
        message="성공",
        result={"status": task["result"]},
    )


async def process_summary_task(task_id: str, request: SummaryRequestDTO):
    try:
        tasks[task_id]["status"] = "crawling"
        news_articles = await news_crawling_service.crawl_news(request)

        tasks[task_id]["status"] = "summarizing"
        summary_items = await news_summary_service.summarize_news(
            news_articles, request.keyword
        )

        # SummaryItemDTO 리스트를 문자열로 변환
        summary_text = "\n".join(
            [f"{item.title}: {item.content}" for item in summary_items]
        )

        result = {
            "summaries": summary_text,
            "sources": [
                {
                    "date": datetime.combine(
                        article.published_date, article.published_time
                    ).isoformat(),
                    "title": article.title,
                    "content": article.content,
                    "url": article.url,
                }
                for article in news_articles
            ],
        }

        tasks[task_id]["status"] = "completed"
        tasks[task_id]["result"] = result
    except Exception as e:
        tasks[task_id]["status"] = "failed"
        tasks[task_id]["result"] = str(e)
        logging.error(f"Error occurred while processing task {task_id}: {str(e)}")


app.include_router(news_router)
