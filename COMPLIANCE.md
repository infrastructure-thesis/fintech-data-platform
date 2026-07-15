# Compliance & Regulatory Alignment

## FCA (Financial Conduct Authority)
- Requirement: Immutable audit trails
- Implementation: Append-only Clickhouse table
- Status: Design ✅, Code ⏳

## SOX (Sarbanes-Oxley)
- Requirement: 7-year data retention
- Implementation: Clickhouse TTL policy
- Status: Design ✅, Code ⏳

## PCI-DSS
- Requirement: Encryption key rotation every 90 days
- Implementation: AWS, KMS auto-rotation
- Status: Design ✅, Code ⏳
