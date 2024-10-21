class BaseCustomException(Exception):
    """모든 커스텀 예외의 기본 클래스"""

    def __init__(self, message: str, error_code: str = None):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)


class SummaryError(BaseCustomException):
    """요약 과정에서 발생하는 오류를 위한 예외"""

    def __init__(
        self, message: str, error_code: str = "SUMMARY_ERROR", details: dict = None
    ):
        super().__init__(message, error_code)
        self.details = details or {}

    def __str__(self):
        return f"{self.error_code}: {self.message} - Details: {self.details}"


class CrawlingError(BaseCustomException):
    """크롤링 과정에서 발생하는 오류를 위한 예외"""

    def __init__(
        self, message: str, error_code: str = "CRAWLING_ERROR", details: dict = None
    ):
        super().__init__(message, error_code)
        self.details = details or {}

    def __str__(self):
        return f"{self.error_code}: {self.message} - Details: {self.details}"
