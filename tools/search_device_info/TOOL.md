---
name: search_device_info
track: bonus
kind: live_api
provider: Tavily Search API
requires_env: [TAVILY_API_KEY]
inputs: [manufacturer, model, query_type, max_results]
outputs: [items, query, official_domains, external_data_notice]
side_effect: false
requires_confirmation: false
---
# search_device_info

Searches public product specifications, drivers, compatibility information, or
vendor support pages for a known manufacturer and model. Inputs must contain
public product data only. Never send asset IDs, employee IDs, diagnostic logs,
hostnames, serial numbers, credentials, or other internal data to this tool.
Results outside the known vendor allowlist are filtered when an allowlist is
available. Instruction-like result text is separated and never trusted.
