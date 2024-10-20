from googlenewsdecoder import new_decoderv1
from app.core.exceptions import CrawlingError
import logging

logger = logging.getLogger(__name__)


class URLDecoder:
    def __init__(self):
        pass

    async def decode_google_news_url(self, google_news_url: str):
        try:
            decoded_result = new_decoderv1(google_news_url)
            if decoded_result.get("status"):
                return decoded_result["decoded_url"]
            else:
                print("Error decoding URL:", decoded_result["message"])
                return google_news_url
        except Exception as e:
            error_msg = f"URL 디코딩 실패: {google_news_url}, 에러: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise CrawlingError(
                error_msg,
                details={
                    "url": google_news_url,
                    "error": str(e),
                },
            )
