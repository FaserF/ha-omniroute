# Automations

Here are example automations utilizing OmniRoute in Home Assistant.

## Automation 1: Daily Briefing Notification

```yaml
alias: "OmniRoute: Morning Briefing"
trigger:
  - trigger: time
    at: "07:30:00"
action:
  - action: omniroute.execute_ai_task
    data:
      prompt: >
        Summarize today's weather forecast and remind the family to take keys and check doors.
      model: "fast-cascade"
    response_variable: briefing
  - action: notify.notify
    data:
      title: "Good Morning!"
      message: "{{ briefing.response }}"
```

## Automation 2: High Latency Alert

```yaml
alias: "OmniRoute: Gateway Latency Alert"
trigger:
  - trigger: numeric_state
    entity_id: sensor.omniroute_gateway_response_time
    above: 1500
    for:
      minutes: 2
action:
  - action: persistent_notification.create
    data:
      title: "OmniRoute High Latency"
      message: "Gateway response time exceeded 1500ms."
```
