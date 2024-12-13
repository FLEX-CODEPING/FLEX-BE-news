import json
from sqlalchemy import create_engine
from app.config.settings import settings
from redis import Redis


def get_database_connection():
    try:
        connection_info = f"mysql+pymysql://{settings.DATABASE_USERNAME}:{settings.DATABASE_PASSWORD}@{settings.DATABASE_HOST}:{settings.DATABASE_PORT}/{settings.DATABASE_SCHEMA}"
        if not connection_info:
            raise ValueError("데이터 베이스 연결정보가 없습니다.")

        engine = create_engine(connection_info)
        print("MySQL 데이터베이스에 성공적으로 연결되었습니다.")
        return engine
    except Exception as e:
        print(f"데이터베이스 연결 오류: {e}")
        return None


def get_redis_connection():
    try:
        redis_client = Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            password=settings.REDIS_PASSWORD,
            db=settings.REDIS_DB,
            decode_responses=True,
        )
        redis_client.ping()
        print("Redis에 성공적으로 연결되었습니다.")
        return redis_client
    except Exception as e:
        print(f"Redis 연결 오류: {str(e)}")
        return None


def get_cached_summary(key: str) -> dict | None:
    redis_client = get_redis_connection()
    if not redis_client:
        return None
    result = redis_client.get(key)
    return json.loads(result) if result else None
