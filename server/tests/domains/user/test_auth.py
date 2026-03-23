import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_login_creates_new_user(client: AsyncClient) -> None:
    """First login with unknown username creates a new account."""
    resp = await client.post("/api/users/login", json={
        "username": "newuser", "password": "pass1234",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["nickname"] == "newuser"
    assert data["is_agent"] is False


@pytest.mark.asyncio
async def test_login_existing_user_correct_password(client: AsyncClient) -> None:
    """Login with correct password succeeds."""
    # given: register
    await client.post("/api/users/login", json={
        "username": "existing", "password": "mypass",
    })

    # when: login again
    resp = await client.post("/api/users/login", json={
        "username": "existing", "password": "mypass",
    })

    # then: success
    assert resp.status_code == 200
    assert resp.json()["nickname"] == "existing"


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient) -> None:
    """Login with wrong password returns 401."""
    # given: register
    await client.post("/api/users/login", json={
        "username": "secured", "password": "correct",
    })

    # when: wrong password
    resp = await client.post("/api/users/login", json={
        "username": "secured", "password": "wrong",
    })

    # then: unauthorized
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_login_password_too_short(client: AsyncClient) -> None:
    """Password must be at least 4 chars."""
    resp = await client.post("/api/users/login", json={
        "username": "shortpw", "password": "abc",
    })
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_update_profile(client: AsyncClient) -> None:
    """User can update nickname, bio, and avatar_url."""
    # given: a user
    create_resp = await client.post("/api/users", json={"nickname": "editme"})
    user_id = create_resp.json()["id"]

    # when: update profile
    resp = await client.patch(f"/api/users/{user_id}", json={
        "nickname": "edited",
        "bio": "Hello world",
        "avatar_url": "https://example.com/avatar.png",
    })

    # then: updated
    assert resp.status_code == 200
    data = resp.json()
    assert data["nickname"] == "edited"
    assert data["bio"] == "Hello world"
    assert data["avatar_url"] == "https://example.com/avatar.png"


@pytest.mark.asyncio
async def test_update_bio_only(client: AsyncClient) -> None:
    """Partial update: only bio changes."""
    create_resp = await client.post("/api/users", json={"nickname": "bioonly"})
    user_id = create_resp.json()["id"]

    resp = await client.patch(f"/api/users/{user_id}", json={"bio": "Just a bio"})
    assert resp.status_code == 200
    assert resp.json()["bio"] == "Just a bio"
    assert resp.json()["nickname"] == "bioonly"
