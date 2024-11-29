FROM python:3.10-slim

WORKDIR /app

# Docker 캐시를 활용하기 위해 먼저 requirements 복사
COPY requirements.txt .

# Python 의존성 설치
RUN pip install --no-cache-dir -r requirements.txt

# 나머지 복사
COPY . .

# 앱 실행 시 사용할 포트
EXPOSE 8001

# 앱 실행 명령어
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]