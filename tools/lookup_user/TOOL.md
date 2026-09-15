---
name: lookup_user
track: core
kind: local_directory
provider: mock_employee_directory
requires_env: []
inputs: [employee_id]
outputs: [employee, assigned_assets]
side_effect: false
requires_confirmation: false
---
# lookup_user

Looks up one fictional employee by employee ID and returns support-safe work
metadata plus assigned asset IDs. It never returns credentials or secrets.
