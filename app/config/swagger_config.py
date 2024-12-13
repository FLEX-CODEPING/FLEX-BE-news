from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi


def custom_openapi(app: FastAPI):
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="FLEX 뉴스 요약 API",
        version="1.0",
        routes=app.routes,
    )
    openapi_schema["components"]["securitySchemes"] = {
        "bearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "in": "header",
            "name": "Authorization",
        }
    }
    openapi_schema["security"] = [{"bearerAuth": []}]

    # 각 API의 예시 응답값 설정
    paths = openapi_schema.get("paths", {})
    if "/api/news-summary/" in paths:
        paths["/api/news-summary/"]["get"]["responses"]["200"]["content"][
            "application/json"
        ]["example"] = {
            "isSuccess": True,
            "code": "COMMON200",
            "message": "성공",
            "result": {
                "summaries": [{"title": "제목", "content": "내용"}],
                "sources": [
                    {
                        "date": "2024-11-19T16:21:33.952Z",
                        "title": "원본 제목",
                        "content": "원본 내용",
                        "url": "http://example.com",
                    }
                ],
            },
        }
        paths["/api/news-summary/"]["get"]["responses"].update(
            {
                "500": {
                    "description": "서버 오류",
                    "content": {
                        "application/json": {
                            "example": {
                                "isSuccess": False,
                                "code": "COMMON500",
                                "message": "서버 오류",
                            }
                        }
                    },
                }
            }
        )
    if "/api/news-summary/todaynews" in paths:
        paths["/api/news-summary/todaynews"]["get"]["responses"]["200"]["content"][
            "application/json"
        ]["example"] = {
            "isSuccess": True,
            "code": "COMMON200",
            "message": "성공",
            "result": {
                "sources": [
                    {
                        "date": "2024-11-19T16:21:33.952Z",
                        "title": "제목",
                        "content": "내용",
                        "url": "http://example.com",
                    }
                ]
            },
        }
        paths["/api/news-summary/todaynews"]["get"]["responses"].update(
            {
                "500": {
                    "description": "서버 오류",
                    "content": {
                        "application/json": {
                            "example": {
                                "isSuccess": False,
                                "code": "COMMON500",
                                "message": "서버 오류",
                            }
                        }
                    },
                }
            }
        )

    app.openapi_schema = openapi_schema
    return app.openapi_schema


def setup_swagger(app: FastAPI):
    app.openapi = lambda: custom_openapi(app)
