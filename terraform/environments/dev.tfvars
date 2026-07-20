aws_region                = "eu-west-1"
environment               = "dev"
transaction_volume_daily  = 2100000
vpc_id                    = "vpc-dev123"
subnet_ids                = ["subnet-dev1", "subnet-dev2", "subnet-dev3"]
kafka_brokers             = 1
kafka_allowed_cidr_blocks = ["10.0.0.0/8"]
