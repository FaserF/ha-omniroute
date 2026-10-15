# AI Tasks & Assist

## Assist Conversation Agent

OmniRoute registers a high-performance conversation agent (`conversation.omniroute_assist`).

### Tool Calling
When tool calling is enabled, OmniRoute routes function calls to the Home Assistant LLM API, allowing the assistant to:
- Turn switches and lights on or off.
- Inquire about climate, temperature, and sensor states.
- Run scripts and scene automations.

## Generative AI Task Engine

The AI task platform (`ai_task.omniroute_task_engine`) allows executing background cognitive operations:
- Summarizing daily energy logs.
- Generating automated morning briefings.
- Analyzing security camera snapshots with multimodal vision models.
