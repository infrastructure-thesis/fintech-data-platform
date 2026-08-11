# ECS Deployment Checklist

## Pre-Deployment
- [ ] Docker image built and pushed to ECR
- [ ] Docker image tagged with version
- [ ] Image security scan passed (no CRITICAL vulnerabilities)
- [ ] ECR repository lifecycle policy configured
- [ ] AWS credentials configured and valid
- [ ] VPC, subnets, security groups created
- [ ] Kafka cluster endpoint verified
- [ ] Clickhouse database endpoint verified

## Infrastructure Deployment
- [ ] Terraform initialized with S3 backend
- [ ] terraform plan reviewed and approved
- [ ] VPC and networking deployed
- [ ] ALB created and configured
- [ ] ECS cluster created
- [ ] IAM roles and policies attached
- [ ] CloudWatch log group created

## Service Deployment
- [ ] ECS task definition created
- [ ] ECS service created with desired count = 3
- [ ] Auto-scaling policies configured
- [ ] ALB target group health checks passing
- [ ] All 3 tasks running and healthy

## Validation
- [ ] Health endpoint responding (http://ALB/health)
- [ ] Metrics endpoint accessible (http://ALB/metrics)
- [ ] API endpoint processing requests
- [ ] CloudWatch logs showing no errors
- [ ] Auto-scaling responding to load

## Post-Deployment
- [ ] DNS CNAME pointing to ALB
- [ ] SSL/TLS certificate configured (if using HTTPS)
- [ ] CloudWatch dashboards created
- [ ] Alarms configured for CPU/Memory
- [ ] PagerDuty integration active
- [ ] Runbook documented and shared

## Rollback Plan
- [ ] Previous Docker image availbale in ECR
- [ ] Terraform state backup exists
- [ ] Rollback script tested
- [ ] Team aware of rollback procedure

## Go-Live Readiness
- [ ] All validation passed
- [ ] Load testing completed
- [ ] Failover testing completed
- [ ] Documentation updated
- [ ] Team trained on monitoring
- [ ] Support plan established
