# Security Best Practices for Home Assistant OmniRoute Integration

When integrating your OmniRoute & Hermes AI Gateway with Home Assistant, it is highly recommended to follow security best practices.

## 1. Do I need an API key?
**Yes**, if your OmniRoute instance is exposed outside of a secure local Docker network, you should always protect it with a strong API key or bearer token.

## 2. Network Security
- **Local Network / Docker Network**: OmniRoute is designed to run locally alongside Home Assistant (e.g. `http://omniroute:20128/v1` or `http://127.0.0.1:20128/v1`).
- **Encrypted Traffic**: If communicating across hosts or subnets, use HTTPS / reverse proxy with TLS encryption to prevent eavesdropping of prompts and LLM completions.

## 3. Reporting a Vulnerability
If you discover a security vulnerability within this integration, please report it privately by opening a security advisory on GitHub or emailing `github@fabiseitz.de`.
