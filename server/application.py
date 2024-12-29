from aiohttp import web

from server.middlewares import auth_middleware, orm_ctx, session_middleware
from server.views import routes


async def init_app():
    app = web.Application()
    app.add_routes(routes=routes)
    app.cleanup_ctx.append(orm_ctx)
    app.middlewares.extend([session_middleware, auth_middleware])

    return app
