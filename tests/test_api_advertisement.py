from pytest_aiohttp.plugin import TestClient

from server.models import Advertisement
from tests.utils import ClientInfo


def url(id: int = None):
    base_url = "/advertisement"
    if not id:
        return base_url
    return f"{base_url}/{id}"


async def test_get_list_success(adv_factory, client: TestClient):
    advs: list = await adv_factory(2)

    response = await client.get(url())
    response_json: list = await response.json()

    assert response.status == 200
    assert isinstance(response_json, list)
    for adv in advs:
        assert adv.as_dict in response_json


async def test_get_detail_success(adv_factory, client: TestClient, client_info: ClientInfo):
    adv: Advertisement = await adv_factory(user=client_info.model)

    response = await client.get(url(adv.id))
    response_json: dict = await response.json()

    assert response.status == 200
    assert adv.as_dict == response_json


async def test_post_authorized_success(adv_factory, client: TestClient, client_info: ClientInfo):
    adv_data: dict = await adv_factory(raw=True)
    adv_data.pop("user", None)

    response = await client.post(url(), json=adv_data, headers=client_info.auth_headers)
    response_json: dict = await response.json()

    assert response.status == 201
    assert adv_data["title"] == response_json["title"]
    assert adv_data["text"] == response_json["text"]
    assert client_info.id == response_json["id_user"]


async def test_post_fail_existed_title(adv_factory, client: TestClient, client_info: ClientInfo):
    adv: Advertisement = await adv_factory()
    adv_data: dict = await adv_factory(raw=True, title=adv.title)
    adv_data.pop("user", None)

    response = await client.post(url(), json=adv_data, headers=client_info.auth_headers)
    response_json: dict = await response.json()

    assert response.status == 409
    assert response_json.get("error")


async def test_post_fail_unauthorized(adv_factory, client: TestClient):
    adv_data: dict = await adv_factory(raw=True)
    adv_data.pop("user", None)

    response = await client.post(url(), json=adv_data)
    response_json: dict = await response.json()

    assert response.status == 401
    assert response_json.get("error")


async def test_post_fail_no_text(adv_factory, client: TestClient, client_info: ClientInfo):
    adv_data: dict = await adv_factory(raw=True)
    adv_data.pop("user", None)
    adv_data.pop("text", None)

    response = await client.post(url(), json=adv_data, headers=client_info.auth_headers)
    response_json: dict = await response.json()

    assert response.status == 400
    assert response_json.get("error")


async def test_patch_authorized_owner_success(
    adv_factory, client: TestClient, client_info: ClientInfo
):
    adv: Advertisement = await adv_factory(user=client_info.model)
    text = "Abrakadabra"

    response = await client.patch(
        url(adv.id), json={"text": text}, headers=client_info.auth_headers
    )
    response_json: dict = await response.json()

    assert response.status == 200
    assert adv.title == response_json["title"]
    assert text == response_json["text"]
    assert client_info.id == response_json["id_user"]


async def test_patch_authorized_fail_not_owner(
    adv_factory, client: TestClient, client_info: ClientInfo
):
    adv: Advertisement = await adv_factory()
    text = "Abrakadabra"

    response = await client.patch(
        url(adv.id), json={"text": text}, headers=client_info.auth_headers
    )
    response_json: dict = await response.json()

    assert response.status == 403
    assert response_json.get("error")


async def test_patch_fail_unauthorized(adv_factory, client: TestClient):
    adv: Advertisement = await adv_factory()
    text = "Abrakadabra"

    response = await client.patch(url(adv.id), json={"text": text})
    response_json: dict = await response.json()

    assert response.status == 401
    assert response_json.get("error")


async def test_delete_fail_unauthorized(adv_factory, client: TestClient):
    adv: Advertisement = await adv_factory()

    response = await client.delete(url(adv.id))
    response_json: dict = await response.json()

    assert response.status == 401
    assert response_json.get("error")


async def test_delete_authorized_fail_not_owner(
    adv_factory, client: TestClient, client_info: ClientInfo
):
    adv: Advertisement = await adv_factory()

    response = await client.delete(url(adv.id), headers=client_info.auth_headers)
    response_json: dict = await response.json()

    assert response.status == 403
    assert response_json.get("error")


async def test_delete_authorized_owner_success(
    adv_factory, client: TestClient, client_info: ClientInfo
):
    adv: Advertisement = await adv_factory(user=client_info.model)

    response = await client.delete(url(adv.id), headers=client_info.auth_headers)

    assert response.status == 204
