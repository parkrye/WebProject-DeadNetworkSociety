"""
E2E test: Full community interaction flow.
User creation -> Post creation -> Comment -> Reply -> Reactions -> Feed verification
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_full_community_flow(client: AsyncClient) -> None:
    """Complete flow: two users interact via posts, comments, and reactions."""

    # -- Step 1: Create two human users --
    alice_resp = await client.post("/api/users", json={"nickname": "alice"})
    assert alice_resp.status_code == 201
    alice_id = alice_resp.json()["id"]

    bob_resp = await client.post("/api/users", json={"nickname": "bob"})
    assert bob_resp.status_code == 201
    bob_id = bob_resp.json()["id"]

    # -- Step 2: Alice creates a post --
    post_resp = await client.post("/api/posts", json={
        "author_id": alice_id,
        "title": "Welcome to Dead Network Society",
        "content": "This is the first post on our platform. What do you think?",
    })
    assert post_resp.status_code == 201
    post_id = post_resp.json()["id"]
    assert post_resp.json()["author_id"] == alice_id

    # -- Step 3: Bob comments on Alice's post --
    comment_resp = await client.post("/api/comments", json={
        "post_id": post_id,
        "author_id": bob_id,
        "content": "Great start! Looking forward to more content.",
    })
    assert comment_resp.status_code == 201
    comment_id = comment_resp.json()["id"]
    assert comment_resp.json()["depth"] == 0

    # -- Step 4: Alice replies to Bob's comment --
    reply_resp = await client.post("/api/comments", json={
        "post_id": post_id,
        "author_id": alice_id,
        "content": "Thanks Bob! Stay tuned.",
        "parent_id": comment_id,
    })
    assert reply_resp.status_code == 201
    assert reply_resp.json()["depth"] == 1
    assert reply_resp.json()["parent_id"] == comment_id

    # -- Step 5: Both users react to the post --
    like_resp = await client.post("/api/reactions", json={
        "user_id": bob_id,
        "target_type": "post",
        "target_id": post_id,
        "reaction_type": "like",
    })
    assert like_resp.status_code == 200
    assert like_resp.json()["reaction_type"] == "like"

    alice_like_resp = await client.post("/api/reactions", json={
        "user_id": alice_id,
        "target_type": "post",
        "target_id": post_id,
        "reaction_type": "like",
    })
    assert alice_like_resp.status_code == 200

    # -- Step 6: Verify reaction counts --
    counts_resp = await client.get(f"/api/reactions/counts/post/{post_id}")
    assert counts_resp.status_code == 200
    counts = counts_resp.json()
    assert counts["like"] == 2
    assert counts["dislike"] == 0

    # -- Step 7: Bob reacts to the comment --
    comment_like_resp = await client.post("/api/reactions", json={
        "user_id": bob_id,
        "target_type": "comment",
        "target_id": comment_id,
        "reaction_type": "like",
    })
    assert comment_like_resp.status_code == 200

    # -- Step 8: Verify comments on the post --
    comments_resp = await client.get(f"/api/comments/by-post/{post_id}")
    assert comments_resp.status_code == 200
    comments = comments_resp.json()
    assert len(comments) == 2

    # -- Step 9: Verify the feed --
    feed_resp = await client.get("/api/posts")
    assert feed_resp.status_code == 200
    feed = feed_resp.json()
    assert len(feed) == 1
    assert feed[0]["title"] == "Welcome to Dead Network Society"

    # -- Step 10: Verify post detail --
    detail_resp = await client.get(f"/api/posts/{post_id}")
    assert detail_resp.status_code == 200
    assert detail_resp.json()["title"] == "Welcome to Dead Network Society"


@pytest.mark.asyncio
async def test_agent_user_flow(client: AsyncClient) -> None:
    """Flow: Create an AI agent user with profile."""

    # -- Step 1: Create agent user --
    agent_resp = await client.post("/api/users", json={
        "nickname": "NihilistNyx",
        "is_agent": True,
    })
    assert agent_resp.status_code == 201
    agent_id = agent_resp.json()["id"]
    assert agent_resp.json()["is_agent"] is True

    # -- Step 2: Create agent profile --
    profile_resp = await client.post(f"/api/agents/{agent_id}", json={
        "persona_file": "nihilist_nyx",
    })
    assert profile_resp.status_code == 201
    assert profile_resp.json()["is_active"] is True
    profile_id = profile_resp.json()["id"]

    # -- Step 3: Agent creates a post --
    post_resp = await client.post("/api/posts", json={
        "author_id": agent_id,
        "title": "The Void Speaks",
        "content": "nothing matters and yet here we are, posting into the abyss.",
    })
    assert post_resp.status_code == 201

    # -- Step 4: Verify agent appears in active list --
    active_resp = await client.get("/api/agents/active")
    assert active_resp.status_code == 200
    active_ids = [a["id"] for a in active_resp.json()]
    assert profile_id in active_ids

    # -- Step 5: Deactivate agent --
    update_resp = await client.patch(f"/api/agents/{profile_id}", json={"is_active": False})
    assert update_resp.status_code == 200
    assert update_resp.json()["is_active"] is False

    # -- Step 6: Agent no longer in active list --
    active_resp2 = await client.get("/api/agents/active")
    active_ids2 = [a["id"] for a in active_resp2.json()]
    assert profile_id not in active_ids2


@pytest.mark.asyncio
async def test_reaction_toggle_flow(client: AsyncClient) -> None:
    """Flow: Like -> toggle off -> switch to dislike."""

    # Setup
    user_resp = await client.post("/api/users", json={"nickname": "toggler"})
    user_id = user_resp.json()["id"]
    post_resp = await client.post("/api/posts", json={
        "author_id": user_id, "title": "Toggle Test", "content": "Testing reactions"
    })
    post_id = post_resp.json()["id"]

    # Like
    r1 = await client.post("/api/reactions", json={
        "user_id": user_id, "target_type": "post", "target_id": post_id, "reaction_type": "like"
    })
    assert r1.json()["reaction_type"] == "like"

    counts1 = await client.get(f"/api/reactions/counts/post/{post_id}")
    assert counts1.json()["like"] == 1

    # Toggle off (same reaction again)
    r2 = await client.post("/api/reactions", json={
        "user_id": user_id, "target_type": "post", "target_id": post_id, "reaction_type": "like"
    })
    assert r2.json() is None

    counts2 = await client.get(f"/api/reactions/counts/post/{post_id}")
    assert counts2.json()["like"] == 0

    # Switch to dislike
    r3 = await client.post("/api/reactions", json={
        "user_id": user_id, "target_type": "post", "target_id": post_id, "reaction_type": "dislike"
    })
    assert r3.json()["reaction_type"] == "dislike"

    counts3 = await client.get(f"/api/reactions/counts/post/{post_id}")
    assert counts3.json()["dislike"] == 1
    assert counts3.json()["like"] == 0


@pytest.mark.asyncio
async def test_comment_thread_depth(client: AsyncClient) -> None:
    """Flow: Nested comment thread with increasing depth."""

    user_resp = await client.post("/api/users", json={"nickname": "threader"})
    user_id = user_resp.json()["id"]
    post_resp = await client.post("/api/posts", json={
        "author_id": user_id, "title": "Thread Test", "content": "Deep thread"
    })
    post_id = post_resp.json()["id"]

    # Create a chain of 5 nested comments
    parent_id = None
    for depth in range(5):
        resp = await client.post("/api/comments", json={
            "post_id": post_id,
            "author_id": user_id,
            "content": f"Comment at depth {depth}",
            **({"parent_id": parent_id} if parent_id else {}),
        })
        assert resp.status_code == 201
        assert resp.json()["depth"] == depth
        parent_id = resp.json()["id"]

    # Verify all 5 comments exist
    comments_resp = await client.get(f"/api/comments/by-post/{post_id}")
    assert len(comments_resp.json()) == 5
