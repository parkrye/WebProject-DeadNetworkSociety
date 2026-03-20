import pytest
from httpx import AsyncClient


async def _create_user(client: AsyncClient, nickname: str = "reactor") -> str:
    response = await client.post("/api/users", json={"nickname": nickname})
    return response.json()["id"]


async def _create_post(client: AsyncClient, author_id: str) -> str:
    response = await client.post("/api/posts", json={
        "author_id": author_id, "title": "Test Post", "content": "Content"
    })
    return response.json()["id"]


@pytest.mark.asyncio
async def test_like_post(client: AsyncClient) -> None:
    # given: a user and a post
    user_id = await _create_user(client)
    post_id = await _create_post(client, user_id)

    # when: liking the post
    response = await client.post("/api/reactions", json={
        "user_id": user_id, "target_type": "post", "target_id": post_id, "reaction_type": "like"
    })

    # then: reaction is created
    assert response.status_code == 200
    data = response.json()
    assert data["reaction_type"] == "like"
    assert data["target_type"] == "post"


@pytest.mark.asyncio
async def test_toggle_same_reaction_removes_it(client: AsyncClient) -> None:
    # given: a liked post
    user_id = await _create_user(client)
    post_id = await _create_post(client, user_id)
    await client.post("/api/reactions", json={
        "user_id": user_id, "target_type": "post", "target_id": post_id, "reaction_type": "like"
    })

    # when: liking again (toggle off)
    response = await client.post("/api/reactions", json={
        "user_id": user_id, "target_type": "post", "target_id": post_id, "reaction_type": "like"
    })

    # then: reaction is removed (null response)
    assert response.status_code == 200
    assert response.json() is None


@pytest.mark.asyncio
async def test_switch_reaction_type(client: AsyncClient) -> None:
    # given: a liked post
    user_id = await _create_user(client)
    post_id = await _create_post(client, user_id)
    await client.post("/api/reactions", json={
        "user_id": user_id, "target_type": "post", "target_id": post_id, "reaction_type": "like"
    })

    # when: disliking (switch from like to dislike)
    response = await client.post("/api/reactions", json={
        "user_id": user_id, "target_type": "post", "target_id": post_id, "reaction_type": "dislike"
    })

    # then: reaction switched to dislike
    assert response.status_code == 200
    assert response.json()["reaction_type"] == "dislike"


@pytest.mark.asyncio
async def test_get_reaction_counts(client: AsyncClient) -> None:
    # given: multiple users reacting to a post
    user1 = await _create_user(client, "user1")
    user2 = await _create_user(client, "user2")
    user3 = await _create_user(client, "user3")
    post_id = await _create_post(client, user1)

    await client.post("/api/reactions", json={
        "user_id": user1, "target_type": "post", "target_id": post_id, "reaction_type": "like"
    })
    await client.post("/api/reactions", json={
        "user_id": user2, "target_type": "post", "target_id": post_id, "reaction_type": "like"
    })
    await client.post("/api/reactions", json={
        "user_id": user3, "target_type": "post", "target_id": post_id, "reaction_type": "dislike"
    })

    # when: getting counts
    response = await client.get(f"/api/reactions/counts/post/{post_id}")

    # then: returns correct counts
    assert response.status_code == 200
    data = response.json()
    assert data["like"] == 2
    assert data["dislike"] == 1


@pytest.mark.asyncio
async def test_reaction_counts_empty(client: AsyncClient) -> None:
    # given: a post with no reactions
    user_id = await _create_user(client)
    post_id = await _create_post(client, user_id)

    # when: getting counts
    response = await client.get(f"/api/reactions/counts/post/{post_id}")

    # then: all zeros
    assert response.status_code == 200
    data = response.json()
    assert data["like"] == 0
    assert data["dislike"] == 0


@pytest.mark.asyncio
async def test_invalid_reaction_type(client: AsyncClient) -> None:
    # given: an invalid reaction type
    user_id = await _create_user(client)
    post_id = await _create_post(client, user_id)

    # when: sending invalid reaction_type
    response = await client.post("/api/reactions", json={
        "user_id": user_id, "target_type": "post", "target_id": post_id, "reaction_type": "love"
    })

    # then: validation error
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_invalid_target_type(client: AsyncClient) -> None:
    # given: an invalid target type
    user_id = await _create_user(client)

    # when: sending invalid target_type
    response = await client.post("/api/reactions", json={
        "user_id": user_id, "target_type": "story", "target_id": user_id, "reaction_type": "like"
    })

    # then: validation error
    assert response.status_code == 422
