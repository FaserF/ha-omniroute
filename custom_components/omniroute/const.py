"""Constants for the OmniRoute integration."""

from __future__ import annotations

import logging
from typing import Final

from homeassistant.const import Platform

DOMAIN: Final = "omniroute"
LOGGER: Final = logging.getLogger(__package__)

DEFAULT_NAME: Final = "OmniRoute"
DEFAULT_API_URL: Final = "http://omniroute:20128/v1"
DEFAULT_MANUFACTURER: Final = "OmniRoute"
DEFAULT_MODEL: Final = "AI Gateway & Router"

DATA_COORDINATOR: Final = "coordinator"
DATA_CLIENT: Final = "client"

# Cascade definitions (dynamically populated from server combos)
DEFAULT_CASCADES: Final[list[str]] = []

# Configuration keys
CONF_API_URL: Final = "api_url"
CONF_API_KEY: Final = "api_key"

# Conversation options
CONF_CHAT_MODEL: Final = "chat_model"
CONF_PROMPT: Final = "prompt"
CONF_TEMPERATURE: Final = "temperature"
CONF_TOP_P: Final = "top_p"
CONF_MAX_TOKENS: Final = "max_tokens"
CONF_LLM_HASS_API: Final = "llm_hass_api"

# AI Task options
CONF_AI_TASK_MODEL: Final = "ai_task_model"
CONF_AI_TASK_PROMPT: Final = "ai_task_prompt"
CONF_AI_TASK_TEMPERATURE: Final = "ai_task_temperature"
CONF_AI_TASK_MAX_TOKENS: Final = "ai_task_max_tokens"
CONF_SCAN_INTERVAL: Final = "scan_interval"

# Default values
DEFAULT_SCAN_INTERVAL: Final = 180  # seconds (3 minutes)

# TTS options
CONF_TTS_MODEL: Final = "tts_model"
CONF_TTS_VOICE: Final = "tts_voice"
CONF_TTS_SPEED: Final = "tts_speed"
CONF_TTS_FORMAT: Final = "tts_format"

# STT options
CONF_STT_MODEL: Final = "stt_model"
CONF_STT_LANGUAGE: Final = "stt_language"
CONF_STT_FORMAT: Final = "stt_format"

# Default values
DEFAULT_CHAT_MODEL: Final = "default"
DEFAULT_AI_TASK_MODEL: Final = "default"
DEFAULT_FAST_MODEL: Final = "default"
DEFAULT_TTS_MODEL: Final = "tts-latest"
DEFAULT_TTS_VOICE: Final = "Puck"
DEFAULT_TTS_SPEED: Final = 1.0
DEFAULT_TTS_FORMAT: Final = "mp3"

DEFAULT_STT_MODEL: Final = "stt-latest"
DEFAULT_STT_LANGUAGE: Final = "en"
DEFAULT_STT_FORMAT: Final = "wav"

DEFAULT_TEMPERATURE: Final = 0.7
DEFAULT_TOP_P: Final = 1.0
DEFAULT_MAX_TOKENS: Final = 1000
DEFAULT_AI_TASK_TEMPERATURE: Final = 0.2
DEFAULT_AI_TASK_MAX_TOKENS: Final = 2048

DEFAULT_PROMPT: Final = (
    "You are a helpful voice assistant for Home Assistant. "
    "Answer concisely and use the provided tools to interact with devices."
)
DEFAULT_AI_TASK_PROMPT: Final = (
    "You are an AI task specialist for Home Assistant. "
    "Execute reasoning, process context and multimodal inputs, and return structured outputs."
)

CONF_TOKEN_COMPRESSION: Final = "token_compression"
DEFAULT_TOKEN_COMPRESSION: Final = True

DEFAULT_TTS_VOICES: Final[list[str]] = [
    "Charon",
    "Puck",
    "Aoede",
    "Kore",
    "Fenrir",
    "Leda",
    "Orus",
    "Zephyr",
]

# Supported platforms
PLATFORM_AI_TASK: Final = "ai_task"
PLATFORMS: Final[list[Platform | str]] = [
    Platform.CONVERSATION,
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.BUTTON,
    Platform.TTS,
    Platform.STT,
    Platform.SELECT,
    Platform.SWITCH,
    Platform.IMAGE,
    PLATFORM_AI_TASK,
]

# Supported TTS Formats
SUPPORTED_TTS_FORMATS: Final[list[str]] = ["mp3", "opus", "aac", "flac", "wav"]

# Services
SERVICE_EXECUTE_AI_TASK: Final = "execute_ai_task"
SERVICE_GENERATE_IMAGE: Final = "generate_image"
SERVICE_REFRESH_MODELS: Final = "refresh_models"
SERVICE_ANALYZE_CAMERA: Final = "analyze_camera"
SERVICE_GENERATE_EMBEDDING: Final = "generate_embedding"
SERVICE_FLUSH_CACHE: Final = "flush_cache"
SERVICE_SUGGEST_AUTOMATIONS: Final = "suggest_automations"
DATA_SUGGESTIONS_SENSOR: Final = "suggestions_sensor"


# Max tool calling iterations in conversation agent
MAX_TOOL_ITERATIONS: Final = 10

# Attributes
ATTR_LATENCY_MS: Final = "latency_ms"
ATTR_ACTIVE_MODELS: Final = "active_models"
ATTR_TOTAL_MODELS: Final = "total_models"
ATTR_CASCADE_STATUS: Final = "cascade_status"
ATTR_PROMPT_TOKENS: Final = "prompt_tokens"
ATTR_COMPLETION_TOKENS: Final = "completion_tokens"
ATTR_TOTAL_TOKENS: Final = "total_tokens"
