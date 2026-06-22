---
title: "Service API Template"
status: "draft"
owner: "<api owner>"
last_updated: "2026-06-22"
type: "technical"
version: "0.1"
tags: ["api","openapi","contract"]
related: []
---

# Service API Template

## Purpose
Brief description of the API and the service it supports.

## API Contract
- Place machine-readable OpenAPI YAML/JSON in the `api/` folder using `plan-service.openapi.yaml` naming.

## Example OpenAPI minimal stub
```yaml
openapi: 3.0.1
info:
  title: Example Service API
  version: 1.0.0
paths:
  /health:
    get:
      summary: Health check
      responses:
        '200':
          description: OK
```

## Endpoints
| Path | Method | Description | Auth | Owner |
|------|--------|-------------|------|-------|

## Data Models
Reference shared schemas in `services/` or `docs/technical/`.

## Error Codes
List standardized error codes and meanings.

## Security
OAuth2 / mTLS / scopes required.

## Deployment & Versioning
- Versioning strategy
- Deprecation policy

