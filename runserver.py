from aiohttp import web

from server.application import init_app

if __name__ == "__main__":
    web.run_app(app=init_app())
