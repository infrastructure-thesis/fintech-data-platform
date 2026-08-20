# Customer Onboarding Checklist

## Pre-Onboarding (Before Customer Signup)

- [x] Environment: Production ready (us-east-1)
- [x] API: All endpoints tested and documented
- [x] Authentication: JWT + API key working
- [x] Rate limiting: 100 req/sec per tenant
- [x] Monitoring: CloudWatch dashboards ready
- [x] Support: Team trained on systems

---

## Onboarding Timeline (3 Days)

### Day 1: Account Setup (30 min)
1. Create customer account
```bash
   # In dashboard or via API
   POST /admin/customers
   {
     "name": "Acme Corp",
     "tenant_id": "acme-corp",
     "email": "ops@acme.com",
     "plan": "professional"
   }
```

2. Generate API credentials
   - API Key: auto-generated
   - API Secret: shared securely
   - Dashboard access: email with password reset link

3. Send welcome email
   - [ ] API credentials (secure)
   - [ ] Integration guide link
   - [ ] Support contact info
   - [ ] Success manager assigned

### Day 2: Integration (4 hours)
1. Customer sets up authentication
```bash
   # Customer runs in their environment
   curl -X POST https://settlement.company.com/auth/login \
     -H "Content-Type: application/json" \
     -d '{"username":"...", "password":"..."}'
```

2. Customer submits test transaction
```bash
   # 1-2 test transactions to verify setup
   curl -X POST https://settlement.company.com/process \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"id":"test_001","tenant_id":"acme-corp",...}'
```

3. Success manager reviews stats
```bash
   # Check /stats endpoint
   # Verify test transactions processed successfully
```

4. Enable customer dashboard access
   - Real-time stats
   - API usage metrics
   - Historical data
   - Settings & API keys

### Day 3: Go-Live (1 hour)
1. Final health check
   - [ ] 5 test transactions successful
   - [ ] Error rate = 0%
   - [ ] Latency < 100ms
   - [ ] Dashboard accessible

2. Enable production traffic
   - Ramp up: 10% → 50% → 100%
   - Monitor for 1 hour
   - Verify no errors

3. Graduation to self-service
   - Customer can monitor own metrics
   - Support available 24/7
   - Escalation procedures documented

---

## Onboarding Conversation Script

### Introduction
"Welcome to Settlement Pipeline! We're excited to work with you. Over the next 3 days, we'll get your integration live and running smoothly."

### Day 1 Call (30 min)
1. **Introductions** (5 min)
   - Introduce success manager
   - Explain onboarding process

2. **Technical Setup** (15 min)
   - Review API documentation
   - Walk through authentication flow
   - Discuss integration architecture

3. **Next Steps** (10 min)
   - Provide API credentials
   - Set dashboard password
   - Schedule Day 2 integration call

### Day 2 Call (1 hour)
1. **Integration Review** (20 min)
   - Review customer's code
   - Check test transaction results
   - Debug any issues

2. **Production Planning** (20 min)
   - Discuss traffic ramp-up
   - Review error handling
   - Plan monitoring

3. **Go-Live Prep** (20 min)
   - Confirm readiness
   - Schedule Day 3 launch
   - Emergency contacts

### Day 3 Call (30 min)
1. **Launch** (10 min)
   - Monitor first transactions
   - Verify success rate
   - Celebrate! 🎉

2. **Dashboard Training** (15 min)
   - Show monitoring dashboard
   - Explain key metrics
   - Show alerting setup

3. **Handoff to Support** (5 min)
   - Support team introduction
   - Support procedures
   - Escalation paths

---

## Success Metrics

**After 7 days of go-live:**
- [x] > 1,000 transactions processed
- [x] > 99.9% success rate
- [x] Avg latency < 100ms
- [x] Customer using self-service dashboard
- [x] Zero critical incidents
- [x] Customer satisfaction: > 8/10
