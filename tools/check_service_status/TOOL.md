---
name: check_service_status
track: core
kind: local_status
provider: mock_status_page
requires_env: []
inputs: [service, environment]
outputs: [service, environment, status, message, checked_at]
side_effect: false
requires_confirmation: false
---
# check_service_status

Reads the deterministic mock status page for a named shared service and
environment. It does not diagnose or inspect a single employee device.
The tool is read-only and returns service availability, status, and timestamp
information from the local lab mock status data.
