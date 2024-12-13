import json
from typing import List
from app.config.settings import settings
from app.models.dtos import (
    NewsArticleDTO,
    SummaryRequestDTO,
    NewsArticleSourceDTO,
    SummaryResponseDTO,
)
import pandas as pd
from datetime import datetime, timedelta
import logging
from app.core.database_connection import get_database_connection, get_redis_connection

logger = logging.getLogger(__name__)


class NewsDataManager:
    def __init__(self):
        self.engine = get_database_connection()
        self.redis_client = get_redis_connection()

    def get_query_and_params(
        self, request: SummaryRequestDTO, is_combined: bool = False
    ) -> tuple:
        """쿼리와 파라미터를 생성합니다.

        period가 7일인 경우 전체 데이터를 조회하고,
        1, 3, 5일인 경우 정확한 시간 간격으로 데이터를 조회합니다.

        Args:
            request: 요청 DTO (키워드, 언론사, 기간 포함)
            is_combined: 종합 키워드 조회 여부 (기본값: False)

        Returns:
            tuple[str, tuple]: SQL 쿼리문, 파라미터, 기준 시각
        """

        now = datetime.now()

        # 오늘 06:15으로 기준 시각 설정
        today_base = now.replace(hour=6, minute=15, second=0, microsecond=0)

        # 현재가 오늘 06:15 이전이면 어제 06:15을 기준으로 날짜 범위를 설정
        if now < today_base:
            target_date = today_base - timedelta(days=1)
        else:
            target_date = today_base

        # press 코드를 실제 press 이름으로 변환
        press_mapping = {"hk": "한국경제", "mk": "매일경제", "sed": "서울경제"}
        press_names = [press_mapping[p.value] for p in request.press]

        # IN 절을 위한 플레이스홀더(%s) 생성
        placeholders = ", ".join(["%s"] * len(press_names))

        # 일별 기사 수 결정
        articles_per_press = settings.ARTICLES_PER_DAY_MATRIX[request.period][
            len(request.press)
        ]
        logger.info(f"articles_per_press: {articles_per_press}")

        if request.period == 7:
            # 7일이면 전체 데이터 조회 (어차피 DB에는 7일치만 있음)

            # WITH 절로 임시 결과 집합을 만들어서 rank를 부여하고, article_per_press만큼만 선택
            query = f"""
                WITH RankedNews AS (
                    SELECT *,
                        ROW_NUMBER() OVER (
                            PARTITION BY press, DATE(published_date)
                            ORDER BY published_date DESC
                        ) as row_num
                    FROM news_articles
                    WHERE keyword = %s
                    AND press IN ({placeholders})
                )
                SELECT url, title, content, published_date, press, keyword, summary
                FROM RankedNews
                WHERE row_num <= {articles_per_press}
                ORDER BY published_date DESC
            """
            params = (request.keyword, *press_names)
        else:
            # 1, 3, 5일은 시간 단위로 조회

            # WITH 절로 임시 결과 집합을 만들어서 rank를 부여하고, article_per_press만큼만 선택
            base_query = f"""
                WITH RankedNews AS (
                    SELECT *,
                        ROW_NUMBER() OVER (
                            PARTITION BY press{', DATE(published_date)' if request.period > 1 else ''}
                            ORDER BY published_date DESC
                        ) as row_num
                    FROM news_articles
                    WHERE published_date >= DATE_SUB(%s, INTERVAL %s DAY)
                    AND keyword = %s
                    AND press IN ({placeholders})
                )
            """
            if is_combined:  # 종합 키워드 조회
                query = (
                    base_query
                    + """
                    SELECT url, title, content, published_date, press, keyword, summary
                    FROM RankedNews
                    WHERE row_num = 1
                    ORDER BY published_date DESC
                """
                )
            else:
                query = (
                    base_query
                    + f"""
                    SELECT url, title, content, published_date, press, keyword, summary
                    FROM RankedNews
                    WHERE row_num <= {articles_per_press}
                    ORDER BY published_date DESC
                """
                )

            params = (
                target_date,
                request.period,
                request.keyword,
                *press_names,
            )

        return query, params, target_date

    def retrieve_news_articles(
        self, request: SummaryRequestDTO, is_combined: bool = False
    ) -> List[NewsArticleDTO]:
        """DB에서 뉴스 기사를 조회합니다.

        Args:
            request: 요청 DTO (키워드, 언론사, 기간 포함)
            is_combined: 종합 키워드 조회 여부 (기본값: False)

        Returns:
            List[NewsArticleDTO]: 뉴스 기사 목록

        Raises:
            Exception: DB 조회 중 오류 발생 시
        """
        try:
            if is_combined:
                query, params, target_date = self.get_query_and_params(
                    request, is_combined=True
                )
            else:
                query, params, target_date = self.get_query_and_params(request)

            logger.info(f"request: {request}")

            df = pd.read_sql_query(
                query, self.engine, params=params, parse_dates=["published_date"]
            )

            if df.empty:
                logger.warning(
                    f"{target_date.date()} 날짜의 {request.keyword}에 대한 뉴스 기사가 없습니다."
                )
                return []

            articles = [NewsArticleDTO(**row) for row in df.to_dict("records")]

            logger.info(
                f"Retrieved {len(articles)} articles for keyword: {request.keyword}"
            )
            return articles

        except Exception as e:
            logger.error(f"DB에서 뉴스 가져오는 중 오류 발생: {str(e)}")
            raise

    def convert_articles(
        self, articles: List[NewsArticleDTO]
    ) -> List[NewsArticleSourceDTO]:
        """데이터베이스 조회 결과를 API 응답 형식으로 변환

        NewsArticleDTO의 content를 100자로 제한하고 필요한 필드만 추출하여
        NewsArticleSourceDTO 형식으로 변환합니다.

        Args:
            articles (List[NewsArticleDTO]): DB 조회로 얻은 뉴스 기사 목록

        Returns:
            List[NewsArticleSourceDTO]: 변환된 뉴스 기사 목록

        Raises:
            DataProcessingError: 데이터 변환 중 오류 발생 시
        """
        articles_dto = []
        for row in articles:
            try:
                # # row의 published_time과 published_date를 합쳐 NewsArticleSourceDTO로 변환
                articles_dto.append(
                    NewsArticleSourceDTO(
                        date=row.published_date,
                        title=row.title,
                        # # content를 100자로 제한
                        # content=(
                        #     row.content[:100] + "..."
                        #     if len(row.content) > 50
                        #     else row.content
                        # ),
                        content=row.content,
                        url=row.url,
                        press=row.press,
                    )
                )
            except Exception as e:
                logger.error(
                    f"행을 NewsArticleSourceDTO로 변환 중 오류: {str(e)}", exc_info=True
                )

        return articles_dto

    def caching_results(
        self, keyword: str, press: List[str], period: str, response: SummaryResponseDTO
    ):
        """뉴스 기사를 Redis에 캐싱합니다.

        Args:
            keyword (str): 키워드
            press (List[str]): 언론사
            period (str): 기간
            response (SummaryResponseDTO): 요약 결과 DTO

        Raises:
            Exception: 캐시 중 오류 발생 시
        """
        try:
            now = datetime.now()

            # 오늘 06:15으로 기준 시각 설정
            today_base = now.replace(hour=6, minute=15, second=0, microsecond=0)

            # 현재가 오늘 06:15 이전이면 어제 06:15을 기준으로 날짜 범위를 설정
            if now < today_base:
                target_date = today_base - timedelta(days=1)
            else:
                target_date = today_base

            if self.redis_client and response.summaries:
                key = f"news:summary:{target_date.strftime('%Y%m%d')}:{keyword}:{press}:{period}"

                response_dict = self.convert_timestamps(obj=response.model_dump())

                self.redis_client.setex(key, 60 * 60 * 24, json.dumps(response_dict))
                logger.info(f"캐시된 결과: {key}")
        except Exception as e:
            logger.error(f"캐시 중 오류 발생: {str(e)}")
            raise

    def convert_timestamps(self, obj):
        """Timestamp 객체를 문자열로 변환합니다.

        Args:
            obj: 변환할 객체

        Returns:
            str: 변환된 문자열
        """
        if isinstance(obj, dict):
            return {key: self.convert_timestamps(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self.convert_timestamps(item) for item in obj]
        elif isinstance(obj, datetime):
            return obj.isoformat()
        return obj

    def get_cached_results(
        self, keyword: str, press: List[str], period: str
    ) -> SummaryResponseDTO | None:
        """Redis에서 캐싱된 뉴스 기사를 가져옵니다.

        Args:
            keyword (str): 키워드
            press (List[str]): 언론사
            period (str): 기간

        Returns:
            SummaryResponseDTO: 캐싱된 결과 DTO
        """
        try:
            now = datetime.now()

            # 오늘 06:15으로 기준 시각 설정
            today_base = now.replace(hour=6, minute=15, second=0, microsecond=0)

            # 현재가 오늘 06:15 이전이면 어제 06:15을 기준으로 날짜 범위를 설정
            if now < today_base:
                target_date = today_base - timedelta(days=1)
            else:
                target_date = today_base

            key = f"news:summary:{target_date.strftime('%Y%m%d')}:{keyword}:{press}:{period}"
            cached_result = self.redis_client.get(key)
            if cached_result:
                return SummaryResponseDTO(**json.loads(cached_result))
            else:
                return None

        except Exception as e:
            logger.error(f"캐시된 결과 가져오는 중 오류 발생: {str(e)}")

        return SummaryResponseDTO()
