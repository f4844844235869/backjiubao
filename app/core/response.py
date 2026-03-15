import uuid
from typing import Any, Generic, TypeVar

from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from starlette import status

T = TypeVar("T")


class ApiErrorDetail(BaseModel):
    field: str | None = Field(default=None, description="错误字段")
    reason: str = Field(description="错误原因")


class ApiResponse(BaseModel, Generic[T]):
    code: str = Field(description="业务响应码")
    message: str = Field(description="响应消息")
    data: T | None = Field(default=None, description="响应数据")
    trace_id: str = Field(description="请求追踪 ID")


class PageData(BaseModel, Generic[T]):
    items: list[T] = Field(description="分页数据")
    total: int = Field(description="总数")


class AppException(HTTPException):
    def __init__(
        self,
        *,
        status_code: int,
        code: str,
        message: str,
        errors: list[ApiErrorDetail] | None = None,
    ) -> None:
        super().__init__(
            status_code=status_code,
            detail={
                "code": code,
                "message": message,
                "errors": [error.model_dump() for error in (errors or [])],
            },
        )


def translate_validation_reason(reason: str) -> str:
    """将常见的校验错误原因翻译成中文，减少前端直接展示英文文案。"""

    translations = {
        "Field required": "字段不能为空",
        "Input should be a valid UUID": "请输入合法的 UUID",
        "Input should be a valid string": "请输入合法的字符串",
        "Input should be a valid integer": "请输入合法的整数",
        "Input should be a valid boolean": "请输入合法的布尔值",
        "Input should be a valid list": "请输入合法的列表",
        "Input should be a valid dictionary": "请输入合法的对象",
        "Input should be a valid email address": "请输入合法的邮箱地址",
    }
    return translations.get(reason, reason)


def get_trace_id(request: Request) -> str:
    trace_id = getattr(request.state, "trace_id", None)
    if trace_id:
        return str(trace_id)
    return str(uuid.uuid4())


def success_response(
    request: Request,
    *,
    data: Any = None,
    message: str = "请求成功",
    code: str = "SUCCESS",
    status_code: int = status.HTTP_200_OK,
) -> JSONResponse:
    body = ApiResponse[Any](
        code=code,
        message=message,
        data=data,
        trace_id=get_trace_id(request),
    )
    response = JSONResponse(status_code=status_code, content=body.model_dump(mode="json"))
    response.headers["X-Trace-Id"] = body.trace_id
    return response


def raise_api_error(
    *,
    status_code: int,
    code: str,
    message: str,
    errors: list[ApiErrorDetail] | None = None,
) -> None:
    raise AppException(
        status_code=status_code,
        code=code,
        message=message,
        errors=errors,
    )


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    detail = exc.detail if isinstance(exc.detail, dict) else {}
    body = ApiResponse[dict[str, Any] | None](
        code=detail.get("code", "REQUEST_ERROR"),
        message=detail.get("message", "请求失败"),
        data={"errors": detail.get("errors", [])} if detail.get("errors") else None,
        trace_id=get_trace_id(request),
    )
    response = JSONResponse(status_code=exc.status_code, content=body.model_dump(mode="json"))
    response.headers["X-Trace-Id"] = body.trace_id
    return response


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    detail = exc.detail
    if isinstance(detail, dict):
        code = detail.get("code", "HTTP_ERROR")
        message = detail.get("message", "请求失败")
        errors = detail.get("errors", [])
    else:
        code = "HTTP_ERROR"
        message = str(detail)
        errors = []
    body = ApiResponse[dict[str, Any] | None](
        code=code,
        message=message,
        data={"errors": errors} if errors else None,
        trace_id=get_trace_id(request),
    )
    response = JSONResponse(status_code=exc.status_code, content=body.model_dump(mode="json"))
    response.headers["X-Trace-Id"] = body.trace_id
    return response


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    errors = [
        ApiErrorDetail(
            field=".".join(str(part) for part in error["loc"]),
            reason=translate_validation_reason(error["msg"]),
        )
        for error in exc.errors()
    ]
    body = ApiResponse[dict[str, Any]](
        code="VALIDATION_ERROR",
        message="请求参数校验失败",
        data={"errors": [error.model_dump() for error in errors]},
        trace_id=get_trace_id(request),
    )
    response = JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=body.model_dump(mode="json"),
    )
    response.headers["X-Trace-Id"] = body.trace_id
    return response


async def unhandled_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    _ = exc
    body = ApiResponse[None](
        code="INTERNAL_SERVER_ERROR",
        message="服务器内部异常",
        data=None,
        trace_id=get_trace_id(request),
    )
    response = JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=body.model_dump(mode="json"),
    )
    response.headers["X-Trace-Id"] = body.trace_id
    return response
