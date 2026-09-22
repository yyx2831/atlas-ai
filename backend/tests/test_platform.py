import json
import asyncio
import httpx
import pytest
from app.services.knowledge import split_text, parse_document
from app.services.retrieval import bm25, rrf
from app.services.chat import validate_citations
from app.services.llm import ProviderError
from app.services.tools import validate_call


def upload(
    client, headers, text="设备频繁断连，请检查网线和供电。ERR-1007 是链路不稳定。"
):
    response = client.post(
        "/knowledge/documents",
        headers=headers,
        files={"file": ("manual.md", text.encode(), "text/markdown")},
        data={"product": "router", "version": "v1"},
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_auth_and_roles(client, headers, viewer_headers):
    assert (
        client.post(
            "/auth/login", json={"email": "admin@example.test", "password": "wrong"}
        ).status_code
        == 401
    )
    login = client.post(
        "/auth/login",
        json={"email": "admin@example.test", "password": "test-password-123"},
    )
    assert login.status_code == 200
    assert "password_hash" not in login.text
    assert (
        client.get(
            "/devices", headers={"x-device-token": "secret-device-key"}
        ).status_code
        == 401
    )
    assert (
        client.get("/auth/me", headers={"Authorization": "Bearer broken"}).status_code
        == 401
    )
    assert (
        client.post(
            "/devices",
            headers=viewer_headers,
            json={"name": "a", "device_type": "router", "ip": "192.0.2.1"},
        ).status_code
        == 403
    )
    assert (
        client.post(
            "/auth/users",
            headers=viewer_headers,
            json={"email": "new@example.test", "password": "test-password-123"},
        ).status_code
        == 403
    )
    assert client.get("/devices", headers=viewer_headers).status_code == 200


def test_knowledge_citations_isolation_and_delete(client, headers, viewer_headers):
    doc = upload(client, headers)
    assert upload(client, headers)["id"] == doc["id"]
    hits = client.get(
        "/knowledge/search", params={"q": "ERR-1007 断连"}, headers=headers
    ).json()
    assert hits and hits[0]["page"] == 1
    assert (
        client.get(
            "/knowledge/search",
            params={"q": "断连", "product": "wrong"},
            headers=headers,
        ).json()
        == []
    )
    assert (
        client.get(
            "/knowledge/search", params={"q": "断连"}, headers=viewer_headers
        ).json()
        == []
    )
    assert (
        client.get(
            f"/knowledge/documents/{doc['id']}/file", headers=viewer_headers
        ).status_code
        == 404
    )
    response = client.post(
        "/chat", headers=headers, json={"question": "设备断连怎么办"}
    )
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["citations"] and result["citations"][0]["document_id"] == doc["id"]
    assert (
        client.get(
            "/conversations/" + result["conversation_id"], headers=viewer_headers
        ).status_code
        == 404
    )
    assert (
        client.post(
            "/knowledge/documents/" + doc["id"] + "/reindex", headers=headers
        ).status_code
        == 200
    )
    assert (
        client.delete("/knowledge/documents/" + doc["id"], headers=headers).status_code
        == 204
    )
    assert (
        client.get("/knowledge/search", params={"q": "断连"}, headers=headers).json()
        == []
    )


def test_stream_and_empty_knowledge(client, headers):
    empty = client.post("/chat", headers=headers, json={"question": "不存在的内容"})
    assert "没有足够资料" in empty.json()["answer"]
    upload(client, headers)
    response = client.post(
        "/chat/stream", headers=headers, json={"question": "断连怎么办"}
    )
    assert response.status_code == 200
    events = [frame for frame in response.text.split("\n\n") if frame]
    assert events[0].startswith("event: meta")
    assert any(frame.startswith("event: delta") for frame in events)
    final = json.loads(events[-1].split("data: ", 1)[1])
    assert events[-1].startswith("event: done") and final["citations"]


@pytest.mark.parametrize("engine", ["loop", "graph"])
def test_agent_calls_three_tools(client, headers, engine):
    device = client.post(
        "/devices",
        headers=headers,
        json={"name": "A", "device_type": "router", "ip": "192.0.2.1"},
    ).json()
    client.post(
        f"/devices/{device['id']}/alarms", headers=headers, json={"level": "critical"}
    )
    upload(client, headers)
    result = client.post(
        "/agent/runs",
        headers=headers,
        json={
            "question": "设备为什么断连",
            "device_id": device["id"],
            "engine": engine,
        },
    )
    assert result.status_code == 201, result.text
    assert [step["tool"] for step in result.json()["steps"]] == [
        "get_device",
        "get_alarm",
        "search_manual",
    ]
    assert all(step["result"]["ok"] for step in result.json()["steps"])


def test_index_failure_not_searchable(client, headers, monkeypatch):
    async def fail(texts):
        raise ProviderError("test embedding failed")

    monkeypatch.setattr(client.app.state.runtime.llm, "embed", fail)
    response = client.post(
        "/knowledge/documents",
        headers=headers,
        files={"file": ("failure.txt", b"hello world", "text/plain")},
    )
    assert response.status_code == 502
    documents = client.get("/knowledge/documents", headers=headers).json()
    assert documents[0]["status"] == "failed"


def test_invalid_input_and_helpers(client, headers):
    assert (
        client.post(
            "/knowledge/documents",
            headers=headers,
            files={"file": ("bad.exe", b"abc", "application/octet-stream")},
        ).status_code
        == 422
    )
    assert split_text("abcdef", 4, 1) == ["abcd", "def"]
    with pytest.raises(ValueError):
        split_text("abc", 3, 3)
    with pytest.raises(ValueError):
        parse_document("blank.txt", b"   ", 100)
    assert bm25("ERR-1007", ["ERR-1007 fault", "other"])[0] > 0
    assert rrf([["a", "b"], ["b"]])["b"] > rrf([["a", "b"], ["b"]])["a"]
    assert validate_citations("fake [C99]", [])[1] == []
    with pytest.raises(ValueError):
        validate_call("shell", "{}", 1)
    with pytest.raises(ValueError):
        validate_call("get_device", '{"device_id":2}', 1)


def test_compatible_provider_contract(client, monkeypatch):
    provider = client.app.state.runtime.llm
    monkeypatch.setattr(provider.settings, "llm_mode", "compatible")
    monkeypatch.setattr(provider.settings, "embedding_mode", "compatible")
    monkeypatch.setattr(provider.settings, "embedding_dimension", 8)
    requests = []

    async def respond(request):
        requests.append(json.loads(request.content))
        if request.url.path.endswith("/embeddings"):
            return httpx.Response(
                200, json={"data": [{"index": 0, "embedding": [0.1] * 8}]}
            )
        return httpx.Response(
            200,
            json={
                "choices": [
                    {"message": {"role": "assistant", "content": "real adapter"}}
                ]
            },
        )

    async def check():
        await provider.client.aclose()
        provider.client = httpx.AsyncClient(transport=httpx.MockTransport(respond))
        assert (await provider.complete([{"role": "user", "content": "hi"}]))[
            "content"
        ] == "real adapter"
        assert len((await provider.embed(["hi"]))[0]) == 8

    asyncio.run(check())
    assert requests[0]["model"] == provider.settings.llm_model
