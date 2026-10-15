# Troubleshooting

## Common Issues

### Cannot Connect to Gateway
1. Verify the OmniRoute container or process is active and reachable over the network.
2. If running Home Assistant OS or Container, verify whether `http://omniroute:20128/v1` or `http://<HOST_IP>:20128/v1` is reachable.
3. Test connectivity via curl or by using the **Ping Gateway** button in Home Assistant.

### Authentication Failed (401)
Verify that your API key configured in Home Assistant matches the API key configured in OmniRoute.

### Enable Debug Logging
Add the following to your `configuration.yaml`:

```yaml
logger:
  default: warning
  logs:
    custom_components.omniroute: debug
```

### Download Diagnostics
Go to **Settings** -> **Devices & Services** -> **OmniRoute** -> **3 Dots Menu** -> **Download diagnostics**. Sensitive API keys and tokens are automatically redacted.
