import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from py_eureka_client import eureka_client
from app.config.settings import settings

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def eureka_lifespan(app_: FastAPI):
    eureka_server_url = settings.EUREKA_URL
    app_name = settings.APP_NAME
    instance_host = settings.INSTANCE_HOST
    instance_port = settings.INSTANCE_PORT

    # Startup
    logger.info(
        f"Initializing Eureka client: {app_name} at {instance_host}:{instance_port}"
    )
    await eureka_client.init_async(
        eureka_server=eureka_server_url,
        app_name=app_name,
        instance_port=instance_port,
        instance_host=instance_host,
        instance_ip=instance_host,
    )
    logger.info("Eureka client initialized")
    yield  # 애플리케이션 실행

    # Shutdown
    logger.info("Stopping Eureka client")
    await eureka_client.stop_async()
