"""Async client for the OmniRoute API."""

from __future__ import annotations

import asyncio
import time
from typing import Any

import aiohttp
from homeassistant.exceptions import HomeAssistantError

from .const import LOGGER


class OmniRouteError(HomeAssistantError):
    """Base exception for OmniRoute."""


class CannotConnect(OmniRouteError):
    """Error to indicate we cannot connect."""


class InvalidAuth(OmniRouteError):
    """Error to indicate there is invalid auth."""


class ModelNotFoundError(OmniRouteError):
    """Error to indicate requested model is not found."""


class OmniRouteClient:
    """Client for interacting with OmniRoute LLM and Audio proxy."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        api_url: str,
        api_key: str | None = None,
        timeout: float = 60.0,
    ) -> None:
        """Initialize the client."""
        self._session = session
        self._api_key = api_key
        self._timeout = timeout

        clean_url = api_url.rstrip("/")
        if clean_url.endswith("/v1"):
            self._v1_url = clean_url
            self._root_url = clean_url[:-3]
        else:
            self._v1_url = f"{clean_url}/v1"
            self._root_url = clean_url

    @property
    def v1_url(self) -> str:
        """Return the v1 API URL."""
        return self._v1_url

    @property
    def root_url(self) -> str:
        """Return the root URL."""
        return self._root_url

    def _get_headers(self) -> dict[str, str]:
        """Build request headers."""
        headers = {
            "User-Agent": "HomeAssistant-OmniRoute",
            "Accept": "application/json",
        }
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"
        return headers

    async def async_get_models(self) -> list[str]:
        """Fetch list of available model IDs."""
        url = f"{self._v1_url}/models"
        headers = self._get_headers()

        try:
            async with asyncio.timeout(self._timeout):
                async with self._session.get(url, headers=headers) as resp:
                    if resp.status == 401:
                        raise InvalidAuth("Invalid authentication token")
                    if resp.status != 200:
                        raise CannotConnect(
                            f"HTTP {resp.status} while fetching models: {await resp.text()}"
                        )
                    data = await resp.json()
                    model_list: list[dict[str, Any]] = data.get("data", [])
                    return sorted([m["id"] for m in model_list if "id" in m])
        except (TimeoutError, aiohttp.ClientError) as err:
            raise CannotConnect(f"Connection error fetching models: {err}") from err
        except InvalidAuth:
            raise
        except Exception as err:
            raise OmniRouteError(f"Unexpected error fetching models: {err}") from err

    async def async_check_health(self) -> dict[str, Any]:
        """Check gateway health and measure latency."""
        health_url = f"{self._root_url}/api/health"
        headers = self._get_headers()
        start = time.perf_counter()

        try:
            async with asyncio.timeout(10.0):
                async with self._session.get(health_url, headers=headers) as resp:
                    latency_ms = round((time.perf_counter() - start) * 1000, 2)
                    if resp.status == 200:
                        try:
                            health_data = await resp.json()
                            if isinstance(health_data, dict):
                                health_data["latency_ms"] = latency_ms
                                health_data["reachable"] = True
                                return health_data
                        except Exception as exc:
                            LOGGER.debug("Could not parse /api/health JSON: %s", exc)
                        return {
                            "status": "ok",
                            "latency_ms": latency_ms,
                            "reachable": True,
                        }
        except Exception as exc:
            LOGGER.debug("Health endpoint /api/health unavailable: %s", exc)

        # Fallback to /v1/models
        start = time.perf_counter()
        try:
            models = await self.async_get_models()
            latency_ms = round((time.perf_counter() - start) * 1000, 2)
            # Query version from /v1/version if available, or fall back to version header/default
            server_version = "1.0.0"
            try:
                async with asyncio.timeout(5.0):
                    async with self._session.get(
                        f"{self._v1_url}/version", headers=headers
                    ) as v_resp:
                        if v_resp.status == 200:
                            v_data = await v_resp.json()
                            if isinstance(v_data, dict) and "version" in v_data:
                                server_version = str(v_data["version"])
            except Exception:
                pass

            return {
                "status": "ok",
                "latency_ms": latency_ms,
                "reachable": True,
                "models_count": len(models),
                "version": server_version,
            }
        except Exception as err:
            return {
                "status": "offline",
                "latency_ms": None,
                "reachable": False,
                "version": "1.0.0",
                "error": str(err),
            }

    async def async_chat_completion(
        self,
        messages: list[dict[str, Any]],
        model: str,
        temperature: float = 0.7,
        top_p: float = 1.0,
        max_tokens: int | None = None,
        tools: list[dict[str, Any]] | None = None,
        tool_choice: str | dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Send chat completion request."""
        url = f"{self._v1_url}/chat/completions"
        headers = self._get_headers()
        headers["Content-Type"] = "application/json"

        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "top_p": top_p,
        }
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens
        if tools:
            payload["tools"] = tools
        if tool_choice:
            payload["tool_choice"] = tool_choice

        try:
            async with asyncio.timeout(self._timeout):
                async with self._session.post(
                    url, headers=headers, json=payload
                ) as resp:
                    if resp.status == 401:
                        raise InvalidAuth("Invalid authentication token")
                    if resp.status == 404:
                        raise ModelNotFoundError(f"Model '{model}' not found")
                    if resp.status != 200:
                        raise OmniRouteError(
                            f"HTTP {resp.status} during chat completion: {await resp.text()}"
                        )
                    return await resp.json()
        except (TimeoutError, aiohttp.ClientError) as err:
            raise CannotConnect(
                f"Connection error during chat completion: {err}"
            ) from err
        except (InvalidAuth, ModelNotFoundError, OmniRouteError):
            raise
        except Exception as err:
            raise OmniRouteError(
                f"Unexpected error during chat completion: {err}"
            ) from err

    async def async_create_embeddings(
        self,
        model: str,
        input_text: str | list[str],
    ) -> list[list[float]]:
        """Generate text embeddings."""
        url = f"{self._v1_url}/embeddings"
        headers = self._get_headers()
        headers["Content-Type"] = "application/json"

        payload: dict[str, Any] = {
            "model": model,
            "input": input_text,
        }

        try:
            async with asyncio.timeout(self._timeout):
                async with self._session.post(
                    url, headers=headers, json=payload
                ) as resp:
                    if resp.status == 401:
                        raise InvalidAuth("Invalid authentication token")
                    if resp.status != 200:
                        raise OmniRouteError(
                            f"HTTP {resp.status} during embeddings: {await resp.text()}"
                        )
                    data = await resp.json()
                    return [item["embedding"] for item in data.get("data", [])]
        except (TimeoutError, aiohttp.ClientError) as err:
            raise CannotConnect(f"Connection error during embeddings: {err}") from err
        except (InvalidAuth, OmniRouteError):
            raise
        except Exception as err:
            raise OmniRouteError(f"Unexpected error during embeddings: {err}") from err

    async def async_text_to_speech(
        self,
        text: str,
        model: str = "tts-latest",
        voice: str = "Puck",
        response_format: str = "mp3",
        speed: float = 1.0,
    ) -> bytes:
        """Synthesize text into speech audio bytes."""
        url = f"{self._v1_url}/audio/speech"
        headers = self._get_headers()
        headers["Content-Type"] = "application/json"

        payload = {
            "model": model,
            "input": text,
            "voice": voice,
            "response_format": response_format,
            "speed": speed,
        }

        try:
            async with asyncio.timeout(self._timeout):
                async with self._session.post(
                    url, headers=headers, json=payload
                ) as resp:
                    if resp.status == 401:
                        raise InvalidAuth("Invalid authentication token")
                    if resp.status != 200:
                        raise OmniRouteError(
                            f"HTTP {resp.status} during TTS synthesis: {await resp.text()}"
                        )
                    return await resp.read()
        except (TimeoutError, aiohttp.ClientError) as err:
            raise CannotConnect(f"Connection error during TTS: {err}") from err
        except (InvalidAuth, OmniRouteError):
            raise
        except Exception as err:
            raise OmniRouteError(f"Unexpected error during TTS: {err}") from err

    async def async_speech_to_text(
        self,
        audio_data: bytes,
        model: str = "stt-latest",
        language: str | None = None,
        response_format: str = "json",
    ) -> str:
        """Transcribe speech audio bytes to text."""
        url = f"{self._v1_url}/audio/transcriptions"
        headers = self._get_headers()
        headers.pop("Content-Type", None)

        data = aiohttp.FormData()
        data.add_field(
            "file",
            audio_data,
            filename="audio.wav",
            content_type="audio/wav",
        )
        data.add_field("model", model)
        data.add_field("response_format", response_format)
        if language:
            data.add_field("language", language)

        try:
            async with asyncio.timeout(self._timeout):
                async with self._session.post(url, headers=headers, data=data) as resp:
                    if resp.status == 401:
                        raise InvalidAuth("Invalid authentication token")
                    if resp.status != 200:
                        raise OmniRouteError(
                            f"HTTP {resp.status} during transcription: {await resp.text()}"
                        )
                    if response_format == "json":
                        result = await resp.json()
                        return result.get("text", "")
                    return await resp.text()
        except (TimeoutError, aiohttp.ClientError) as err:
            raise CannotConnect(f"Connection error during STT: {err}") from err
        except (InvalidAuth, OmniRouteError):
            raise
        except Exception as err:
            raise OmniRouteError(f"Unexpected error during STT: {err}") from err

    async def async_generate_image(
        self,
        prompt: str,
        model: str = "flux-schnell",
        size: str = "1024x1024",
        quality: str = "standard",
        n: int = 1,
    ) -> list[str]:
        """Generate images matching prompt."""
        url = f"{self._v1_url}/images/generations"
        headers = self._get_headers()
        headers["Content-Type"] = "application/json"

        payload = {
            "model": model,
            "prompt": prompt,
            "size": size,
            "quality": quality,
            "n": n,
        }

        try:
            async with asyncio.timeout(self._timeout):
                async with self._session.post(
                    url, headers=headers, json=payload
                ) as resp:
                    if resp.status == 401:
                        raise InvalidAuth("Invalid authentication token")
                    if resp.status != 200:
                        raise OmniRouteError(
                            f"HTTP {resp.status} during image generation: {await resp.text()}"
                        )
                    data = await resp.json()
                    images = data.get("data", [])
                    return [
                        item.get("url") or item.get("b64_json", "") for item in images
                    ]
        except (TimeoutError, aiohttp.ClientError) as err:
            raise CannotConnect(
                f"Connection error during image generation: {err}"
            ) from err
        except (InvalidAuth, OmniRouteError):
            raise
        except Exception as err:
            raise OmniRouteError(
                f"Unexpected error during image generation: {err}"
            ) from err
