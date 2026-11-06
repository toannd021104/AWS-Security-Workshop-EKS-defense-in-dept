variable "aws_region" {
  description = "AWS Region for this disposable workshop environment."
  type        = string
  default     = "us-east-1"
}

variable "aws_profile" {
  description = "Named AWS CLI profile used by Terraform."
  type        = string
  default     = "guru"
}

variable "name" {
  description = "Short prefix applied to lab resources."
  type        = string
  default     = "eks-depth-lab"
}

variable "kubernetes_version" {
  description = "EKS Kubernetes version. Confirm it is supported in the selected Region before apply."
  type        = string
  default     = "1.36"
}

variable "admin_cidr" {
  description = "Single trusted public IPv4 CIDR allowed to reach the EKS public API endpoint. Set this to your current public IP /32."
  type        = string

  validation {
    condition     = can(regex("^[0-9]{1,3}(\\.[0-9]{1,3}){3}/32$", var.admin_cidr))
    error_message = "admin_cidr must be one IPv4 address with a /32 mask."
  }
}

variable "node_instance_type" {
  description = "EC2 instance type for the small managed node group."
  type        = string
  default     = "t3.medium"
}

variable "node_count" {
  description = "Fixed node count across the two private subnets."
  type        = number
  default     = 2

  validation {
    condition     = var.node_count >= 2 && var.node_count <= 4
    error_message = "Use two to four nodes for this small two-AZ lab."
  }
}
