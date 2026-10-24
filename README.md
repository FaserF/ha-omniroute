<p align="center">
  <img src="https://raw.githubusercontent.com/FaserF/ha-omniroute/main/brand/logo.png" alt="OmniRoute Logo" width="360">
</p>

# OmniRoute for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/default)
[![CI](https://github.com/FaserF/ha-omniroute/actions/workflows/ci-orchestrator.yml/badge.svg)](https://github.com/FaserF/ha-omniroute/actions)
[![Documentation](https://img.shields.io/badge/docs-GitHub_Pages-blue.svg)](https://faserf.github.io/ha-omniroute/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Home Assistant custom integration for **OmniRoute AI Gateway & Router**. Seamlessly connects Home Assistant to your local or remote OmniRoute LLM and Audio proxy gateway, providing unified access to voice pipelines, multimodal vision, AI tasks, automated smart home suggestions, image generation, speech synthesis, embeddings, and live provider quota telemetry.

---

## 🌟 Key Features & Platforms

### 1. 🗣️ Assist Voice & Conversation Agent (`conversation.omniroute_*`)
- **Native LLM Tool / Intent Calling**: Control lights, query states, trigger scripts, and run custom intents with Home Assistant's built-in tool registry.
- **Cascading Failover**: Route through intelligent cascades (`chat-cascade`, `fast-cascade`, `coding-cascade`) that automatically failover across Google Gemini, Anthropic Claude, OpenAI, DeepSeek, and Groq.
- **Configurable Parameters**: Custom system prompt with Jinja2 support, temperature, top_p, and token ceilings.

### 2. 🧠 Native Generative AI Task Engine (`ai_task.omniroute_*`)
- **Home Assistant AI Suggestions**: Fully complies with Home Assistant's AI Task specifications (`GENERATE_DATA`, `GENERATE_IMAGE`, `SUPPORT_ATTACHMENTS`).
- Selectable under Home Assistant **Settings > Voice Assistants > AI Suggestions** (`ai_task.omniroute_gateway_task_engine`) to power native automation naming and blueprint suggestions.

### 3. 🤖 AI Automation Suggester (`sensor.omniroute_automation_suggestions` & `omniroute.suggest_automations`)
- **Context-Aware Smart Home Ideas**: Scans your real entities, domains, and areas to generate tailored, ready-to-paste Home Assistant YAML automations.
- **Persistent Notifications**: Dispatches formatted automation alerts directly into Home Assistant notifications.
- **Sensor Attributes**: Exposes the suggested description, YAML code block, and metadata for easy display on Lovelace dashboard Markdown cards.
- **Zero-Dependency Migration**: Directly replaces standalone integrations like `ai_automation_suggester`.

### 4. 👁️ Multimodal Camera Vision (`omniroute.analyze_camera`)
- **Instant Snapshots**: Grabs still frames from any Home Assistant camera (`camera.front_door`, `camera.driveway`).
- **Vision Model Inspection**: Feeds snapshots into multimodal vision models to detect package deliveries, license plates, unknown persons, or open garage doors.
- Returns structured responses directly into automation variables for Telegram or push notifications.

### 5. 🔊 Text-to-Speech (TTS) (`tts.omniroute`)
- High-quality speech synthesis via OmniRoute's audio synthesis endpoints.
- Voice switching across natural profiles: `Charon`, `Puck`, `Aoede`, `Kore`, `Fenrir`, `Leda`, `Orus`, and `Zephyr`.
- Adjustable speed and audio formats (`mp3`, `opus`, `aac`, `flac`, `wav`).

### 6. 🎙️ Speech-to-Text (STT) (`stt.omniroute`)
- Fast, multi-lingual audio transcription for Assist pipelines and voice satellites.
- Supports raw WAV streams with automatic sample rate handling.

### 7. 🎛️ Dynamic Selectors (`select.omniroute_*`)
- **`select.omniroute_active_cascade`**: Change active model cascade (`chat-cascade`, `fast-cascade`, `coding-cascade`, or custom model IDs) on the fly via dashboards or automations without editing config entries.
- **`select.omniroute_tts_voice`**: Switch active voice persona dynamically.

### 8. ⚡ Token Optimization & Cache Controls (`switch` & `button`)
- **`switch.omniroute_token_compression`**: Toggle OmniRoute's RTK / Caveman token compression headers (15%–95% prompt token reduction).
- **`button.omniroute_flush_cache`**: Instant flush of route resolutions and model cache without container restarts.

### 9. 🎨 AI Image Generation & Display (`image.omniroute_*` & `omniroute.generate_image`)
- Generate pictures using models like `flux-schnell` or SD.
- **`image.omniroute_latest_generated`**: Lovelace entity that automatically updates with the latest generated image.

### 10. 📊 Quota Telemetry & Provider Monitoring (`sensor` & `binary_sensor`)
- **Per-Provider Health Binary Sensors**: Individual diagnostic sensors for Google Gemini, Anthropic Claude, OpenAI, DeepSeek, and Groq to flag HTTP 429 rate limits or provider downtime.
- **Analytics & Quota Sensors**:
  - `sensor.omniroute_daily_tokens_consumed`: Real-time daily token counter.
  - `sensor.omniroute_daily_estimated_cost`: Estimated daily spend in USD.
  - `sensor.omniroute_quota_reset_countdown`: Time until quota budgets refresh.
  - `sensor.omniroute_latency_ms`: Roundtrip gateway ping latency.
  - `sensor.omniroute_active_cascades` & `sensor.omniroute_models_registered`.

### 11. 🧭 Vector Embeddings (`omniroute.generate_embedding`)
- Access `/v1/embeddings` directly in scripts for RAG, smart home knowledge retrieval, or similarity matching.

---

## 🚀 Installation

### Option 1: HACS (Recommended)

1. Open **HACS** in Home Assistant.
2. Go to **Integrations**, click the three dots in the top right corner, and select **Custom repositories**.
3. Add `https://github.com/FaserF/ha-omniroute` with category **Integration**.
4. Search for **OmniRoute**, click **Download**, and restart Home Assistant.

### Option 2: Manual Installation

1. Download the latest release from the [Releases page](https://github.com/FaserF/ha-omniroute/releases).
2. Copy `custom_components/omniroute/` to your Home Assistant `<config_dir>/custom_components/omniroute/`.
3. Restart Home Assistant.

---

## ⚙️ Configuration

1. In Home Assistant, go to **Settings > Devices & Services > Add Integration**.
2. Search for **OmniRoute**.
3. Fill in the connection parameters:
   - **API URL**: e.g. `http://omniroute:20128/v1` or `https://omniroute.yourdomain.com/v1`.
   - **API Key**: Bearer token (optional if authentication is disabled on the gateway).

### Options Flow Settings

Click **Configure** on the OmniRoute integration card:
- **Chat / Conversation Model**: Default model for Assist voice agent (e.g. `chat-cascade`).
- **AI Task Model**: Default model for AI Tasks (e.g. `coding-cascade`).
- **System Prompts**: Customizable prompts with Jinja2 template support.
- **Temperature & Max Tokens**: Adjust sampling creativity and response limits.
- **TTS Model & Default Voice**: Voice selection and default output formats.

---

## 🛠️ Service & Action Reference

### `omniroute.suggest_automations`
Scans Home Assistant entities and creates context-aware automation suggestions with complete YAML code.

```yaml
action: omniroute.suggest_automations
data:
  domains:
    - light
    - binary_sensor
    - climate
  entity_limit: 30
  custom_prompt: "Focus on energy conservation when no one is in the room."
  model: "coding-cascade"
  send_notification: true
```

### `omniroute.analyze_camera`
Takes a live snapshot from a camera entity and analyzes it using multimodal vision.

```yaml
action: omniroute.analyze_camera
data:
  camera_entity_id: camera.front_door
  prompt: "Is there a package on the porch or a courier at the door?"
  model: "coding-cascade"
response_variable: camera_result
```

### `omniroute.generate_image`
Generates an image and updates `image.omniroute_latest_generated`.

```yaml
action: omniroute.generate_image
data:
  prompt: "A cozy modern living room with warm smart lighting at dusk"
  model: "flux-schnell"
  size: "1024x1024"
```

### `omniroute.execute_ai_task`
Run arbitrary prompts or structured data generation in scripts.

```yaml
action: omniroute.execute_ai_task
data:
  prompt: "Categorize the following events into security alerts vs routine: {{ events }}"
  model: "coding-cascade"
```

### `omniroute.generate_embedding`
Generates vector representations for text.

```yaml
action: omniroute.generate_embedding
data:
  text: "Living room ceiling light dimming rule"
  model: "text-embedding-3-small"
response_variable: embedding_result
```

### `omniroute.flush_cache`
Clears route caches and triggers a coordinator refresh.

```yaml
action: omniroute.flush_cache
```

---

## ⚠️ Limitations & Prerequisites

- **Network Connectivity**: Home Assistant must be able to reach the OmniRoute endpoint over HTTP/HTTPS.
- **Provider Quotas**: Underlying AI providers (OpenAI, Gemini, Anthropic, etc.) must have valid API keys and active quotas configured inside your OmniRoute gateway instance.
- **Camera Snapshots**: Multimodal camera inspection requires camera entities that support `camera.async_get_image` (standard on Home Assistant camera integrations).
- **Token Compression**: `switch.omniroute_token_compression` sends `x-omniroute-compression` headers; effective token savings require the compression middleware to be enabled on your OmniRoute gateway server.
- **Home Assistant AI Suggestions**: Requires Home Assistant 2024.12+ for native `ai_task` entity selection under Voice Assistants.

---

## 🔄 Migrating from `ai_automation_suggester`

If you were using the legacy `ai_automation_suggester` custom component:
1. `ha-omniroute` includes the `omniroute.suggest_automations` action and `sensor.omniroute_automation_suggestions` entity built-in.
2. In your automations, replace service call `ai_automation_suggester.generate_suggestions` with `omniroute.suggest_automations`.
3. In dashboard cards, replace `sensor.ai_automation_suggestions_*` with `sensor.omniroute_automation_suggestions`.
4. Delete the old `ai_automation_suggester` integration entry in **Settings > Devices & Services** and uninstall it from HACS.

---

## 🧩 Troubleshooting

| Symptom | Cause | Solution |
|---|---|---|
| Gateway unreachable / `connected` off | Wrong API URL or network firewall | Verify the URL in integration options and ensure port 20128 is accessible. |
| Assist tool calling not executing | Tools permission disabled | Ensure "Expose entities to Assist" and "Enable Home Assistant Tool Calling" are checked. |
| AI Task missing from AI Suggestions dropdown | HA version or feature bitmask | Ensure Home Assistant is updated to 2024.12+ and OmniRoute version is updated. |
| Provider health binary sensor is off | Upstream provider 429 or outage | Check OmniRoute gateway logs and provider quotas on your OmniRoute dashboard. |
| Camera snapshot failed | Camera offline or format error | Test whether `camera.snapshot` works on that entity in Developer Tools. |

---


## 🔌 Recommended Hardware & Ecosystem Links

| Device / Service | Integration Use Case | Link |
| :--- | :--- | :--- |
| **OpenWrt-kompatible Wi-Fi 6/7 Router & Gateways** | Native Ubus/RPC, WireGuard, SQM & Präsenz-Erkennung in Home Assistant | [Offizielle Geräte-Seite →](https://fabiseitz.de/go/ha-router) |
| **Home Assistant Green / Yellow Zentrale** | Dedizierter, stromsparender 24/7 Smart-Home-Host | [Offizielle Geräte-Seite →](https://fabiseitz.de/go/ha-hardware) |

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
