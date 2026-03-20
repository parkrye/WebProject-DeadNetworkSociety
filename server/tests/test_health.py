import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient) -> None:
    # given: a running application

    # when: requesting the health endpoint
    response = await client.get("/health")

    # then: returns ok status
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
