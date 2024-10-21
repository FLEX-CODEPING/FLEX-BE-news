import os
from urllib3.exceptions import InsecureRequestWarning
from urllib.parse import urlparse
import json
import requests
from bs4 import BeautifulSoup
from app.core.exceptions import CrawlingError
import logging

logger = logging.getLogger(__name__)


class ContentExtractor:
    def __init__(self):
        self.load_news_site_structures = self.load_news_site_structures()

    requests.packages.urllib3.disable_warnings(
        InsecureRequestWarning
    )  # ssl 인증 우회 경고 비활성화

    def load_news_site_structures(self):
        try:
            base_path = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            resource_path = os.path.join(
                base_path, "resources", "news_site_structures.json"
            )
            with open(resource_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            error_msg = f"뉴스 사이트 구조 불러오기 실패: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise CrawlingError(
                error_msg,
                details={
                    "resource_path": resource_path,
                    "error": str(e),
                },
            )

    async def extract_content(self, url):
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36"
        }
        news_site_structures = self.load_news_site_structures
        try:
            # 기사 HTML 획득 후 파싱
            response = requests.get(
                url, headers=headers, timeout=10
            )  # 서버 응답 지연 대응용 10초 타임아웃 설정
            soup = BeautifulSoup(response.content, "html.parser")

            # 도메인에 따른 사이트 구조 정보 가져오기
            domain = urlparse(url).netloc
            site_structure = None
            for site_name, site_info in news_site_structures.items():
                if isinstance(site_info["domain"], list):
                    if domain in site_info["domain"]:
                        site_structure = site_info
                        break
                elif site_info["domain"] in domain:
                    site_structure = site_info
                    break

            print(f"Debug - URL: {url}")
            print(f"Debug - Domain: {domain}")
            print(f"Debug - Site structure: {site_structure}")

            if site_structure:
                if isinstance(site_structure["selectors"], dict):
                    # 여러 도메인을 가진 사이트 처리 (예: 매일경제, 서울경제)
                    if domain in ["m.sedaily.com", "www.sedaily.com"]:
                        if domain == "m.sedaily.com":
                            path = urlparse(url).path
                            content_selector = (
                                site_structure["selectors"]["m.sedaily.com"][
                                    "NewsViewAmp"
                                ]
                                if "NewsViewAmp" in path
                                else site_structure["selectors"]["m.sedaily.com"][
                                    "NewsView"
                                ]
                            )
                        else:  # www.sedaily.com
                            content_selector = site_structure["selectors"][
                                "www.sedaily.com"
                            ]
                    else:
                        content_selector = site_structure["selectors"].get(domain)
                        if not content_selector:
                            # 정확한 매치가 없을 경우, 부분 매치 시도
                            for site_domain, selector in site_structure[
                                "selectors"
                            ].items():
                                if site_domain in domain:
                                    content_selector = selector
                                    break
                else:
                    # 단일 선택자를 가진 사이트 처리
                    content_selector = site_structure["selectors"]
                if content_selector:
                    print(f"Debug - Content selector: {content_selector}")
                    content_element = soup.select_one(content_selector)
                    if content_element:
                        content = content_element.get_text(strip=True)
                        print(
                            f"Debug - Extracted content (first 200 chars): {content[:200]}"
                        )
                        return content
                    else:
                        print(
                            f"Debug - Content selector '{content_selector}' not found"
                        )
                else:
                    print("Debug - No suitable selector found for this domain")
            else:
                print(f"Debug - No structure defined for domain: {domain}")

            # 폴백: 기본 콘텐츠 추출 로직
            fallback_content = soup.get_text(strip=True)
            print(
                f"Debug - Fallback content (first 200 characters): {fallback_content[:200]}"
            )
            return fallback_content
        except Exception as e:
            error_msg = f"콘텐츠 추출 실패 URL: {url}, 에러: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise CrawlingError(
                error_msg,
                details={
                    "url": url,
                    "error": str(e),
                },
            )
