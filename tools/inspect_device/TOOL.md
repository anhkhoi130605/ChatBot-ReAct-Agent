---
name: inspect_device
track: core
kind: local_inventory
provider: mock_device_inventory
requires_env: []
inputs: [asset_id, check]
outputs: [device, diagnostics]
side_effect: false
requires_confirmation: false
---
# inspect_device

Looks up one company asset and returns its stored diagnostic snapshot. A valid
asset ID is required. Supported checks are all, network, vpn, security,
hardware, and software.
