#这是一个检查请求本身是否合法的中间件
from collections.abc import Awaitable, Callable

from fastapi import Request, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, Response

from app.security.schemas import PermissionLevel, ResourceType
from app.security.service import permission_service


class PermissionMiddleware(BaseHTTPMiddleware):
    """Checks resource access for requests that declare permission headers."""

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        resource_type = request.headers.get("X-Resource-Type")
        resource_id = request.headers.get("X-Resource-Id")
        required_level = request.headers.get("X-Required-Permission")
        user_id = request.headers.get("X-User-Id")

        #无该请求用户
        if resource_type and resource_id and required_level:
            if not user_id:
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "missing X-User-Id header"},
                )
        #该请求不成立
            try:
                decision = permission_service.check_permission(
                    user_id=int(user_id),
                    resource_type=ResourceType(resource_type),
                    resource_id=int(resource_id),
                    required_level=PermissionLevel(required_level),
                    actor_id=int(user_id),
                )
            except ValueError as exc:
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={"detail": str(exc)},
                )

            if not decision.allowed:
                return JSONResponse(
                    status_code=status.HTTP_403_FORBIDDEN,
                    content={"detail": decision.reason},
                )

            request.state.permission = decision

        return await call_next(request)
