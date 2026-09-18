import pytest


@pytest.mark.asyncio
async def test_health(client):
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


@pytest.mark.asyncio
async def test_chat_empty_message(client):
    response = await client.post("/api/v1/chat", json={"message": ""})
    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_agent_status(client):
    response = await client.get("/api/v1/status")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_chat_without_session_id_gets_own_session(client, monkeypatch):
    from src.api import routes
    from src.models.schemas import AgentDecision
    from tests.conftest import ScriptedReasoner, make_test_graph

    final = AgentDecision(thought="t", action="final", enough_data=True, final_answer="ok")
    monkeypatch.setattr(routes, "agent", make_test_graph(ScriptedReasoner([final, final])))

    first = (await client.post("/api/v1/chat", json={"message": "Chào"})).json()
    second = (await client.post("/api/v1/chat", json={"message": "Chào"})).json()

    assert first["session_id"] and second["session_id"]
    assert first["session_id"] != second["session_id"]


@pytest.mark.asyncio
async def test_resume_requires_session_id(client):
    response = await client.post("/api/v1/chat/resume", json={"resume": "approve"})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_resume_surfaces_second_interrupt(client, monkeypatch):
    from src.api import routes
    from src.models.schemas import AgentDecision
    from tests.conftest import ScriptedReasoner, make_test_graph

    email = AgentDecision(
        thought="gửi", action="tool", tool_name="send_email",
        tool_args={"to": "a@example.com", "subject": "s", "body": "b"},
    )
    monkeypatch.setattr(routes, "agent", make_test_graph(ScriptedReasoner([email, email])))

    first = (await client.post("/api/v1/chat", json={"message": "Gửi 2 email"})).json()
    resumed = await client.post(
        "/api/v1/chat/resume", json={"session_id": first["session_id"], "resume": "approve"}
    )

    assert resumed.status_code == 200
    assert resumed.json()["response"].startswith("[CẦN PHÊ DUYỆT]")
