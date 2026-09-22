from app.services.llm import ProviderError


def test_failed_stream_saved_and_can_continue(client, headers, monkeypatch):
    async def fail(messages):
        yield {"type": "delta", "text": "部分回答"}
        raise ProviderError("upstream failed")

    monkeypatch.setattr(client.app.state.runtime.llm, "stream", fail)
    response = client.post(
        "/chat/stream",
        headers=headers,
        json={"question": "hello", "use_knowledge": False},
    )
    assert "event: error" in response.text
    identifier = client.get("/conversations", headers=headers).json()[0]["id"]
    history = client.get("/conversations/" + identifier, headers=headers).json()
    assert history[-1]["status"] == "failed" and history[-1]["content"] == "部分回答"
    result = client.post(
        "/chat",
        headers=headers,
        json={
            "question": "再问一次",
            "conversation_id": identifier,
            "use_knowledge": False,
        },
    )
    assert result.status_code == 200


def test_login_rate_limit(client):
    for _ in range(10):
        assert (
            client.post(
                "/auth/login",
                json={"email": "nobody@example.test", "password": "wrong"},
            ).status_code
            == 401
        )
    assert (
        client.post(
            "/auth/login", json={"email": "nobody@example.test", "password": "wrong"}
        ).status_code
        == 429
    )
