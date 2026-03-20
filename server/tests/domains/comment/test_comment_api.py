import pytest
from httpx import AsyncClient


async def _create_user(client: AsyncClient, nickname: str = "commenter") -> str:
    response = await client.post("/api/users", json={"nickname": nickname})
    return response.json()["id"]


async def _create_post(client: AsyncClient, author_id: str) -> str:
    response = await client.post("/api/posts", json={
        "author_id": author_id, "title": "Test Post", "content": "Content"
    })
    return response.json()["id"]


@pytest.mark.asyncio
async def test_create_comment(client: AsyncClient) -> None:
    # given: a user and a post
    author_id = await _create_user(client)
    post_id = await _create_post(client, author_id)

    # when: creating a comment
    response = await client.post("/api/comments", json={
        "post_id": post_id, "author_id": author_id, "content": "Nice post!"
    })

    # then: comment is created with depth 0
    assert response.status_code == 201
    data = response.json()
    assert data["content"] == "Nice post!"
    assert data["depth"] == 0
    assert data["parent_id"] is None


@pytest.mark.asyncio
async def test_create_reply(client: AsyncClient) -> None:
    # given: an existing comment
    author_id = await _create_user(client)
    post_id = await _create_post(client, author_id)
    parent_resp = await client.post("/api/comments", json={
        "post_id": post_id, "author_id": author_id, "content": "Parent"
    })
    parent_id = parent_resp.json()["id"]

    # when: creating a reply
    response = await client.post("/api/comments", json={
        "post_id": post_id, "author_id": author_id, "content": "Reply", "parent_id": parent_id
    })

    # then: reply has depth 1
    assert response.status_code == 201
    data = response.json()
    assert data["depth"] == 1
    assert data["parent_id"] == parent_id


@pytest.mark.asyncio
async def test_create_nested_reply(client: AsyncClient) -> None:
    # given: a reply comment (depth 1)
    author_id = await _create_user(client)
    post_id = await _create_post(client, author_id)
    c1 = await client.post("/api/comments", json={
        "post_id": post_id, "author_id": author_id, "content": "Level 0"
    })
    c2 = await client.post("/api/comments", json={
        "post_id": post_id, "author_id": author_id, "content": "Level 1", "parent_id": c1.json()["id"]
    })

    # when: creating a nested reply
    response = await client.post("/api/comments", json={
        "post_id": post_id, "author_id": author_id, "content": "Level 2", "parent_id": c2.json()["id"]
    })

    # then: depth is 2
    assert response.status_code == 201
    assert response.json()["depth"] == 2


@pytest.mark.asyncio
async def test_get_comments_by_post(client: AsyncClient) -> None:
    # given: comments on a post
    author_id = await _create_user(client)
    post_id = await _create_post(client, author_id)
    for i in range(3):
        await client.post("/api/comments", json={
            "post_id": post_id, "author_id": author_id, "content": f"Comment {i}"
        })

    # when: fetching comments for the post
    response = await client.get(f"/api/comments/by-post/{post_id}")

    # then: returns all comments
    assert response.status_code == 200
    assert len(response.json()) == 3


@pytest.mark.asyncio
async def test_update_comment(client: AsyncClient) -> None:
    # given: an existing comment
    author_id = await _create_user(client)
    post_id = await _create_post(client, author_id)
    create_resp = await client.post("/api/comments", json={
        "post_id": post_id, "author_id": author_id, "content": "Old"
    })
    comment_id = create_resp.json()["id"]

    # when: updating the comment
    response = await client.patch(f"/api/comments/{comment_id}", json={"content": "Updated"})

    # then: content is updated
    assert response.status_code == 200
    assert response.json()["content"] == "Updated"


@pytest.mark.asyncio
async def test_delete_comment(client: AsyncClient) -> None:
    # given: an existing comment
    author_id = await _create_user(client)
    post_id = await _create_post(client, author_id)
    create_resp = await client.post("/api/comments", json={
        "post_id": post_id, "author_id": author_id, "content": "Delete me"
    })
    comment_id = create_resp.json()["id"]

    # when: deleting the comment
    response = await client.delete(f"/api/comments/{comment_id}")

    # then: comment is deleted
    assert response.status_code == 204
    get_resp = await client.get(f"/api/comments/{comment_id}")
    assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_create_comment_invalid_parent(client: AsyncClient) -> None:
    # given: a non-existent parent id
    author_id = await _create_user(client)
    post_id = await _create_post(client, author_id)
    fake_id = "00000000-0000-0000-0000-000000000000"

    # when: creating a reply with invalid parent
    response = await client.post("/api/comments", json={
        "post_id": post_id, "author_id": author_id, "content": "Reply", "parent_id": fake_id
    })

    # then: not found
    assert response.status_code == 404
