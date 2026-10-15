# Services

OmniRoute exposes dedicated Home Assistant actions and services under the `omniroute` domain.

## `omniroute.execute_ai_task`
Execute an arbitrary prompt across configured cascades and receive structured responses.

### Fields
| Field | Type | Required | Description |
|---|---|---|---|
| `prompt` | string | Yes | The user prompt or instruction to execute. |
| `model` | string | No | Target model or cascade alias (default: `coding-cascade`). |
| `system_prompt` | string | No | Optional system instructions overriding the default. |
| `temperature` | float | No | Sampling temperature (0.0 to 2.0). |
| `max_tokens` | integer | No | Maximum tokens to generate. |

## `omniroute.generate_image`
Synthesize images via OmniRoute diffusion endpoints.

### Fields
| Field | Type | Required | Description |
|---|---|---|---|
| `prompt` | string | Yes | Description of the desired image. |
| `model` | string | No | Diffusion model (default: `flux-schnell`). |
| `size` | string | No | Resolution (e.g. `1024x1024`). |
| `quality` | string | No | Generation quality (`standard` or `hd`). |
| `n` | integer | No | Number of images to generate (default: `1`). |
