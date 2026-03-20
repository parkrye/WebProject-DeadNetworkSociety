import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_user(client: AsyncClient) -> None:
    # given: a valid user payload
    payload = {"nickname": "testuser"}

    # when: creating a user
    response = await client.post("/api/users", json=payload)

    # then: user is created successfully
    assert response.status_code == 201
    data = response.json()
    assert data["nickname"] == "testuser"
    assert data["is_agent"] is False
    assert "id" in data


@pytest.mark.asyncio
async def test_create_agent_user(client: AsyncClient) -> None:
    # given: a payload with is_agent=True
    payload = {"nickname": "bot_agent", "is_agent": True}

    # when: creating an agent user
    response = await client.post("/api/users", json=payload)

    # then: agent user is created
    assert response.status_code == 201
    assert response.json()["is_agent"] is True


@pytest.mark.asyncio
async def test_create_user_duplicate_nickname(client: AsyncClient) -> None:
    # given: an existing user
    await client.post("/api/users", json={"nickname": "duplicate"})

    # when: creating another user with same nickname
    response = await client.post("/api/users", json={"nickname": "duplicate"})

    # then: conflict error
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_create_user_short_nickname(client: AsyncClient) -> None:
    # given: a nickname that is too short
    payload = {"nickname": "a"}

    # when: creating a user
    response = await client.post("/api/users", json=payload)

    # then: validation error
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_user(client: AsyncClient) -> None:
    # given: an existing user
    create_response = await client.post("/api/users", json={"nickname": "getme"})
    user_id = create_response.json()["id"]

    # when: fetching the user
    response = await client.get(f"/api/users/{user_id}")

    # then: returns the user
    assert response.status_code == 200
    assert response.json()["nickname"] == "getme"


@pytest.mark.asyncio
async def test_get_user_not_found(client: AsyncClient) -> None:
    # given: a non-existent user id
    fake_id = "00000000-0000-0000-0000-000000000000"

    # when: fetching the user
    response = await client.get(f"/api/users/{fake_id}")

    # then: not found
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_users_list(client: AsyncClient) -> None:
    # given: multiple users
    await client.post("/api/users", json={"nickname": "user1"})
    await client.post("/api/users", json={"nickname": "user2"})
    await client.post("/api/users", json={"nickname": "user3"})

    # when: listing users
    response = await client.get("/api/users")

    # then: returns all users
    assert response.status_code == 200
    assert len(response.json()) == 3


@pytest.mark.asyncio
async def test_get_users_pagination(client: AsyncClient) -> None:
    # given: multiple users
    for i in range(5):
        await client.post("/api/users", json={"nickname": f"page_user_{i}"})

    # when: requesting page 1 with size 2
    response = await client.get("/api/users?page=1&size=2")

    # then: returns 2 users
    assert response.status_code == 200
    assert len(response.json()) == 2


@pytest.mark.asyncio
async def test_update_user(client: AsyncClient) -> None:
    # given: an existing user
    create_response = await client.post("/api/users", json={"nickname": "old_name"})
    user_id = create_response.json()["id"]

    # when: updating the nickname
    response = await client.patch(f"/api/users/{user_id}", json={"nickname": "new_name"})

    # then: nickname is updated
    assert response.status_code == 200
    assert response.json()["nickname"] == "new_name"


@pytest.mark.asyncio
async def test_update_user_duplicate_nickname(client: AsyncClient) -> None:
    # given: two existing users
    await client.post("/api/users", json={"nickname": "taken_name"})
    create_response = await client.post("/api/users", json={"nickname": "other_name"})
    user_id = create_response.json()["id"]

    # when: updating to a taken nickname
    response = await client.patch(f"/api/users/{user_id}", json={"nickname": "taken_name"})

    # then: conflict error
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_delete_user(client: AsyncClient) -> None:
    # given: an existing user
    create_response = await client.post("/api/users", json={"nickname": "deleteme"})
    user_id = create_response.json()["id"]

    # when: deleting the user
    response = await client.delete(f"/api/users/{user_id}")

    # then: user is deleted
    assert response.status_code == 204

    # and: user is no longer found
    get_response = await client.get(f"/api/users/{user_id}")
    assert get_response.status_code == 404
