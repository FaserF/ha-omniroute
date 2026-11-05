<p align="center">
  <img src="https://raw.githubusercontent.com/FaserF/ha-omniroute/main/brand/logo.png" alt="OmniRoute Logo" width="360">
</p>

# OmniRoute (for Home Assistant)

[![GitHub Release](https://img.shields.io/github/release/FaserF/ha-omniroute.svg?style=flat-square)](https://github.com/FaserF/ha-omniroute/releases)
[![Downloads (Current release)](https://img.shields.io/github/downloads/FaserF/ha-omniroute/latest/omniroute.zip?label=Downloads%20(Current%20release)&style=flat-square)](https://github.com/FaserF/ha-omniroute/releases)
[![License](https://img.shields.io/github/license/FaserF/ha-omniroute.svg?style=flat-square)](LICENSE)
[![Home Assistant Marketplace](https://img.shields.io/badge/HA-Marketplace-blue.svg?style=flat-square)](https://my.home-assistant.io/redirect/marketplace_repository/?repository=FaserF/ha-omniroute&category=integration)
[![Python 3.14 | 3.15](https://img.shields.io/badge/python-3.14%20%7C%203.15-blue.svg?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![Documentation](https://img.shields.io/badge/docs-GitHub_Pages-blue.svg?style=flat-square)](https://faserf.github.io/ha-omniroute/)
[![Add to Home Assistant](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=omniroute)
[![CI Orchestrator](https://github.com/FaserF/ha-omniroute/actions/workflows/ci-orchestrator.yml/badge.svg)](https://github.com/FaserF/ha-omniroute/actions/workflows/ci-orchestrator.yml)

Home Assistant custom integration for **OmniRoute AI Gateway & Router**. Seamlessly connects Home Assistant to your local or remote OmniRoute LLM and Audio proxy gateway, providing unified access to voice pipelines, multimodal vision, AI tasks, automated smart home suggestions, image generation, speech synthesis, embeddings, and live provider quota telemetry.

## 🧭 Quick Links

| | | | |
| :--- | :--- | :--- | :--- |
| [📖 Documentation Site](https://faserf.github.io/ha-omniroute/) | [✨ Features](#-key-features--platforms) | [📦 Installation](#-installation) | [⚙️ Configuration](#️-configuration) |
| [🛡️ Security](SECURITY.md) | [🛠️ Services](#️-service--action-reference) | [⚠️ Limitations](#️-limitations--prerequisites) | [🔄 Migration](#-migrating-from-ai_automation_suggester) |
| [❓ Troubleshooting](#-troubleshooting) | [🧑‍💻 Development](#-development) | [❤️ Support](#️-support-this-project) | [📄 License](#-license) |

## ❤️ Support This Project

> I maintain this integration in my **free time alongside my regular job** — bug hunting, new features, testing on real devices. Test hardware costs money, and every donation helps me stay independent and dedicate more time to open-source work.
>
> **This project is and will always remain 100% free.** There are no "Premium Upgrades", paid features, or subscriptions. Every feature is available to everyone.
>
> Donations are completely voluntary — but the more support I receive, the less I depend on other income sources and the more time I can realistically invest into these projects. 💪

<div align="center">

[![GitHub Sponsors](https://img.shields.io/badge/Sponsor%20on-GitHub-%23EA4AAA?style=for-the-badge&logo=github-sponsors&logoColor=white)](https://github.com/sponsors/FaserF)&nbsp;&nbsp;
[![PayPal](https://img.shields.io/badge/Donate%20via-PayPal-%2300457C?style=for-the-badge&logo=paypal&logoColor=white)](https://paypal.me/FaserF)

</div>

---

## 🔌 Recommended Hardware & Ecosystem Links

| Device / Service | Integration Use Case | Link |
| :--- | :--- | :--- |
| **OpenWrt-compatible Wi-Fi 6/7 Routers & Gateways** | Native Ubus/RPC, WireGuard, SQM & presence detection in Home Assistant | [Official Device Page →](https://fabiseitz.de/go/ha-router) |
| **Home Assistant Green / Yellow Hub** | Dedicated, power-efficient 24/7 smart home appliance | [Official Device Page →](https://fabiseitz.de/go/ha-hardware) |

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

## 📦 Installation

### Home Assistant Marketplace (formerly HACS) (Recommended)

This integration is fully compatible with the official **Home Assistant Marketplace** (native in Home Assistant 2026.11+) and classic HACS setups.

[![Open your Home Assistant instance and open the repository in the Marketplace.](https://my.home-assistant.io/badges/marketplace_repository.svg)](https://my.home-assistant.io/redirect/marketplace_repository/?repository=FaserF/ha-omniroute&category=integration)

> [!NOTE]
> This integration is distributed as a custom integration repository. You can add it directly to Home Assistant using the one-click button above or manually following the steps below.

#### Native Marketplace (Home Assistant 2026.11+)
1. Click the **Open Home Assistant** button above, or navigate to **Marketplace** (or **Settings > Integrations > Marketplace**) in your Home Assistant sidebar.
2. Open the overflow menu (`⋮` three dots) in the top-right corner and select **Custom repositories**.
3. Enter `https://github.com/FaserF/ha-omniroute` (or `FaserF/ha-omniroute`) with category **Integration** and click **Add**.
4. Search for **OmniRoute** in the Marketplace catalog.
5. Click **Download** / **Install** and restart Home Assistant when prompted.

#### Legacy HACS Fallback (Older Home Assistant versions)
1. Open **HACS** in Home Assistant.
2. Go to **Integrations**, click the three dots in the top right corner, and select **Custom repositories**.
3. Add `https://github.com/FaserF/ha-omniroute` with category **Integration**.
4. Search for **OmniRoute**, click **Download**, and restart Home Assistant.

### Manual Installation

1. Download the latest `omniroute.zip` release archive from the [Releases page](https://github.com/FaserF/ha-omniroute/releases).
2. Extract the archive or copy the `custom_components/omniroute/` folder into your Home Assistant `<config_dir>/custom_components/omniroute/`.
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

- **Python 3.14 & 3.15 Only**: Built strictly for modern Python 3.14+ (Home Assistant 2026.11+). Python 3.13 and older are not supported.
- **Home Assistant 2026.11+**: Designed for Home Assistant 2026.11 or newer (native Marketplace and modern AI Task specifications).
- **Network Connectivity**: Home Assistant must be able to reach the OmniRoute endpoint over HTTP/HTTPS.
- **Provider Quotas**: Underlying AI providers (OpenAI, Gemini, Anthropic Claude, DeepSeek, Groq, etc.) must have valid API keys and active quotas configured inside your OmniRoute gateway instance.
- **Camera Snapshots**: Multimodal camera inspection requires camera entities that support `camera.async_get_image` (standard on Home Assistant camera integrations).
- **Token Compression**: `switch.omniroute_token_compression` sends `x-omniroute-compression` headers; effective token savings require the compression middleware to be enabled on your OmniRoute gateway server.
- **Home Assistant AI Suggestions**: Requires Home Assistant 2024.12+ for native `ai_task` entity selection under Voice Assistants.

---

## 🔄 Migrating from `ai_automation_suggester`

If you were using the legacy `ai_automation_suggester` custom component:
1. `ha-omniroute` includes the `omniroute.suggest_automations` action and `sensor.omniroute_automation_suggestions` entity built-in.
2. In your automations, replace service call `ai_automation_suggester.generate_suggestions` with `omniroute.suggest_automations`.
3. In dashboard cards, replace `sensor.ai_automation_suggestions_*` with `sensor.omniroute_automation_suggestions`.
4. Delete the old `ai_automation_suggester` integration entry in **Settings > Devices & Services** and uninstall it from the Marketplace.

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

## 🧑‍💻 Development

This project uses modern Python development tools:
- `ruff` for linting and formatting
- `mypy` for static typing
- `pytest` for unit testing

### Setup

```bash
uv pip install --system -e ".[test]"
```

### Pre-commit Checks

Before committing, run tests and linters:
```bash
ruff format .
ruff check --fix .
mypy custom_components/omniroute tests
pytest
```

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
