import json

from aiohttp import web


class BaseError(web.HTTPError):
    def __init__(self, description: dict | list | str):
        self.description = description
        super().__init__(
            text=json.dumps({"error": description}),
            content_type="application/json",
        )


class NotFoundError(BaseError):
    status_code = 404


class ConflictError(BaseError):
    status_code = 409


class UnauthorizedError(BaseError):
    status_code = 401


class BadRequestError(BaseError):
    status_code = 400


class ForbiddenError(BaseError):
    status_code = 403


class MethodNotAllowedError(BaseError):
    status_code = 405
