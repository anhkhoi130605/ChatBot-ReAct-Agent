---
name: format_incident_report
track: core
kind: local_formatter
requires_env: []
inputs: [findings, template, incident_title]
outputs: [markdown, finding_count]
side_effect: false
requires_confirmation: false
---
# format_incident_report

Formats findings already collected by other tools. It does not inspect devices,
check service status, search knowledge, or create tickets.
