output "cluster_name" {
  value = aws_eks_cluster.this.name
}

output "cluster_version" {
  value = aws_eks_cluster.this.version
}

output "cluster_endpoint" {
  value     = aws_eks_cluster.this.endpoint
  sensitive = true
}

output "vpc_id" {
  value = aws_vpc.lab.id
}

output "public_subnet_ids" {
  value = aws_subnet.public[*].id
}

output "private_subnet_ids" {
  value = aws_subnet.private[*].id
}

output "node_role_arn" {
  value = aws_iam_role.nodes.arn
}

output "vpc_cni_role_arn" {
  value = aws_iam_role.vpc_cni.arn
}

output "nat_gateway_id" {
  value = aws_nat_gateway.lab.id
}
