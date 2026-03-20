import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_enriched_feed(client: AsyncClient) -> None:
    """Feed endpoint returns author nickname, reaction counts, and comment count."""

    # given: a user, a post, comments, and reactions
    user_resp = await client.post("/api/users", json={"nickname": "feeduser"})
    user_id = user_resp.json()["id"]

    user2_resp = await client.post("/api/users", json={"nickname": "feeduser2"})
    user2_id = user2_resp.json()["id"]

    post_resp = await client.post("/api/posts", json={
        "author_id": user_id, "title": "Feed Post", "content": "Content here"
    })
    post_id = post_resp.json()["id"]

    await client.post("/api/comments", json={
        "post_id": post_id, "author_id": user2_id, "content": "Comment 1"
    })
    await client.post("/api/comments", json={
        "post_id": post_id, "author_id": user_id, "content": "Comment 2"
    })

    await client.post("/api/reactions", json={
        "user_id": user_id, "target_type": "post", "target_id": post_id, "reaction_type": "like"
    })
    await client.post("/api/reactions", json={
        "user_id": user2_id, "target_type": "post", "target_id": post_id, "reaction_type": "dislike"
    })

    # when: fetching the enriched feed
    response = await client.get("/api/posts/feed")

    # then: returns enriched data
    assert response.status_code == 200
    feed = response.json()
    assert len(feed) == 1

    post = feed[0]
    assert post["author_nickname"] == "feeduser"
    assert post["like_count"] == 1
    assert post["dislike_count"] == 1
    assert post["comment_count"] == 2
    assert post["title"] == "Feed Post"
