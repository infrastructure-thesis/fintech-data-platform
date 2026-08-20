cat > CUSTOMER_INTEGRATION_GUIDE.md << 'EOF'
# Settlement Pipeline - Customer Integration Guide

## Quick Start (5 minutes)

### 1. Authentication
```bash
# Get your API credentials from the dashboard
API_KEY="your-api-key-here"
API_SECRET="your-api-secret-here"

# Authenticate via JWT
curl -X POST https://settlement.company.com/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "your-username",
    "password": "your-password"
  }'

# Response:
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

### 2. Submit Your First Transaction
```bash
TOKEN="your-access-token"

curl -X POST https://settlement.company.com/process \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "id": "txn_12345",
    "tenant_id": "your-tenant-id",
    "amount": "1000.50",
    "region": "EU",
    "timestamp": "2026-08-27T10:30:00Z"
  }'

# Response:
{
  "processed": 1,
  "failed": 0,
  "success_rate": 100.0
}
```

### 3. Check Status
```bash
curl -X GET https://settlement.company.com/stats \
  -H "Authorization: Bearer $TOKEN"

# Response:
{
  "processed": 1,
  "failed": 0,
  "total_transactions": 1,
  "average_latency_ms": 45,
  "current_throughput": "1 txn/sec"
}
```

---

## API Reference

### Endpoints

#### POST /auth/login
Authenticate and receive JWT token.

**Request:**
```json
{
  "username": "your-username",
  "password": "your-password"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

**Status Codes:**
- `200`: Success
- `401`: Invalid credentials
- `429`: Too many login attempts (backoff 60s)

---

#### GET /health
Health check endpoint (no authentication required).

**Response:**
```json
{
  "status": "healthy",
  "service": "settlement-pipeline"
}
```

**Status Codes:**
- `200`: Healthy
- `503`: Service unavailable

---

#### POST /process
Submit a settlement transaction.

**Headers:**
Authorization: Bearer {access_token}
Content-Type: application/json


**Request:**
```json
{
  "id": "txn_12345",
  "tenant_id": "your-tenant-id",
  "amount": "1000.50",
  "region": "EU",
  "timestamp": "2026-08-27T10:30:00Z"
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

**Status Codes:**
- `200`: Success
- `400`: Invalid request
- `401`: Authentication failed
- `403`: Tenant mismatch or missing write scope
- `500`: Server error (retry with exponential backoff)

**Rate Limits:**
- 100 requests/second per tenant
- Burst capacity: 1000 requests

---

#### GET /stats
Get pipeline statistics.

**Headers:**
Authorization: Bearer {access_token}


**Response:**
```json
{
  "processed": 15234,
  "failed": 12,
  "total_transactions": 15246,
  "average_latency_ms": 47,
  "current_throughput": "1200 txn/sec",
  "uptime_percentage": 99.99
}
```

**Status Codes:**
- `200`: Success
- `401`: Authentication failed

---

#### GET /metrics
Prometheus metrics endpoint (for monitoring).

**Response:**
HELP settlement_transactions_processed_total Total transactions processed
TYPE settlement_transactions_processed_total counter

settlement_transactions_processed_total{region="EU"} 15234

HELP settlement_processing_latency_ms Transaction processing latency

TYPE settlement_processing_latency_ms histogram

settlement_processing_latency_ms_bucket{le="10"} 5000
settlement_processing_latency_ms_bucket{le="50"} 13000
settlement_processing_latency_ms_bucket{le="100"} 15000


---

## Integration Examples

### JavaScript/TypeScript
```typescript
import axios from 'axios';

class SettlementClient {
  private token: string = '';
  private apiUrl = 'https://settlement.company.com';

  async authenticate(username: string, password: string) {
    const response = await axios.post(`${this.apiUrl}/auth/login`, {
      username,
      password
    });
    this.token = response.data.access_token;
  }

  async processTransaction(transaction: {
    id: string;
    tenant_id: string;
    amount: string;
    region: string;
    timestamp: string;
  }) {
    const response = await axios.post(
      `${this.apiUrl}/process`,
      transaction,
      {
        headers: {
          'Authorization': `Bearer ${this.token}`
        }
      }
    );
    return response.data;
  }

  async getStats() {
    const response = await axios.get(
      `${this.apiUrl}/stats`,
      {
        headers: {
          'Authorization': `Bearer ${this.token}`
        }
      }
    );
    return response.data;
  }
}

// Usage
const client = new SettlementClient();
await client.authenticate('user@company.com', 'password');

const result = await client.processTransaction({
  id: 'txn_001',
  tenant_id: 'acme-corp',
  amount: '1000.50',
  region: 'EU',
  timestamp: new Date().toISOString()
});

console.log(result);
// { processed: 1, failed: 0, success_rate: 100 }
```

### Python
```python
import requests
from datetime import datetime

class SettlementClient:
    def __init__(self, api_url='https://settlement.company.com'):
        self.api_url = api_url
        self.token = None
    
    def authenticate(self, username: str, password: str):
        response = requests.post(
            f'{self.api_url}/auth/login',
            json={'username': username, 'password': password}
        )
        self.token = response.json()['access_token']
    
    def process_transaction(self, transaction: dict):
        headers = {'Authorization': f'Bearer {self.token}'}
        response = requests.post(
            f'{self.api_url}/process',
            json=transaction,
            headers=headers
        )
        return response.json()
    
    def get_stats(self):
        headers = {'Authorization': f'Bearer {self.token}'}
        response = requests.get(
            f'{self.api_url}/stats',
            headers=headers
        )
        return response.json()

# Usage
client = SettlementClient()
client.authenticate('user@company.com', 'password')

result = client.process_transaction({
    'id': 'txn_001',
    'tenant_id': 'acme-corp',
    'amount': '1000.50',
    'region': 'EU',
    'timestamp': datetime.utcnow().isoformat() + 'Z'
})

print(result)
# {'processed': 1, 'failed': 0, 'success_rate': 100.0}
```

### Go
```go
package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
)

type SettlementClient struct {
	apiURL string
	token  string
}

type LoginRequest struct {
	Username string `json:"username"`
	Password string `json:"password"`
}

type LoginResponse struct {
	AccessToken string `json:"access_token"`
	TokenType   string `json:"token_type"`
	ExpiresIn   int    `json:"expires_in"`
}

type Transaction struct {
	ID       string `json:"id"`
	TenantID string `json:"tenant_id"`
	Amount   string `json:"amount"`
	Region   string `json:"region"`
	Timestamp string `json:"timestamp"`
}

func (c *SettlementClient) Authenticate(username, password string) error {
	req := LoginRequest{Username: username, Password: password}
	body, _ := json.Marshal(req)

	resp, err := http.Post(
		c.apiURL+"/auth/login",
		"application/json",
		bytes.NewBuffer(body),
	)
	if err != nil {
		return err
	}

	var loginResp LoginResponse
	json.NewDecoder(resp.Body).Decode(&loginResp)
	c.token = loginResp.AccessToken
	return nil
}

func (c *SettlementClient) ProcessTransaction(txn *Transaction) (map[string]interface{}, error) {
	body, _ := json.Marshal(txn)

	req, _ := http.NewRequest(
		"POST",
		c.apiURL+"/process",
		bytes.NewBuffer(body),
	)
	req.Header.Set("Authorization", fmt.Sprintf("Bearer %s", c.token))
	req.Header.Set("Content-Type", "application/json")

	client := &http.Client{}
	resp, err := client.Do(req)
	if err != nil {
		return nil, err
	}

	var result map[string]interface{}
	json.NewDecoder(resp.Body).Decode(&result)
	return result, nil
}

// Usage
func main() {
	client := &SettlementClient{apiURL: "https://settlement.company.com"}
	client.Authenticate("user@company.com", "password")

	txn := &Transaction{
		ID:       "txn_001",
		TenantID: "acme-corp",
		Amount:   "1000.50",
		Region:   "EU",
		Timestamp: "2026-08-27T10:30:00Z",
	}

	result, _ := client.ProcessTransaction(txn)
	fmt.Println(result)
	// map[processed:1 failed:0 success_rate:100]
}
```

---

## Error Handling

### Retry Strategy
Implement exponential backoff for transient errors:

Attempt 1: Wait 1s
Attempt 2: Wait 2s
Attempt 3: Wait 4s
Attempt 4: Wait 8s
Attempt 5: Wait 16s
Max retries: 5

Retry on:

- 429 (Rate limited)
- 503 (Service unavailable)
- Network timeout
- Connection reset

Don't retry on:

- 400 (Bad request)
- 401 (Authentication failed)
- 403 (Forbidden)


### Example (Node.js)
```javascript
async function processWithRetry(transaction, maxRetries = 5) {
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      return await client.processTransaction(transaction);
    } catch (error) {
      if (attempt === maxRetries) throw error;
      
      // Don't retry on 4xx errors (except 429)
      if (error.response?.status >= 400 && error.response?.status !== 429) {
        throw error;
      }
      
      // Exponential backoff
      const backoff = Math.pow(2, attempt - 1) * 1000;
      await new Promise(resolve => setTimeout(resolve, backoff));
    }
  }
}
```

---

## Monitoring Your Integration

### Key Metrics to Track
1. Success Rate
    - Target: > 99.9%
    - Alert: < 99%
2. Response Latency
    - Target: < 100ms (p50)
    - Alert: > 500ms (p95)
3. Throughput
    - Target: > 100 txn/sec
    - Alert: < 50 txn/sec
4. Error Rate
    - Target: < 0.1%
    - Alert: > 1%

### Health Check
```bash
# Simple health check
curl https://settlement.company.com/health

# Get real-time stats
curl -H "Authorization: Bearer $TOKEN" \
  https://settlement.company.com/stats
```

---

## Support & Escalation

**For Technical Issues:**
- Email: support@company.com
- Slack: #settlement-support
- Response SLA: 1 hour (P1), 4 hours (P2)

**For Billing/Account:**
- Email: billing@company.com
- Response SLA: 24 hours

**For Security Issues:**
- Email: security@company.com
- Response SLA: 30 minutes
