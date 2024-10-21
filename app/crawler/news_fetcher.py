from urllib.parse import urlparse
import feedparser
from typing import List, Dict
from datetime import datetime
from app.models.dtos import PressDTO
from app.crawler.url_decoder import URLDecoder
from app.crawler.content_extractor import ContentExtractor
from app.core.exceptions import CrawlingError
import logging

logger = logging.getLogger(__name__)


class NewsFetcher:
    def __init__(self):
        self.url_decoder = URLDecoder()
        self.content_extractor = ContentExtractor()

    async def fetch_news(
        self,
        period: int,
        keyword: str,
        press_list: List[PressDTO],
        articles_per_keyword: int = 2,
        max_total_articles: int = 6,
    ) -> List[Dict]:
        all_articles = []
        logger.info(f"press_list: {press_list}")
        for press in press_list:
            if len(all_articles) >= max_total_articles:
                break
            try:
                logger.info(f"Fetching news from {press.name}, domain: {press.domain}")
                articles = await self._fetch_from_press(
                    period, keyword, press, articles_per_keyword, max_total_articles
                )
                logger.info(f"Fetched {len(articles)} articles from {press.name}")
                all_articles.extend(articles)
            except Exception as e:
                logger.warning(f"Failed to fetch news from {press.name}: {str(e)}")

        if not all_articles:
            error_msg = (
                f"No articles fetched for keyword: {keyword}, press_list: {press_list}"
            )
            logger.error(error_msg)
            raise CrawlingError(
                error_msg,
                details={
                    "period": period,
                    "keyword": keyword,
                    "press_count": len(press_list),
                },
            )

        return all_articles

    async def _fetch_from_press(
        self,
        period: int,
        keyword: str,
        press: PressDTO,
        articles_per_keyword: int,
        max_total_articles: int,
    ) -> List[Dict]:
        articles = []
        rss_url = f"https://news.google.com/rss/search?q={keyword}%20site%3A{press.domain}%20when%3A{period}d&hl=ko&gl=KR&ceid=KR:ko"

        try:
            feed = feedparser.parse(rss_url)

            for entry in feed.entries:
                if (
                    len(articles) >= articles_per_keyword
                    or len(articles) >= max_total_articles
                ):
                    break
                try:
                    decoded_url = await self.url_decoder.decode_google_news_url(
                        entry.link
                    )
                    entry_domain = urlparse(decoded_url).netloc
                    logger.info(
                        f"Decoded URL: {decoded_url}, Entry domain: {entry_domain}"
                    )

                    if press.domain not in entry_domain:
                        logger.info(f"Skipping article from {entry_domain}")
                        continue

                    published = datetime.strptime(
                        entry.published, "%a, %d %b %Y %H:%M:%S %Z"
                    )
                    content = await self.content_extractor.extract_content(decoded_url)

                    article = {
                        "title": entry.title,
                        "source": entry.source.title,
                        "published_date": published.strftime("%Y-%m-%d"),
                        "published_time": published.strftime("%H:%M"),
                        "url": decoded_url,
                        "content": content,
                        "keywords": keyword,
                    }
                    articles.append(article)
                except Exception as e:
                    logger.warning(
                        f"Failed to process article from {press.name}: {str(e)}"
                    )

            return articles
        except Exception as e:
            logger.error(
                f"Failed to fetch news from {press.name}: {str(e)}", exc_info=True
            )
            raise CrawlingError(
                f"Failed to fetch news from {press.name}",
                details={"press": press.name, "keyword": keyword, "period": period},
            )
