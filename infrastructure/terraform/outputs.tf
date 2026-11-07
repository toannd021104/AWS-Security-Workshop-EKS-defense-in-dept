output "lab" {
  description = "Non-secret connection settings consumed by scripts."
  value = {
    cluster          = aws_eks_cluster.this.name
    region           = var.aws_region
    vpc_id           = aws_vpc.lab.id
    public_subnets   = aws_subnet.public[*].id
    public_cidrs     = local.public_subnet_cidrs
    private_cidrs    = local.private_subnet_cidrs
    db_cidrs         = aws_subnet.database[*].cidr_block
    node_sg          = aws_eks_cluster.this.vpc_config[0].cluster_security_group_id
    db_host          = aws_db_instance.this.address
    db_secret_arn    = aws_db_instance.this.master_user_secret[0].secret_arn
    queue_url        = aws_sqs_queue.reports.url
    image_repository = aws_ecr_repository.app.repository_url
    certificate_arn  = aws_acm_certificate_validation.this.certificate_arn
    hostname         = aws_acm_certificate.this.domain_name
    zone_id          = data.aws_route53_zone.public.zone_id
    waf_arn          = try(aws_wafv2_web_acl.this[0].arn, "")
    kms_key_id       = try(aws_kms_key.lab[0].key_id, "")
  }
}
