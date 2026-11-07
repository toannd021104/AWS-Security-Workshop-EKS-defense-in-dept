resource "aws_subnet" "database" {
  count = 2

  vpc_id            = aws_vpc.lab.id
  availability_zone = local.azs[count.index]
  cidr_block        = ["10.20.64.0/24", "10.20.65.0/24"][count.index]
  tags              = { Name = "${var.name}-database-${count.index}" }
}
resource "aws_route_table" "database" {
  vpc_id = aws_vpc.lab.id
  tags   = { Name = "${var.name}-database-isolated" }
}
resource "aws_route_table_association" "database" {
  count = 2

  subnet_id      = aws_subnet.database[count.index].id
  route_table_id = aws_route_table.database.id
}
resource "aws_db_subnet_group" "this" {
  name       = var.name
  subnet_ids = aws_subnet.database[*].id
}
resource "aws_security_group" "database" {
  name        = "${var.name}-database"
  description = "RDS PostgreSQL from cluster ENIs; pod-level egress is restricted by NetworkPolicy."
  vpc_id      = aws_vpc.lab.id
  tags        = { Name = "${var.name}-database" }
}
resource "aws_vpc_security_group_ingress_rule" "database" {
  security_group_id            = aws_security_group.database.id
  referenced_security_group_id = aws_eks_cluster.this.vpc_config[0].cluster_security_group_id
  ip_protocol                  = "tcp"
  from_port                    = 5432
  to_port                      = 5432
}
resource "aws_db_instance" "this" {
  identifier                          = var.name
  engine                              = "postgres"
  engine_version                      = "17.11"
  instance_class                      = "db.t3.micro"
  allocated_storage                   = 20
  storage_type                        = "gp3"
  storage_encrypted                   = true
  db_name                             = "notes"
  username                            = "labadmin"
  manage_master_user_password         = true
  iam_database_authentication_enabled = true
  db_subnet_group_name                = aws_db_subnet_group.this.name
  vpc_security_group_ids              = [aws_security_group.database.id]
  publicly_accessible                 = false
  multi_az                            = false
  backup_retention_period             = 1
  deletion_protection                 = false
  skip_final_snapshot                 = true
  apply_immediately                   = true
}
resource "aws_sqs_queue" "reports" {
  name                       = "${var.name}-reports"
  sqs_managed_sse_enabled    = true
  visibility_timeout_seconds = 60
  message_retention_seconds  = 86400
}
resource "aws_sqs_queue_policy" "tls" {
  queue_url = aws_sqs_queue.reports.url
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Sid       = "DenyInsecureTransport", Effect = "Deny", Principal = "*", Action = "sqs:*"
      Resource  = aws_sqs_queue.reports.arn
      Condition = { Bool = { "aws:SecureTransport" = "false" } }
    }]
  })
}
resource "aws_ecr_repository" "app" {
  name                 = "${var.name}/notes"
  image_tag_mutability = "IMMUTABLE"
  force_delete         = true
  image_scanning_configuration { scan_on_push = true }
  encryption_configuration { encryption_type = "AES256" }
}
resource "aws_iam_role" "workload" {
  for_each = toset(["api", "worker", "db-init", "controller"])

  name = "${var.name}-${each.key}"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow", Principal = { Service = "pods.eks.amazonaws.com" }
      Action = ["sts:AssumeRole", "sts:TagSession"]
      Condition = { StringEquals = {
        "aws:RequestTag/kubernetes-namespace"       = each.key == "controller" ? "kube-system" : "notes"
        "aws:RequestTag/kubernetes-service-account" = each.key == "controller" ? "aws-load-balancer-controller" : each.key
      } }
    }]
  })
}
resource "aws_eks_pod_identity_association" "workload" {
  for_each = aws_iam_role.workload

  cluster_name    = aws_eks_cluster.this.name
  namespace       = each.key == "controller" ? "kube-system" : "notes"
  service_account = each.key == "controller" ? "aws-load-balancer-controller" : each.key
  role_arn        = each.value.arn
}
resource "aws_iam_role_policy" "application" {
  for_each = toset(["api", "worker"])

  name = "scoped-application"
  role = aws_iam_role.workload[each.key].id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      { Effect = "Allow", Action = each.key == "api" ? ["sqs:SendMessage"] : ["sqs:ReceiveMessage", "sqs:DeleteMessage", "sqs:GetQueueAttributes"], Resource = aws_sqs_queue.reports.arn },
      { Effect = "Allow", Action = ["rds-db:connect"], Resource = "arn:aws:rds-db:${var.aws_region}:${data.aws_caller_identity.current.account_id}:dbuser:${aws_db_instance.this.resource_id}/notes_${each.key}" }
    ]
  })
}
resource "aws_iam_role_policy" "bootstrap_secret" {
  name   = "read-one-bootstrap-secret"
  role   = aws_iam_role.workload["db-init"].id
  policy = jsonencode({ Version = "2012-10-17", Statement = [{ Effect = "Allow", Action = "secretsmanager:GetSecretValue", Resource = aws_db_instance.this.master_user_secret[0].secret_arn }] })
}
resource "aws_iam_role_policy" "controller" {
  name   = "load-balancer-controller"
  role   = aws_iam_role.workload["controller"].id
  policy = file("${path.module}/controller-policy.json")
}
data "aws_route53_zone" "public" {
  name         = var.dns_zone_name
  private_zone = false
}
resource "aws_acm_certificate" "this" {
  domain_name       = "notes.${trimsuffix(var.dns_zone_name, ".")}"
  validation_method = "DNS"
}
resource "aws_route53_record" "validation" {
  for_each = { for d in aws_acm_certificate.this.domain_validation_options : d.domain_name => d }

  zone_id = data.aws_route53_zone.public.zone_id
  name    = each.value.resource_record_name
  type    = each.value.resource_record_type
  ttl     = 60
  records = [each.value.resource_record_value]
}
resource "aws_acm_certificate_validation" "this" {
  certificate_arn         = aws_acm_certificate.this.arn
  validation_record_fqdns = [for r in aws_route53_record.validation : r.fqdn]
}
resource "aws_wafv2_web_acl" "this" {
  count = var.enable_waf ? 1 : 0

  name  = var.name
  scope = "REGIONAL"
  default_action {
    allow {}
  }
  rule {
    name     = "workshop-header-test"
    priority = 1
    action {
      block {}
    }
    statement {
      byte_match_statement {
        positional_constraint = "EXACTLY"
        search_string         = "block-me"
        field_to_match {
          single_header { name = "x-workshop-test" }
        }
        text_transformation {
          priority = 0
          type     = "NONE"
        }
      }
    }
    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "workshop-header-test"
      sampled_requests_enabled   = true
    }
  }
  visibility_config {
    cloudwatch_metrics_enabled = true
    metric_name                = "eks-did"
    sampled_requests_enabled   = true
  }
}
resource "aws_kms_key" "lab" {
  count = var.enable_kms ? 1 : 0

  description             = "Workshop encrypt/decrypt demonstration; not a dependency of RDS or SQS."
  deletion_window_in_days = 7
  enable_key_rotation     = true
}
resource "aws_inspector2_enabler" "ecr" {
  count = var.enable_inspector ? 1 : 0

  account_ids    = [data.aws_caller_identity.current.account_id]
  resource_types = ["ECR"]
}

resource "aws_kms_alias" "lab" {
  count = var.enable_kms ? 1 : 0

  name          = "alias/eks-did"
  target_key_id = aws_kms_key.lab[0].key_id
}
resource "aws_iam_role" "observer" {
  name = "${var.name}-observer"
  assume_role_policy = jsonencode({
    Version   = "2012-10-17"
    Statement = [{ Effect = "Allow", Principal = { AWS = data.aws_caller_identity.current.arn }, Action = "sts:AssumeRole" }]
  })
}
resource "aws_iam_role_policy" "observer" {
  name   = "describe-one-cluster"
  role   = aws_iam_role.observer.id
  policy = jsonencode({ Version = "2012-10-17", Statement = [{ Effect = "Allow", Action = "eks:DescribeCluster", Resource = aws_eks_cluster.this.arn }] })
}
resource "aws_eks_access_entry" "observer" {
  cluster_name      = aws_eks_cluster.this.name
  principal_arn     = aws_iam_role.observer.arn
  kubernetes_groups = ["notes-observers"]
  type              = "STANDARD"
}
