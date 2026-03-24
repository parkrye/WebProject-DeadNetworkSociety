import pytest
from httpx import AsyncClient


async def _create_user(client: AsyncClient, nickname: str) -> str:
    resp = await client.post("/api/users", json={"nickname": nickname})
    return resp.json()["id"]


async def _create_post(client: AsyncClient, author_id: str, title: str, content: str) -> str:
    resp = await client.post("/api/posts", json={
        "author_id": author_id, "title": title, "content": content,
    })
    return resp.json()["id"]


async def _react(client: AsyncClient, user_id: str, post_id: str, reaction: str) -> None:
    await client.post("/api/reactions", json={
        "user_id": user_id, "target_type": "post", "target_id": post_id, "reaction_type": reaction,
    })


async def _comment(client: AsyncClient, author_id: str, post_id: str, content: str) -> str:
    resp = await client.post("/api/comments", json={
        "post_id": post_id, "author_id": author_id, "content": content,
    })
    return resp.json()["id"]


async def _refresh_popular(client: AsyncClient) -> None:
    resp = await client.post("/api/posts/popular/refresh")
    assert resp.status_code == 204


@pytest.mark.asyncio
async def test_popular_feed_empty(client: AsyncClient) -> None:
    """No posts meet the min_engagement threshold."""
    await _refresh_popular(client)
    resp = await client.get("/api/posts/popular")
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_popular_feed_filters_low_engagement(client: AsyncClient) -> None:
    """Posts with less than min_engagement are excluded."""
    user_id = await _create_user(client, "pop_user1")
    post_id = await _create_post(client, user_id, "낮은 인기", "관심 없는 글")
    liker_id = await _create_user(client, "pop_liker1")
    await _react(client, liker_id, post_id, "like")

    await _refresh_popular(client)
    resp = await client.get("/api/posts/popular")

    assert resp.status_code == 200
    assert len(resp.json()) == 0


@pytest.mark.asyncio
async def test_popular_feed_includes_engaged_posts(client: AsyncClient) -> None:
    """Posts meeting min_engagement threshold appear in popular feed."""
    author_id = await _create_user(client, "pop_author")
    post_id = await _create_post(client, author_id, "인기글 테스트", "좋아요 많이 받을 글")
    liker1 = await _create_user(client, "pop_lk1")
    liker2 = await _create_user(client, "pop_lk2")
    await _react(client, liker1, post_id, "like")
    await _react(client, liker2, post_id, "like")

    await _refresh_popular(client)
    resp = await client.get("/api/posts/popular")

    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["title"] == "인기글 테스트"


@pytest.mark.asyncio
async def test_popular_feed_ordered_by_score(client: AsyncClient) -> None:
    """More engaged posts rank higher."""
    author = await _create_user(client, "pop_ord_author")
    u1 = await _create_user(client, "pop_ord_u1")
    u2 = await _create_user(client, "pop_ord_u2")
    u3 = await _create_user(client, "pop_ord_u3")

    low_post = await _create_post(client, author, "보통 인기", "괜찮은 글")
    high_post = await _create_post(client, author, "높은 인기", "대박 글")

    # low: 2 likes
    await _react(client, u1, low_post, "like")
    await _react(client, u2, low_post, "like")

    # high: 2 likes + 1 comment
    await _react(client, u1, high_post, "like")
    await _react(client, u2, high_post, "like")
    await _comment(client, u3, high_post, "댓글 추가")

    # Refresh twice: each refresh adds 1 new post to queue
    await _refresh_popular(client)
    await _refresh_popular(client)
    resp = await client.get("/api/posts/popular")

    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2
    assert data[0]["title"] == "높은 인기"
    assert data[1]["title"] == "보통 인기"


@pytest.mark.asyncio
async def test_popular_max_slots(client: AsyncClient) -> None:
    """Popular queue is capped at max_slots (10)."""
    author = await _create_user(client, "pop_max_author")
    users = []
    for i in range(3):
        uid = await _create_user(client, f"pop_max_u{i}")
        users.append(uid)

    # Create 12 posts each with 2 likes (meets threshold)
    for i in range(12):
        pid = await _create_post(client, author, f"글{i}", f"내용{i}")
        await _react(client, users[0], pid, "like")
        await _react(client, users[1], pid, "like")

    # Refresh 12 times to add all candidates
    for _ in range(12):
        await _refresh_popular(client)
    resp = await client.get("/api/posts/popular")

    assert resp.status_code == 200
    assert len(resp.json()) <= 10
