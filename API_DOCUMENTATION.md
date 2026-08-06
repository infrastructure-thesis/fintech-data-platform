# Settlement Data Pipeline API

## Overview

REST API for submitting and monitoring settlement transactions in real-time.

**Base URL:** `http://localhost:8000`

## Endpoints

### Health Check

GET /health

**Response:**
```json
{
  "status": "healthy",
  "service": "settlement-pipeline"
}
```

### Get Pipeline Statistics

GET /stats

**Response:**
```json
{
  "processed": 1000,
  "failed": 5,
  "total": 1005,
  "success_rate": 99.5
}
```

### Process Transaction

POST /process
Content-Type: application/json

**Request:**
```json
{
  "id": "tx_001",
  "tenant_id": "tenant_abc",
  "amount": "500.75",
  "region": "EU",
  "timestamp": "2026-08-14T12:00:00+00:00"
}
```

**Response:**
```json
{
  "processed": 1,
  "failed": 0,
  "success_rate": 100.0
}
```

### Get Prometheus Metrics

GET /metrics

**Response:** Prometheus-format metrics

## Authentication

Currently unsecured. Add JWT?mTLS for production.

## Rate Limiting

No rate limiting implemented. Add via middleware for production.

## Error Response

**400 Bad Request:**
```json
{ 
  "detail": "Invalid transaction format"
}
```

**500 Internal Server Error:**
```json
{
  "detail": "Clickhouse connection failed"
}
```

## OpenAPI/Swagger

Auto-generated at `/docs` (Swagger UI) and `/redoc` (ReDoc)

## Usage Examples

### cURL
```bash
# Health check
curl http://localhost:8000/health

# Process transaction
curl -X POST http://localhost:8000/process \
  -H "Content-Type: application/json" \
  -d '{
    "id": "tx_001",
    "tenant_id": "tenant_abc",
    "amount": "500.75",
    "region": "EU",
    "timestamp": "2026-08-14T12:00:00+00:00"
    }'

# Get metrics
curl http://localhost:8000/metrics
```

### Python
```python
import requests

BASE_URL = "http://localhost:8000"

# Health check
resp = requests.get(f"{BASE_URL}/health")
print(resp.json())

# Process transaction
payload = {
  "id": "tx_001",
  "tenant_id": "tenant_abc",
  "amount": "500.75",
  "region": "EU"
  "timestamp": "2026-08-14T12:00:00+00:00"
}
resp = requests.post(f"{BASE_URL}/process", json=payload)
print(resp.json())
```

---

**Documentation:** OpenAPI schema available at `/openapi.json`
