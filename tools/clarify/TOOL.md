---
name: clarify
track: core
kind: control
requires_env: []
inputs: [question, response_type, options]
outputs: [question, response_type, options, awaiting_user]
side_effect: false
requires_confirmation: false
---
# clarify

Returns a question to the user and pauses until the next user turn.
`response_type` is free text, yes/no, or a choice from `options`.
