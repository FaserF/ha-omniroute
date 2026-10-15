<p align="center">
  <img src="https://raw.githubusercontent.com/FaserF/ha-omniroute/main/brand/logo.png" alt="OmniRoute Logo" width="360">
</p>

# OmniRoute for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/default)
[![CI](https://github.com/FaserF/ha-omniroute/actions/workflows/ci-orchestrator.yml/badge.svg)](https://github.com/FaserF/ha-omniroute/actions)
[![Documentation](https://img.shields.io/badge/docs-GitHub_Pages-blue.svg)](https://faserf.github.io/ha-omniroute/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Home Assistant custom integration for **OmniRoute AI Gateway & Router**. Seamlessly connect Home Assistant to your local or remote OmniRoute LLM and Audio proxy gateway.

---

## 🌟 Key Features

- **Assist Conversation Agent (`conversation.omniroute_*`)**:
  - Full voice assistant pipeline support.
  - Native Home Assistant LLM Tool / Intent Calling (turn devices on/off, query sensors, execute automations).
  - Configurable system prompts, model cascades (`chat-cascade`, `fast-cascade`, etc.), temperature, top_p, and token budgets.
- **Generative AI Task Engine (`ai_task.omniroute_*`)**:
  - Dedicated AI task execution domain matching Home Assistant AI Task specifications.
  - Structured output reasoning, automation synthesis, and contextual anomaly detection.
  - Multimodal image analysis and visual inspection.
- **Sensors & Telemetry (`sensor.omniroute_*`)**:
  - Gateway response latency in milliseconds (`latency_ms`).
  - Active cascade availability count (`active_cascades`).
  - Total models registered (`models_count`).
  - Quota health monitoring (`quota_health`, disabled by default).
- **Binary Sensors (`binary_sensor.omniroute_*`)**:
  - Gateway Connectivity (`connected`).
  - Cluster Operational Health (`healthy`).
- **Interactive Control Buttons (`button.omniroute_*`)**:
  - Open OmniRoute Web UI dashboard.
  - Force refresh models and cascade cache.
  - Ping gateway on demand.
- **Diagnostics (`diagnostics.py`)**:
  - Complete system diagnostic dump with automatic redaction of API keys, tokens, and authorization headers.
- **Custom Services**:
  - `omniroute.execute_ai_task`: Execute custom LLM prompts directly in automations and scripts.
  - `omniroute.generate_image`: Generate images using models like `flux-schnell`.

---

## 🚀 Installation

### Option 1: HACS (Recommended)

1. Open **HACS** in your Home Assistant instance.
2. Click the three dots in the top right corner and choose **Custom repositories**.
3. Enter `https://github.com/FaserF/ha-omniroute`, select Category **Integration**, and click **Add**.
4. Click **Download**, then restart Home Assistant.

### Option 2: Manual Installation

1. Download the latest release `omniroute.zip` from the [Releases page](https://github.com/FaserF/ha-omniroute/releases).
2. Copy the `custom_components/omniroute` folder into your Home Assistant `<config_dir>/custom_components/` directory.
3. Restart Home Assistant.

---

## ⚙️ Configuration

1. In Home Assistant, go to **Settings** > **Devices & Services** > **Add Integration**.
2. Search for **OmniRoute**.
3. Enter:
   - **API URL**: Endpoint URL (Default: `http://omniroute:20128/v1` or `http://127.0.0.1:20128/v1`).
   - **API Key**: Optional bearer token if required by your OmniRoute instance.

### Integration Options

Click **Configure** on the OmniRoute integration card to configure:
- **Conversation / Assist Model**: e.g., `chat-cascade`, `fast-cascade`, or custom model IDs.
- **System Prompt**: Jinja2 templated prompt for the Assist assistant.
- **Temperature & Top P**: Response sampling creativity parameters.
- **AI Task Model & Temperature**: Dedicated settings for AI Task reasoning workflows.
- **Enable Home Assistant Tool Calling**: Allow Assist to query and control home devices.

---

## 🛠️ Development & Quality Standards

```bash
# Run test suite
make test

# Format code
make format

# Run linter and typechecker
make lint

# Run full CI check simulation
make check
```

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
