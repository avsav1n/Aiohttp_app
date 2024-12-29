import re

from aiohttp import BasicAuth
from pytest_aiohttp.plugin import TestClient

from server.models import User
from server.security import hash_password
from tests.utils import ClientInfo


def url(id: int = None):
    base_url = "/user"
    if not id:
        return base_url
    return f"{base_url}/{id}"


async def test_get_list_success(user_factory, client: TestClient):
    users: list = await user_factory(2)

    response = await client.get(url())
    response_json: list = await response.json()

    assert response.status == 200
    assert isinstance(response_json, list)
    for user in users:
        assert user.as_dict in response_json


async def test_get_detail_success(client: TestClient, client_info: ClientInfo):
    response = await client.get(url(client_info.id))
    response_json: dict = await response.json()

    assert response.status == 200
    assert client_info.model.as_dict == response_json


async def test_post_success(user_factory, client: TestClient):
    user_data: dict = await user_factory(raw=True)

    response = await client.post(url(), json=user_data)
    response_json: dict = await response.json()

    assert response.status == 201
    assert user_data["username"] == response_json["username"]


async def test_post_fail_simple_password(user_factory, client: TestClient):
    user_data: dict = await user_factory(raw=True, password="simple password")

    response = await client.post(url(), json=user_data)
    response_json: dict = await response.json()

    assert response.status == 400
    assert response_json.get("error")


async def test_post_fail_no_name(user_factory, client: TestClient):
    user_data: dict = await user_factory(raw=True)
    user_data.pop("username")

    response = await client.post(url(), json=user_data)
    response_json: dict = await response.json()

    assert response.status == 400
    assert response_json.get("error")


async def test_post_fail_existed_name(user_factory, client: TestClient, client_info: ClientInfo):
    user_data: dict = await user_factory(raw=True, username=client_info.username)

    response = await client.post(url(), json=user_data)
    response_json: dict = await response.json()

    assert response.status == 409
    assert response_json.get("error")


async def test_post_fail_no_data(client: TestClient):
    response = await client.post(url(), json={})
    response_json: dict = await response.json()

    assert response.status == 400
    assert response_json.get("error")
    assert isinstance(response_json["error"], list)


async def test_patch_fail_unauthorized(client: TestClient, client_info: ClientInfo):
    response = await client.patch(url(client_info.id), json={"password": "QWErty123"})
    response_json: dict = await response.json()

    assert response.status == 401
    assert response_json.get("error")


async def test_patch_authorized_owner_success(client: TestClient, client_info: ClientInfo):
    response = await client.patch(
        url(client_info.id),
        json={"password": "QWErty123"},
        headers=client_info.auth_headers,
    )
    response_json: dict = await response.json()

    assert response.status == 200
    assert client_info.model.as_dict == response_json


async def test_patch_authorized_fail_not_owner(
    user_factory, client: TestClient, client_info: ClientInfo
):
    user: User = await user_factory()

    response = await client.patch(
        url(user.id),
        json={"password": "QWErty123"},
        headers=client_info.auth_headers,
    )
    response_json: dict = await response.json()

    assert response.status == 403
    assert response_json.get("error")


async def test_delete_fail_unauthorized(user_factory, client: TestClient):
    user: User = await user_factory()

    response = await client.delete(url(user.id))
    response_json: dict = await response.json()

    assert response.status == 401
    assert response_json.get("error")


async def test_delete_authorized_fail_not_owner(
    user_factory, client: TestClient, client_info: ClientInfo
):
    user: User = await user_factory()

    response = await client.delete(url(user.id), headers=client_info.auth_headers)
    response_json: dict = await response.json()

    assert response.status == 403
    assert response_json.get("error")


async def test_delete_authorized_owner_success(client: TestClient, client_info: ClientInfo):
    response = await client.delete(url(client_info.id), headers=client_info.auth_headers)

    assert response.status == 204


async def test_login_success(user_factory, client: TestClient):
    user_data: dict = await user_factory(raw=True)
    await user_factory(**hash_password(user_data.copy()))
    auth = BasicAuth(login=user_data["username"], password=user_data["password"])

    response = await client.post("/login", auth=auth)
    response_json: dict = await response.json()

    assert response.status == 201
    assert response_json.get("auth_token")
    assert re.fullmatch(
        pattern=r"^[A-Za-z0-9_-]{2,}(?:\.[A-Za-z0-9_-]{2,}){2}$", string=response_json["auth_token"]
    )


async def test_login_fail_unathorized(client: TestClient):
    response = await client.post("/login")
    response_json: dict = await response.json()

    assert response.status == 401
    assert response_json.get("error")


async def test_login_fail_invalid_password(user_factory, client: TestClient):
    user_data: dict = await user_factory(raw=True)
    await user_factory(**hash_password(user_data.copy()))
    auth = BasicAuth(login=user_data["username"], password="password")

    response = await client.post("/login", auth=auth)
    response_json: dict = await response.json()

    assert response.status == 401
    assert response_json.get("error")


async def test_request_fail_invalid_token(client: TestClient):
    response = await client.get(url(), headers={"Authorization": "Token invalid_token"})
    response_json: dict = await response.json()

    assert response.status == 401
    assert response_json.get("error")
