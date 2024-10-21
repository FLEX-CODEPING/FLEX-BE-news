from datetime import datetime
import pandas as pd
from typing import List
import os
from app.crawler.news_fetcher import NewsFetcher
from app.models.dtos import PressDTO, NewsArticleDTO
from app.core.exceptions import CrawlingError
import logging

logger = logging.getLogger(__name__)


class NewsCrawler:
    def __init__(self):
        self.news_fetcher = NewsFetcher()

    async def crawl_and_save(
        self,
        period: int,
        keyword: str,
        press_list: List[PressDTO],
    ):
        # articles = await self.crawl_news(period, keyword, press)
        try:
            logger.info(
                f"크롤링 시작: {period}일간의 {keyword} 키워드 뉴스 수집, 언론사: {press_list}",
                exc_info=True,
            )
            articles = await self.news_fetcher.fetch_news(period, keyword, press_list)
            df = pd.DataFrame(articles)

            if df.empty:
                print("No articles found")
                return

            # DataFrame의 각 행을 NewsArticleDTO로 변환
            article_dtos = []
            # NewsArticleDTO(**row) for row in df.to_dict(orient="records")
            for row in df.to_dict(orient="records"):
                try:
                    # published_time 필드를 datetime 형식으로 변환
                    if "published_time" in row:
                        row["published_time"] = datetime.strptime(
                            row["published_time"], "%H:%M"
                        )
                    article_dtos.append(NewsArticleDTO(**row))
                except Exception as e:
                    logger.error(
                        f"행을 NewsArticleDTO로 변환 중 오류: {str(e)}", exc_info=True
                    )

            # 파일 이름 생성
            date_str = datetime.now().strftime("%Y%m%d_%H%M%S")

            # keywords_str = "".join(keyword)[:30]  # 키워드가 너무 길어지지 않도록 제한
            file_name = f"news_crawl_{date_str}_{keyword}.csv"

            # resources 디렉토리 경로 생성
            base_path = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            resources_dir = os.path.join(base_path, "resources", "crawl_results")

            # resources 디렉토리가 없으면 생성
            os.makedirs(resources_dir, exist_ok=True)

            # CSV 파일 저장 경로 설정
            csv_path = os.path.join(resources_dir, file_name)

            # CSV 파일로 저장
            df.to_csv(csv_path, index=False, encoding="utf-8-sig")

            logger.info(f"File saved: {csv_path}")
            return article_dtos

        except Exception as e:
            error_msg = f"크롤링 및 저장 실패: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise CrawlingError(
                error_msg,
                details={
                    "period": period,
                    "keyword": keyword,
                    "press_count": len(press_list),
                },
            )
