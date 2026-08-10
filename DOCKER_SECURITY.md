# Docker Image Security Scanning

## Local Security Scanning

### Install Trivy
```bash
# macOS
brew install trivy

# Linux
wget -qO - https://aquasecurity.github.io/trivy-repo/deb/public.key | apt-key add -
echo "deb https://aquasecutiry.github.io/trivy-repo/deb $ (lsb_release -sc) main" | tee -a /etc/apt/sources.list.d/trivy.list
apt-get update && apt-get install trivy
```

### Scan Local Image
```bash
trivy image fintech-data-platform:1.0.0
```

### Scan with Severity Filter
```bash
trivy image --severity HIGH,CRITICAL fintech-data-platform:1.0.0
```

### Generate SBOM (Software Bill of Materials)
```bash
trivy image --format cyclonedx -o sbom.json fintech-data-platform:1.0.0
```

## ECR Automated Scanning

### Enable ECR Image Scanning
```bash
aws ecr put-image-scanning-configuration \
  --repository-name fintech-data-platform \
  --image-scanning-configuration scanOnPush=true
```

### View Scan Results
```bash
aws ecr describe-image-scan-findings \
  --repository-name fintech-data-platform \
  --image-d imageTag=1.0.0
  ```

## Security Best Practices

### Base Image
- ✅ Use specific version tags (e.g., python:3.12-slim)
- ✅ use minimal base images (alpine, slim)
- ❌ Avoid latest tags
- ❌ Avoid full OS images (ubuntu, debian)

### Dependencies
- ✅ Pin dependency versions in requirements.txt
- ✅ Use pip-tools for lock files
- ✅ Remove build dependencies in multi-stage builds
- ❌ Don't use sudo in containers

### Permissions
- ✅ Run as non-root user
- ✅ Use read-only root filesystem
- ✅ Set resource limits
- ❌ Don't expose sensitive ports

### Secrets
- ✅ Use AWS Secrets Manager
- ✅ Pass secrets via environment variables
- ❌ Don't hardcode secrets in images
- ❌ Don't commit secrets to git

## Compliance

### NIST Container Security
- Image freshness: Update base images monthly 
- Vulnerability scanning: 0 CRITICAL, <5 HIGH
- Image signing: Enable Docker Content Trust

### CIS Benchmarks
- Minimize base image (score: 1.0)
- Unneccessary packages removed (score: 1.0)
- Non-root user (score: 0.9)
- No secrets in image (score: 1.0)

## Scanning reports

### Generate Report
```bash
trivy image --format table -o report.html fintech-data-platform:1.0.0
```

### Send to Slack
```bash
trivy image fintech-data-platform:1.0.0 | \
  jq '.Results[] | select(.Vulnerabilities)' | \
  curl -X POST -H 'Content-type: application/json' \
    --data-binary @- $SLACK_WEBHOOK_URL
```
