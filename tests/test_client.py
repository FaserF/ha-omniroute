"""Test OmniRoute async API client."""

from unittest.mock import AsyncMock, MagicMock

import aiohttp
import pytest

from custom_components.omniroute.client import (
    InvalidAuth,
    ModelNotFoundError,
    OmniRouteClient,
)


@pytest.fixture
def mock_session():
    """Mock aiohttp ClientSession."""
    session = MagicMock(spec=aiohttp.ClientSession)
    return session


def create_response_mock(status=200, json_data=None, text_data="", read_data=b""):
    """Helper to mock aiohttp response context manager."""
    resp = MagicMock()
    resp.status = status
    resp.json = AsyncMock(return_value=json_data)
    resp.text = AsyncMock(return_value=text_data)
    resp.read = AsyncMock(return_value=read_data)

    cm = AsyncMock()
    cm.__aenter__.return_value = resp
    cm.__aexit__.return_value = None
    return cm


@pytest.mark.asyncio
async def test_client_urls():
    """Test URL normalization in client."""
    session = MagicMock()
    c1 = OmniRouteClient(session, "http://localhost:20128/v1/")
    assert c1.v1_url == "http://localhost:20128/v1"
    assert c1.root_url == "http://localhost:20128"

    c2 = OmniRouteClient(session, "http://localhost:20128")
    assert c2.v1_url == "http://localhost:20128/v1"
    assert c2.root_url == "http://localhost:20128"


@pytest.mark.asyncio
async def test_get_models_success(mock_session):
    """Test fetching available models."""
    mock_session.get.return_value = create_response_mock(
        200, json_data={"data": [{"id": "model-b"}, {"id": "model-a"}]}
    )
    client = OmniRouteClient(
        mock_session, "http://localhost:20128/v1", api_key="secret"
    )
    models = await client.async_get_models()
    assert models == ["model-a", "model-b"]


@pytest.mark.asyncio
async def test_get_models_auth_failure(mock_session):
    """Test auth failure when fetching models."""
    mock_session.get.return_value = create_response_mock(401, text_data="Unauthorized")
    client = OmniRouteClient(mock_session, "http://localhost:20128/v1")
    with pytest.raises(InvalidAuth):
        await client.async_get_models()


@pytest.mark.asyncio
async def test_check_health(mock_session):
    """Test gateway health checking."""
    mock_session.get.return_value = create_response_mock(
        200, json_data={"status": "ok", "uptime": 1234}
    )
    client = OmniRouteClient(mock_session, "http://localhost:20128")
    health = await client.async_check_health()
    assert health["reachable"] is True
    assert health["status"] == "ok"
    assert "latency_ms" in health


@pytest.mark.asyncio
async def test_chat_completion_success(mock_session):
    """Test chat completion call."""
    mock_session.post.return_value = create_response_mock(
        200,
        json_data={
            "choices": [{"message": {"content": "Hello smart home!"}}],
            "usage": {"total_tokens": 15},
        },
    )
    client = OmniRouteClient(mock_session, "http://localhost:20128/v1")
    res = await client.async_chat_completion(
        messages=[{"role": "user", "content": "Hi"}],
        model="chat-cascade",
    )
    assert res["choices"][0]["message"]["content"] == "Hello smart home!"


@pytest.mark.asyncio
async def test_chat_completion_not_found(mock_session):
    """Test 404 model not found."""
    mock_session.post.return_value = create_response_mock(
        404, text_data="Model not found"
    )
    client = OmniRouteClient(mock_session, "http://localhost:20128/v1")
    with pytest.raises(ModelNotFoundError):
        await client.async_chat_completion(
            messages=[{"role": "user", "content": "Hi"}],
            model="missing-model",
        )


@pytest.mark.asyncio
async def test_embeddings(mock_session):
    """Test embeddings API call."""
    mock_session.post.return_value = create_response_mock(
        200,
        json_data={"data": [{"embedding": [0.1, 0.2, 0.3]}]},
    )
    client = OmniRouteClient(mock_session, "http://localhost:20128/v1")
    embeddings = await client.async_create_embeddings(
        model="text-embedding-3-small",
        input_text="Home Assistant rules",
    )
    assert embeddings == [[0.1, 0.2, 0.3]]


@pytest.mark.asyncio
async def test_text_to_speech(mock_session):
    """Test text to speech synthesis."""
    mock_session.post.return_value = create_response_mock(200, read_data=b"AUDIO_BYTES")
    client = OmniRouteClient(mock_session, "http://localhost:20128/v1")
    audio = await client.async_text_to_speech("Turn on the living room light")
    assert audio == b"AUDIO_BYTES"


@pytest.mark.asyncio
async def test_speech_to_text(mock_session):
    """Test speech to text transcription."""
    mock_session.post.return_value = create_response_mock(
        200, json_data={"text": "Turn off lights"}
    )
    client = OmniRouteClient(mock_session, "http://localhost:20128/v1")
    text = await client.async_speech_to_text(b"AUDIO_DATA")
    assert text == "Turn off lights"


@pytest.mark.asyncio
async def test_generate_image(mock_session):
    """Test image generation."""
    mock_session.post.return_value = create_response_mock(
        200,
        json_data={"data": [{"url": "http://img.png"}]},
    )
    client = OmniRouteClient(mock_session, "http://localhost:20128/v1")
    images = await client.async_generate_image("Modern interior")
    assert images == ["http://img.png"]
