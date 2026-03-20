import pytest
from httpx import AsyncClient


async def _create_agent_user(client: AsyncClient, nickname: str = "agent_bot") -> str:
    response = await client.post("/api/users", json={"nickname": nickname, "is_agent": True})
    return response.json()["id"]


@pytest.mark.asyncio
async def test_create_agent_profile(client: AsyncClient) -> None:
    # given: an agent user
    user_id = await _create_agent_user(client)

    # when: creating an agent profile
    response = await client.post(f"/api/agents/{user_id}", json={"persona_file": "llama3/nihilist_nyx"})

    # then: profile is created
    assert response.status_code == 201
    data = response.json()
    assert data["user_id"] == user_id
    assert data["persona_file"] == "llama3/nihilist_nyx"
    assert data["is_active"] is True


@pytest.mark.asyncio
async def test_create_duplicate_agent_profile(client: AsyncClient) -> None:
    # given: an agent with existing profile
    user_id = await _create_agent_user(client)
    await client.post(f"/api/agents/{user_id}", json={"persona_file": "llama3/nihilist_nyx"})

    # when: creating another profile for same user
    response = await client.post(f"/api/agents/{user_id}", json={"persona_file": "gemma2/retro_rick"})

    # then: conflict
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_get_agent_profile(client: AsyncClient) -> None:
    # given: an agent profile
    user_id = await _create_agent_user(client)
    create_resp = await client.post(f"/api/agents/{user_id}", json={"persona_file": "gemma2/retro_rick"})
    profile_id = create_resp.json()["id"]

    # when: fetching the profile
    response = await client.get(f"/api/agents/{profile_id}")

    # then: returns the profile
    assert response.status_code == 200
    assert response.json()["persona_file"] == "gemma2/retro_rick"


@pytest.mark.asyncio
async def test_get_active_agents(client: AsyncClient) -> None:
    # given: multiple agents
    for i in range(3):
        uid = await _create_agent_user(client, f"bot_{i}")
        await client.post(f"/api/agents/{uid}", json={"persona_file": f"llama3/bot_{i}"})

    # when: fetching active agents
    response = await client.get("/api/agents/active")

    # then: returns all active agents
    assert response.status_code == 200
    assert len(response.json()) == 3


@pytest.mark.asyncio
async def test_update_agent_profile(client: AsyncClient) -> None:
    # given: an active agent
    user_id = await _create_agent_user(client)
    create_resp = await client.post(f"/api/agents/{user_id}", json={"persona_file": "llama3/nihilist_nyx"})
    profile_id = create_resp.json()["id"]

    # when: deactivating the agent
    response = await client.patch(f"/api/agents/{profile_id}", json={"is_active": False})

    # then: agent is deactivated
    assert response.status_code == 200
    assert response.json()["is_active"] is False


@pytest.mark.asyncio
async def test_get_agent_not_found(client: AsyncClient) -> None:
    # given: a non-existent profile id
    fake_id = "00000000-0000-0000-0000-000000000000"

    # when: fetching the profile
    response = await client.get(f"/api/agents/{fake_id}")

    # then: not found
    assert response.status_code == 404
