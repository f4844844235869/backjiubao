from pathlib import Path
from uuid import uuid4

import sentry_sdk
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.routing import APIRoute
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.cors import CORSMiddleware

from app.api.main import api_router
from app.core.config import settings
from app.core.response import (
    AppException,
    app_exception_handler,
    http_exception_handler,
    unhandled_exception_handler,
    validation_exception_handler,
)


def custom_generate_unique_id(route: APIRoute) -> str:
    return f"{route.tags[0]}-{route.name}"


if settings.SENTRY_DSN and settings.ENVIRONMENT != "local":
    sentry_sdk.init(dsn=str(settings.SENTRY_DSN), enable_tracing=True)

static_dir = Path(__file__).resolve().parent / "static"

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="酒吧经营系统后端接口文档，包含认证、用户、员工、门店、组织与权限管理能力。",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    generate_unique_id_function=custom_generate_unique_id,
    openapi_tags=[
        {"name": "Auth", "description": "登录、当前用户、小程序认证与门店切换接口"},
        {"name": "Users", "description": "后台用户管理与个人信息接口"},
        {"name": "Employees", "description": "员工入职、离职、档案与任职记录接口"},
        {"name": "Stores", "description": "门店查询、维护与删除接口"},
        {"name": "Organization", "description": "组织节点与用户组织绑定接口"},
        {"name": "IAM", "description": "角色、权限、数据范围与授权摘要接口"},
    ],
)


@app.middleware("http")
async def add_trace_id(request: Request, call_next):
    request.state.trace_id = request.headers.get("X-Trace-Id") or str(uuid4())
    response = await call_next(request)
    response.headers["X-Trace-Id"] = request.state.trace_id
    return response

# Set all CORS enabled origins
if settings.all_cors_origins:
    allow_all_origins = "*" in settings.all_cors_origins
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.all_cors_origins,
        allow_credentials=not allow_all_origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.mount("/static", StaticFiles(directory=static_dir), name="static")
app.include_router(api_router, prefix=settings.API_V1_STR)
app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)
