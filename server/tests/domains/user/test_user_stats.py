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


@pytest.mark.asyncio
async def test_stats_empty_user(client: AsyncClient) -> None:
    """User with no activity has all zeros."""
    user_id = await _create_user(client, "stats_empty")

    resp = await client.get(f"/api/users/{user_id}/stats")
    assert resp.status_code == 200
    data = resp.json()
    assert data["nickname"] == "stats_empty"
    assert data["post_count"] == 0
    assert data["comment_count"] == 0
    assert data["likes_given"] == 0
    assert data["likes_received"] == 0
    assert data["dislikes_given"] == 0
    assert data["dislikes_received"] == 0
    assert data["recent_posts"] == []
    assert data["recent_comments"] == []
    assert data["liked_items"] == []
    assert data["disliked_items"] == []


@pytest.mark.asyncio
async def test_stats_with_activity(client: AsyncClient) -> None:
    """Stats reflect posts, comments, and reactions."""
    author_id = await _create_user(client, "stats_active")
    other_id = await _create_user(client, "stats_other")

    # Author creates 2 posts
    post1 = await _create_post(client, author_id, "글1", "내용1")
    post2 = await _create_post(client, author_id, "글2", "내용2")

    # Author comments
    await client.post("/api/comments", json={
        "post_id": post1, "author_id": author_id, "content": "내 글에 댓글",
    })

    # Other user likes author's post
    await client.post("/api/reactions", json={
        "user_id": other_id, "target_type": "post", "target_id": post1, "reaction_type": "like",
    })

    # Author likes other's reaction target (self-like)
    other_post = await _create_post(client, other_id, "남의글", "내용")
    await client.post("/api/reactions", json={
        "user_id": author_id, "target_type": "post", "target_id": other_post, "reaction_type": "like",
    })

    resp = await client.get(f"/api/users/{author_id}/stats")
    assert resp.status_code == 200
    data = resp.json()
    assert data["post_count"] == 2
    assert data["comment_count"] == 1
    assert data["likes_given"] == 1
    assert data["likes_received"] == 1
    assert len(data["recent_posts"]) == 2
    assert len(data["liked_items"]) == 1


@pytest.mark.asyncio
async def test_stats_title_truncation(client: AsyncClient) -> None:
    """Post titles are truncated to 20 chars with ellipsis."""
    user_id = await _create_user(client, "stats_trunc")
    await _create_post(client, user_id, "이것은스물자가넘는매우매우긴제목입니다아아아", "내용")

    resp = await client.get(f"/api/users/{user_id}/stats")
    data = resp.json()
    title = data["recent_posts"][0]["title"]
    assert len(title) <= 23  # 20 chars + "..."
    assert title.endswith("...")


@pytest.mark.asyncio
async def test_stats_not_found(client: AsyncClient) -> None:
    fake_id = "00000000-0000-0000-0000-000000000000"
    resp = await client.get(f"/api/users/{fake_id}/stats")
    assert resp.status_code == 404
