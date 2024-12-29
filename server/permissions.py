import base64
import binascii
import functools
from datetime import datetime, timedelta, timezone

import jwt
from aiohttp import web

from server.config import SECRET_KEY
from server.crud import DataBase
from server.exceptions import ForbiddenError, UnauthorizedError
from server.models import User
from server.security import check_password


def encode_token(user_id: int) -> dict:
    expiration_time = datetime.now(tz=timezone.utc) + timedelta(minutes=60)
    auth_token: str = jwt.encode(
        {"user_id": user_id, "exp": expiration_time},
        SECRET_KEY,
        algorithm="HS256",
    )
    return {"auth_token": auth_token}


def decode_token(token: str) -> dict:
    """Функция проверки подлинности предоставленного токена.

    Возвращает зашифрованные данные - словарь с идентификатором пользователя.
    """
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    except (jwt.exceptions.DecodeError, jwt.exceptions.ExpiredSignatureError):
        raise UnauthorizedError("The provided authorization token is invalid")


def get_auth_info(request: web.Request, required_auth_type: str = "Token"):
    if (auth_info := request.headers.get("Authorization")) and required_auth_type in auth_info:
        auth_type, auth_data = auth_info.split(maxsplit=1)
        if required_auth_type == auth_type == "Basic":
            try:
                auth_data = (
                    base64.b64decode(auth_data.encode("ascii"), validate=True)
                    .decode()
                    .replace(":", " ")
                )
            except binascii.Error:
                pass
        return auth_data


async def check_basic_authentication(request: web.Request) -> bool:
    if auth_data := get_auth_info(request=request, required_auth_type="Basic"):
        username, password = auth_data.split()
        dbase: DataBase = DataBase(model=User, session=request.session)
        user: User = await dbase.get_user_by_name(username=username)
        if check_password(password=password, hashed_password=user.password):
            return user
        raise UnauthorizedError("The provided password is invalid")
    raise UnauthorizedError("Basic authorization credentials were not provided")


async def check_token_authentication(request: web.Request):
    if token := get_auth_info(request=request):
        user_info: dict = decode_token(token=token)
        dbase: DataBase = DataBase(model=User, session=request.session)
        user: User = await dbase.get_obj(id=user_info["user_id"])
        return user


async def check_permissions_for_user(view_obj, **kw):
    if view_obj.request.is_authenticated:
        if kw.get("is_owner") and view_obj.request.method in ["PATCH", "DELETE"]:
            if view_obj.id_from_url == view_obj.request.user.id:
                return
            raise ForbiddenError("You can only make changes to your own profile")
    else:
        raise UnauthorizedError("Authorization credentials were not provided")


async def check_permissions_for_advertisement(view_obj, **kw):
    if view_obj.request.is_authenticated and view_obj.request.method in ["POST", "PATCH", "DELETE"]:
        if kw.get("is_owner") and view_obj.request.method in ["PATCH", "DELETE"]:
            for adv in await view_obj.request.user.awaitable_attrs.advertisements:
                if adv.id == view_obj.id_from_url:
                    return
            raise ForbiddenError("You can only make changes to your own advertisements")
    else:
        raise UnauthorizedError("Authorization credentials were not provided")


def authentication(**kw):
    def decorator(old_method):
        permission_handler = {
            "UserView": check_permissions_for_user,
            "AdvertisementView": check_permissions_for_advertisement,
        }

        @functools.wraps(old_method)
        async def new_method(view_obj, *args, **kwargs):
            await permission_handler[view_obj.__class__.__name__](view_obj=view_obj, **kw)
            response = await old_method(view_obj, *args, **kwargs)
            return response

        return new_method

    return decorator
