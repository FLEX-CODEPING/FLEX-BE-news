from typing import Dict, List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Eureka settings
    EUREKA_URL: str
    APP_NAME: str
    INSTANCE_HOST: str
    INSTANCE_PORT: str
    
    openai_api_key: str

    # Database settings
    database_host: str
    database_port: str
    database_username: str
    database_password: str
    database_schema: str

    # News settings
    NEWS_KEYWORD: List[str] = [
        "국내주식",
        "해외주식",
        "크립토",
        "ETF",
        "정치",
        "경제",
        "환율",
        "부동산",
        "지수",
    ]

    ARTICLES_PER_DAY_MATRIX: Dict[int, Dict[int, int]] = {
        # period: {press_count: articles_per_press}
        1: {1: 6, 2: 3, 3: 2},  # 1일: 1개사=6개, 2개사=3개씩, 3개사=2개씩
        3: {1: 4, 2: 2, 3: 1},  # 3일: 1개사=4개, 2개사=2개씩, 3개사=1개씩
        5: {1: 2, 2: 1, 3: 1},  # 5일: 1개사=2개, 2개사=1개씩, 3개사=1개씩
        7: {1: 1, 2: 1, 3: 1},  # 7일: 모든 경우 1개씩
    }

    class Config:
        env_file = ".env"


settings = Settings()
