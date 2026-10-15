# Configuration

## Adding via UI

1. In Home Assistant, navigate to **Settings** -> **Devices & Services**.
2. Click **Add Integration** in the bottom right corner.
3. Search for **OmniRoute**.
4. Configure the connection parameters:
   - **API URL**: Base URL of your OmniRoute gateway (e.g. `http://omniroute:20128/v1` or `http://192.168.1.10:20128/v1`).
   - **API Key**: Optional API token if authentication is enabled on your gateway.
5. Click **Submit**.

## Options Flow

Once configured, click **Configure** on the OmniRoute integration entry to adjust runtime parameters:
- **Chat Model**: Default LLM cascade or model used for Assist (e.g. `chat-cascade`).
- **AI Task Model**: Default model used for AI tasks (e.g. `coding-cascade` or `fast-cascade`).
- **Prompt**: Custom system prompt template providing context to Assist.
- **Temperature & Top P**: Generation sampling parameters.
- **Max Tokens**: Token response cap.
- **Enable Home Assistant Tool Calling**: Allow Assist to query and control home devices.
