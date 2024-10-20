from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    openai_api_key: str
    naver_client_id: str
    naver_client_secret: str

    class Config:
        env_file = ".env"


settings = Settings()
