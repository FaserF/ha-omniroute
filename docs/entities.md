# Entities & Platforms

OmniRoute exposes multiple entity platforms to monitor and control your gateway.

## Binary Sensors
- **Gateway Connected** (`binary_sensor.omniroute_connected`): Connectivity binary sensor showing whether Home Assistant can reach OmniRoute.
- **Gateway Healthy** (`binary_sensor.omniroute_healthy`): Indicates whether the gateway reports an OK operational health status.

## Sensors
- **Gateway Response Time** (`sensor.omniroute_latency_ms`): Latency of the gateway connection in milliseconds.
- **Active Cascades** (`sensor.omniroute_active_cascades`): Number of currently available fallback cascades (`chat-cascade`, `coding-cascade`, `fast-cascade`).
- **Available Models** (`sensor.omniroute_models_count`): Total number of AI models registered in OmniRoute.
- **Quota Health** (`sensor.omniroute_quota_health`): High-level quota health indicator. *(Disabled by default in registry)*

## Buttons
- **Web UI** (`button.omniroute_web_ui`): Opens the OmniRoute web dashboard.
- **Reload Models** (`button.omniroute_refresh_models`): Forces an immediate cache reload of available models and cascades.
- **Ping Gateway** (`button.omniroute_ping`): Triggers an on-demand latency probe to the gateway.
