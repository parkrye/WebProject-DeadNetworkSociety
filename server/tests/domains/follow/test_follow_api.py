import pytest
from httpx import AsyncClient


async def _create_user(client: AsyncClient, nickname: str) -> str:
    resp = await client.post("/api/users", json={"nickname": nickname})
    return resp.json()["id"]


@pytest.mark.asyncio
async def test_follow_toggle(client: AsyncClient) -> None:
    """Follow then unfollow via toggle."""
    alice = await _create_user(client, "follow_alice")
    bob = await _create_user(client, "follow_bob")

    # Follow
    resp = await client.post("/api/follows", json={
        "follower_id": alice, "following_id": bob,
    })
    assert resp.status_code == 200
    assert resp.json()["follower_id"] == alice
    assert resp.json()["following_id"] == bob

    # Check
    check = await client.get(f"/api/follows/{bob}/check?viewer_id={alice}")
    assert check.json()["is_following"] is True

    # Unfollow (toggle)
    resp2 = await client.post("/api/follows", json={
        "follower_id": alice, "following_id": bob,
    })
    assert resp2.status_code == 200
    assert resp2.json() is None

    # Check again
    check2 = await client.get(f"/api/follows/{bob}/check?viewer_id={alice}")
    assert check2.json()["is_following"] is False


@pytest.mark.asyncio
async def test_self_follow_returns_none(client: AsyncClient) -> None:
    """Cannot follow yourself."""
    alice = await _create_user(client, "follow_self")
    resp = await client.post("/api/follows", json={
        "follower_id": alice, "following_id": alice,
    })
    assert resp.status_code == 200
    assert resp.json() is None


@pytest.mark.asyncio
async def test_followers_list(client: AsyncClient) -> None:
    """Followers list shows users who follow the target."""
    target = await _create_user(client, "follow_target")
    f1 = await _create_user(client, "follower1")
    f2 = await _create_user(client, "follower2")

    await client.post("/api/follows", json={"follower_id": f1, "following_id": target})
    await client.post("/api/follows", json={"follower_id": f2, "following_id": target})

    resp = await client.get(f"/api/follows/{target}/followers")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2
    nicknames = {d["nickname"] for d in data}
    assert "follower1" in nicknames
    assert "follower2" in nicknames


@pytest.mark.asyncio
async def test_following_list(client: AsyncClient) -> None:
    """Following list shows users the actor follows."""
    actor = await _create_user(client, "follow_actor")
    t1 = await _create_user(client, "follow_t1")
    t2 = await _create_user(client, "follow_t2")

    await client.post("/api/follows", json={"follower_id": actor, "following_id": t1})
    await client.post("/api/follows", json={"follower_id": actor, "following_id": t2})

    resp = await client.get(f"/api/follows/{actor}/following")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


@pytest.mark.asyncio
async def test_follow_count_in_stats(client: AsyncClient) -> None:
    """Profile stats include followers/following counts."""
    alice = await _create_user(client, "follow_stats_a")
    bob = await _create_user(client, "follow_stats_b")

    await client.post("/api/follows", json={"follower_id": alice, "following_id": bob})

    # Bob has 1 follower
    bob_stats = await client.get(f"/api/users/{bob}/stats")
    assert bob_stats.json()["followers_count"] == 1
    assert bob_stats.json()["following_count"] == 0

    # Alice follows 1
    alice_stats = await client.get(f"/api/users/{alice}/stats")
    assert alice_stats.json()["followers_count"] == 0
    assert alice_stats.json()["following_count"] == 1
