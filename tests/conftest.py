import asyncio
import sys

import pytest
from pytest_aiohttp.plugin import TestClient

from server.application import init_app
from server.models import User
from server.permissions import encode_token
from tests.utils import AdvertisementFactory, ClientInfo, UserFactory

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


@pytest.fixture(scope="function")
async def client_info():
    user: User = await UserFactory.create()
    auth_headers: dict = {"Authorization": f"Token {encode_token(user_id=user.id)['auth_token']}"}
    info: ClientInfo = ClientInfo(**user.as_dict, auth_headers=auth_headers, model=user)
    return info


@pytest.fixture(scope="function")
async def client(aiohttp_client: TestClient) -> TestClient:
    return await aiohttp_client(await init_app())


@pytest.fixture(scope="module")
def user_factory():
    async def factory(size: int = None, /, **kwargs):
        if kwargs.pop("raw", None):
            return UserFactory.stub(**kwargs).__dict__
        if size and size > 1:
            return await asyncio.gather(*UserFactory.create_batch(size, **kwargs))
        return await UserFactory.create(**kwargs)

    return factory


@pytest.fixture(scope="module")
def adv_factory():
    async def factory(size: int = None, /, **kwargs):
        if kwargs.pop("raw", None):
            return AdvertisementFactory.stub(**kwargs).__dict__
        if size and size > 1:
            return await asyncio.gather(*AdvertisementFactory.create_batch(size, **kwargs))
        return await AdvertisementFactory.create(**kwargs)

    return factory
