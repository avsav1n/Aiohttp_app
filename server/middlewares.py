from aiohttp import web
from sqlalchemy.ext.asyncio import AsyncSession

from server.models import Session, User, close_orm
from server.permissions import check_token_authentication


async def orm_ctx(app: web.Application):
    """Контекст aiohttp сервера."""
    yield
    await close_orm()


@web.middleware
async def session_middleware(request: web.Request, handler):
    """Middleware ORM-сессии."""
    session: AsyncSession = Session()
    request.session = session
    try:
        response: web.Response = await handler(request)
    finally:
        await request.session.close()
    return response


@web.middleware
async def auth_middleware(request: web.Request, handler):
    """Middleware аутентификации."""
    user: User = await check_token_authentication(request=request)
    if user:
        request.user = user
        request.is_authenticated = True
    else:
        request.is_authenticated = False
    response: web.Response = await handler(request)
    return response
