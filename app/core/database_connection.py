import os
from dotenv import load_dotenv
from sqlalchemy import create_engine

# .env 파일 로드
load_dotenv()

# 환경 변수 가져오기
DATABASE_USER = os.getenv("DATABASE_USERNAME")
DATABASE_PASSWORD = os.getenv("DATABASE_PASSWORD")
DATABASE_HOST = os.getenv("DATABASE_HOST")
DATABASE_PORT = os.getenv("DATABASE_PORT")
DATABASE_SCHEMA = os.getenv("DATABASE_SCHEMA")


def get_database_connection():
    try:
        connection_info = f"mysql+pymysql://{DATABASE_USER}:{DATABASE_PASSWORD}@{DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_SCHEMA}"
        if not connection_info:
            raise ValueError("데이터 베이스 연결정보가 없습니다.")

        engine = create_engine(connection_info)
        print("MySQL 데이터베이스에 성공적으로 연결되었습니다.")
        return engine
    except Exception as e:
        print(f"데이터베이스 연결 오류: {e}")
        return None
