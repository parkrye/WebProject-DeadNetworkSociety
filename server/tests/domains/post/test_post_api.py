import pytest
from httpx import AsyncClient


async def _create_user(client: AsyncClient, nickname: str = "poster") -> str:
    response = await client.post("/api/users", json={"nickname": nickname})
    return response.json()["id"]


@pytest.mark.asyncio
async def test_create_post(client: AsyncClient) -> None:
    # given: an existing user
    author_id = await _create_user(client)
    payload = {"author_id": author_id, "title": "First Post", "content": "Hello world"}

    # when: creating a post
    response = await client.post("/api/posts", json=payload)

    # then: post is created
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "First Post"
    assert data["content"] == "Hello world"
    assert data["author_id"] == author_id


@pytest.mark.asyncio
async def test_create_post_empty_title(client: AsyncClient) -> None:
    # given: an empty title
    author_id = await _create_user(client)

    # when: creating a post with empty title
    response = await client.post("/api/posts", json={"author_id": author_id, "title": "", "content": "body"})

    # then: validation error
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_post(client: AsyncClient) -> None:
    # given: an existing post
    author_id = await _create_user(client)
    create_resp = await client.post("/api/posts", json={
        "author_id": author_id, "title": "Fetch Me", "content": "Content"
    })
    post_id = create_resp.json()["id"]

    # when: fetching the post
    response = await client.get(f"/api/posts/{post_id}")

    # then: returns the post
    assert response.status_code == 200
    assert response.json()["title"] == "Fetch Me"


@pytest.mark.asyncio
async def test_get_post_not_found(client: AsyncClient) -> None:
    # given: a non-existent post id
    fake_id = "00000000-0000-0000-0000-000000000000"

    # when: fetching the post
    response = await client.get(f"/api/posts/{fake_id}")

    # then: not found
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_posts_list(client: AsyncClient) -> None:
    # given: multiple posts
    author_id = await _create_user(client)
    for i in range(3):
        await client.post("/api/posts", json={
            "author_id": author_id, "title": f"Post {i}", "content": f"Content {i}"
        })

    # when: listing posts
    response = await client.get("/api/posts")

    # then: returns all posts
    assert response.status_code == 200
    assert len(response.json()) == 3


@pytest.mark.asyncio
async def test_update_post(client: AsyncClient) -> None:
    # given: an existing post
    author_id = await _create_user(client)
    create_resp = await client.post("/api/posts", json={
        "author_id": author_id, "title": "Old Title", "content": "Old Content"
    })
    post_id = create_resp.json()["id"]

    # when: updating the post
    response = await client.patch(f"/api/posts/{post_id}", json={"title": "New Title"})

    # then: title is updated, content remains
    assert response.status_code == 200
    assert response.json()["title"] == "New Title"
    assert response.json()["content"] == "Old Content"


@pytest.mark.asyncio
async def test_delete_post(client: AsyncClient) -> None:
    # given: an existing post
    author_id = await _create_user(client)
    create_resp = await client.post("/api/posts", json={
        "author_id": author_id, "title": "Delete Me", "content": "Content"
    })
    post_id = create_resp.json()["id"]

    # when: deleting the post
    response = await client.delete(f"/api/posts/{post_id}")

    # then: post is deleted
    assert response.status_code == 204
    get_resp = await client.get(f"/api/posts/{post_id}")
    assert get_resp.status_code == 404
