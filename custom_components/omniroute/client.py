"""Async client for the OmniRoute API."""

from __future__ import annotations

import asyncio
import time
from typing import Any

import aiohttp
from homeassistant.exceptions import HomeAssistantError

from .const import DEFAULT_CASCADES, LOGGER


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
        self._compression_enabled = True

        clean_url = api_url.rstrip("/")
        if clean_url.endswith("/v1"):
            self._v1_url = clean_url
            self._root_url = clean_url[:-3]
        else:
            self._v1_url = f"{clean_url}/v1"
            self._root_url = clean_url

    @property
    def compression_enabled(self) -> bool:
        """Return whether prompt token compression is enabled."""
        return self._compression_enabled

    @compression_enabled.setter
    def compression_enabled(self, val: bool) -> None:
        """Set token compression state."""
        self._compression_enabled = bool(val)

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
        headers["x-omniroute-compression"] = (
            "true" if self._compression_enabled else "false"
        )
        return headers

    async def async_get_cascades(self) -> list[str]:
        """Fetch active cascades dynamically from OmniRoute /api/combos."""
        url = f"{self._root_url}/api/combos"
        headers = self._get_headers()

        try:
            async with asyncio.timeout(self._timeout):
                async with self._session.get(url, headers=headers) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        combos = (
                            data.get("combos", [])
                            if isinstance(data, dict)
                            else (data if isinstance(data, list) else [])
                        )
                        names = [
                            c["name"]
                            for c in combos
                            if isinstance(c, dict)
                            and "name" in c
                            and not c.get("isHidden", False)
                        ]
                        if names:
                            return names
        except Exception as exc:
            LOGGER.debug("Could not fetch combos from /api/combos: %s", exc)
        return list(DEFAULT_CASCADES)

    async def async_get_models(self) -> list[str]:
        """Fetch available models from OmniRoute."""
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
                    # Filter models to only include those configured and active
                    available_models = [
                        m["id"]
                        for m in model_list
                        if "id" in m and not m.get("id", "").startswith("meta-")
                    ]
                    return sorted(available_models)
        except (TimeoutError, aiohttp.ClientError) as err:
            raise CannotConnect(f"Connection error fetching models: {err}") from err
        except InvalidAuth:
            raise
        except Exception as err:
            raise OmniRouteError(f"Unexpected error fetching models: {err}") from err

    async def async_get_quotas(self) -> dict[str, Any]:
        """Fetch provider quotas (AGH, GH, GHE, Jules, Gemini, etc.)."""
        url = f"{self._root_url}/api/quotas"
        headers = self._get_headers()

        try:
            async with asyncio.timeout(10.0):
                async with self._session.get(url, headers=headers) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if isinstance(data, dict):
                            return data
        except Exception as exc:
            LOGGER.debug("Quotas endpoint unavailable: %s", exc)

        # Fallback empty quotas structure
        return {"quotas": {}, "providers": {}}

    async def _async_get_server_version(self) -> str | None:
        """Attempt to fetch version from OmniRoute server endpoints."""
        headers = self._get_headers()
        for endpoint in (
            f"{self._root_url}/api/system/version",
            f"{self._root_url}/api/version",
        ):
            try:
                async with asyncio.timeout(3.0):
                    async with self._session.get(endpoint, headers=headers) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            if isinstance(data, dict):
                                val = data.get("version") or data.get("current")
                                if val:
                                    return str(val)
            except Exception:
                continue
        return None

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
                                if "version" not in health_data:
                                    s_ver = await self._async_get_server_version()
                                    if s_ver:
                                        health_data["version"] = s_ver
                                return health_data
                        except Exception as exc:
                            LOGGER.debug("Could not parse /api/health JSON: %s", exc)
                        s_ver = await self._async_get_server_version()
                        return {
                            "status": "ok",
                            "latency_ms": latency_ms,
                            "reachable": True,
                            "version": s_ver,
                        }
        except Exception as exc:
            LOGGER.debug("Health endpoint /api/health unavailable: %s", exc)

        # Fallback to /v1/models
        start = time.perf_counter()
        try:
            models = await self.async_get_models()
            latency_ms = round((time.perf_counter() - start) * 1000, 2)
            server_version = await self._async_get_server_version()

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
                "version": None,
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

    async def async_flush_cache(self) -> bool:
        """Clear route and model resolution caches in OmniRoute."""
        url = f"{self._root_url}/api/cli-tools/flush-cache"
        headers = self._get_headers()
        try:
            async with asyncio.timeout(10.0):
                async with self._session.post(url, headers=headers) as resp:
                    if resp.status in (200, 204):
                        return True
                    fallback_url = f"{self._root_url}/api/cache/clear"
                    async with self._session.post(
                        fallback_url, headers=headers
                    ) as fb_resp:
                        return fb_resp.status in (200, 204)
        except Exception as exc:
            LOGGER.debug("Cache flush endpoint failed: %s", exc)
            return False

    async def async_generate_embedding(
        self,
        input_text: str | list[str],
        model: str = "text-embedding-3-small",
    ) -> list[float] | list[list[float]]:
        """Generate text vector embeddings."""
        url = f"{self._v1_url}/embeddings"
        headers = self._get_headers()
        headers["Content-Type"] = "application/json"
        payload = {"model": model, "input": input_text}

        try:
            async with asyncio.timeout(self._timeout):
                async with self._session.post(
                    url, headers=headers, json=payload
                ) as resp:
                    if resp.status == 401:
                        raise InvalidAuth("Invalid authentication token")
                    if resp.status != 200:
                        raise OmniRouteError(
                            f"HTTP {resp.status} during embedding: {await resp.text()}"
                        )
                    data = await resp.json()
                    res_data = data.get("data", [])
                    if isinstance(input_text, list):
                        return [item.get("embedding", []) for item in res_data]
                    if res_data:
                        return res_data[0].get("embedding", [])
                    return []
        except (TimeoutError, aiohttp.ClientError) as err:
            raise CannotConnect(f"Connection error during embedding: {err}") from err
        except (InvalidAuth, OmniRouteError):
            raise
        except Exception as err:
            raise OmniRouteError(f"Unexpected error during embedding: {err}") from err

    async def async_analyze_camera_image(
        self,
        image_bytes: bytes,
        prompt: str = "Describe in detail what you see in this security camera snapshot.",
        model: str | None = None,
    ) -> dict[str, Any]:
        """Analyze a camera image using multimodal vision."""
        import base64

        b64_image = base64.b64encode(image_bytes).decode("ascii")
        data_uri = f"data:image/jpeg;base64,{b64_image}"
        chosen_model = model or "coding-cascade"

        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": data_uri}},
                ],
            }
        ]

        start = time.perf_counter()
        resp = await self.async_chat_completion(messages=messages, model=chosen_model)
        latency_ms = round((time.perf_counter() - start) * 1000, 2)
        choices = resp.get("choices", [])
        content = ""
        if choices and "message" in choices[0]:
            content = str(choices[0]["message"].get("content", ""))

        return {
            "response": content,
            "model": chosen_model,
            "latency_ms": latency_ms,
            "usage": resp.get("usage", {}),
        }
