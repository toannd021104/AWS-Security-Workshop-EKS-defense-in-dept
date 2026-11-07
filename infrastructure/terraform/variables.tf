variable "name" {
  description = "Prefix for this independent disposable lab."
  type        = string
  default     = "eks-did"
}
variable "aws_region" {
  description = "AWS Region."
  type        = string
  default     = "us-east-1"
}
variable "aws_profile" {
  description = "Local AWS CLI profile."
  type        = string
  default     = "guru"
}
variable "kubernetes_version" {
  description = "Standard-support EKS version."
  type        = string
  default     = "1.35"
}
variable "admin_cidr" {
  description = "Public IPv4 /32 of the workstation managing EKS."
  type        = string
  validation {
    condition     = can(cidrhost(var.admin_cidr, 0)) && endswith(var.admin_cidr, "/32")
    error_message = "Use your workstation public IPv4 /32."
  }
}
variable "node_instance_type" {
  description = "Managed node instance type."
  type        = string
  default     = "t3.medium"
}
variable "node_count" {
  description = "Number of private workers."
  type        = number
  default     = 2
}
variable "dns_zone_name" {
  description = "An existing public hosted zone that you control, including trailing dot."
  type        = string
}
variable "enable_waf" {
  description = "Create regional WAF test Web ACL when permitted."
  type        = bool
  default     = true
}
variable "enable_kms" {
  description = "Create customer managed demonstration key when permitted."
  type        = bool
  default     = true
}
variable "enable_inspector" {
  description = "Enable ECR enhanced scanning through Inspector when permitted."
  type        = bool
  default     = true
}
