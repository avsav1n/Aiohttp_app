from __future__ import annotations

from aiohttp import web

from server.crud import DataBase
from server.exceptions import MethodNotAllowedError

# from server.middlewares import routes
from server.models import ORM_MODELS, Advertisement, User
from server.permissions import authentication, check_basic_authentication, encode_token
from server.schema import (
    CreateAdvertisement,
    CreateUser,
    UpdateAdvertisement,
    UpdateUser,
    validate,
)

routes = web.RouteTableDef()


class BaseView(web.View):
    model = None

    def __init__(self, request: web.Request):
        if self.model is None:
            raise TypeError(
                f"{self.__class__.__name__}'s subclasses must override class attribute 'model'"
            )
        self.check_http_method(request=request)
        self.dbase = DataBase(model=self.model, session=request.session)
        super().__init__(request)

    @property
    def id_from_url(self) -> int:
        return int(self.request.match_info["id"])

    @classmethod
    def check_http_method(cls, request: web.Request) -> None:
        if request.match_info and request.method in ["GET", "PATCH", "DELETE"]:
            return
        if not request.match_info and request.method in ["GET", "POST"]:
            return
        raise MethodNotAllowedError(
            f"HTTP-method '{request.method}' on path '{request.path}' not allowed"
        )

    async def get_list(self) -> web.Response:
        objects: list[ORM_MODELS] = await self.dbase.get_objects()
        data: list[dict] = [obj.as_dict for obj in objects]
        return web.json_response(data=data, status=200)

    async def get_detail(self) -> web.Response:
        obj: ORM_MODELS = await self.dbase.get_obj(id=self.id_from_url)
        return web.json_response(data=obj.as_dict, status=200)

    async def delete(self) -> web.Response:
        obj_for_delete: ORM_MODELS = await self.dbase.get_obj(id=self.id_from_url)
        await self.dbase.delete_obj(obj=obj_for_delete)
        return web.json_response(status=204)


@routes.view(r"/user")
@routes.view(r"/user/{id:\d+}")
class UserView(BaseView):
    model = User

    async def get(self) -> web.Response:
        return await self.get_detail() if self.request.match_info else await super().get_list()

    async def get_detail(self) -> web.Response:
        if self.request.is_authenticated and self.id_from_url == self.request.user.id:
            return web.json_response(data=self.request.user.as_dict, status=200)
        return await super().get_detail()

    async def post(self) -> web.Response:
        input_data: dict = await self.request.json()
        validated_data: dict = validate(CreateUser, input_data)
        created_obj: User = await self.dbase.create_obj(data=validated_data)
        return web.json_response(data=created_obj.as_dict, status=201)

    @authentication(is_owner=True)
    async def patch(self) -> web.Response:
        obj_for_update: User = await self.dbase.get_obj(self.id_from_url)
        input_data: dict = await self.request.json()
        validated_data: dict = validate(UpdateUser, input_data)
        updated_obj: User = await self.dbase.update_obj(obj=obj_for_update, data=validated_data)
        return web.json_response(data=updated_obj.as_dict, status=200)

    @authentication(is_owner=True)
    async def delete(self) -> web.Response:
        return await super().delete()


@routes.view(r"/advertisement")
@routes.view(r"/advertisement/{id:\d+}")
class AdvertisementView(BaseView):
    model = Advertisement

    async def get(self) -> web.Response:
        return await super().get_detail() if self.request.match_info else await super().get_list()

    @authentication(is_auth=True)
    async def post(self) -> web.Response:
        input_data: dict = await self.request.json()
        validated_data: dict = validate(CreateAdvertisement, input_data)
        validated_data.update({"user": self.request.user})
        created_obj: Advertisement = await self.dbase.create_obj(data=validated_data)
        return web.json_response(data=created_obj.as_dict, status=201)

    @authentication(is_owner=True)
    async def patch(self) -> web.Response:
        obj_for_update: Advertisement = await self.dbase.get_obj(self.id_from_url)
        input_data: dict = await self.request.json()
        validated_data: dict = validate(UpdateAdvertisement, input_data)
        updated_obj: Advertisement = await self.dbase.update_obj(
            obj=obj_for_update, data=validated_data
        )
        return web.json_response(data=updated_obj.as_dict, status=200)

    @authentication(is_owner=True)
    async def delete(self) -> web.Response:
        return await super().delete()


@routes.post(r"/login")
async def login(request: web.Request) -> web.Response:
    if user := await check_basic_authentication(request=request):
        token_info: dict = encode_token(user_id=user.id)
        return web.json_response(data=token_info, status=201)
