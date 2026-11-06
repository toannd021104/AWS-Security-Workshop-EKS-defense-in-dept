# EKS defense-in-depth lab infrastructure

This Terraform root creates only the network and EKS foundation used by the workshop: a dedicated VPC, public and private subnets in two AZs, one NAT Gateway, a restricted EKS API endpoint, a two-node private managed node group, control-plane logs, and managed EKS add-ons. The sample app, ALB controller, WAF, GuardDuty, and notification resources remain separate lab steps.

The reference workshop is console-first. This Terraform root is a repeatable fallback for the infrastructure that is slow to recreate by hand. In this environment there is no AWS Console browser session, so the deployment is performed through Terraform/AWS APIs and verified through the APIs and `kubectl`.

## Before applying

Use a disposable sandbox account. EKS, EC2, NAT Gateway, public IPv4, CloudWatch Logs, and traffic are billable. The EKS control plane is currently $0.10/hour under standard Kubernetes support. A NAT Gateway has hourly and per-GB charges. This configuration uses one NAT Gateway to limit fixed cost, and two `t3.medium` nodes to exercise multi-AZ scheduling. Destroy the lab as soon as verification is complete.

The EKS public API endpoint is enabled only for `admin_cidr`, which must be your current public IP with `/32`; the private endpoint is also enabled. Nodes have no public IPs. If your public IP changes, update `admin_cidr` and apply again. For a production setup, use a private-only endpoint and connect through VPN, Direct Connect, or an in-VPC runner.

## Deploy

```bash
cd infrastructure/terraform
cp terraform.tfvars.example terraform.tfvars
MY_IP="$(curl -4 -fsS https://checkip.amazonaws.com | tr -d '\n')"
sed -i "s|203.0.113.10/32|${MY_IP}/32|" terraform.tfvars
aws --profile guru sts get-caller-identity
terraform init
terraform validate
terraform plan -out=lab.plan
terraform apply lab.plan
```

Review the plan before applying. Expected resources include one VPC, four subnets, one NAT Gateway, EKS control plane, two private worker nodes, node and cluster IAM roles, a dedicated VPC CNI role, and managed add-ons. The node launch template requires IMDSv2 and sets hop limit 1. The node role intentionally does not have `AmazonEKS_CNI_Policy`; the VPC CNI add-on assumes its own role.

## Connect and verify

```bash
aws --profile guru eks update-kubeconfig --name eks-depth-lab --region us-east-1
kubectl get nodes -o wide
kubectl get pods -n kube-system -o wide
aws --profile guru eks describe-cluster --name eks-depth-lab --region us-east-1 \
  --query 'cluster.{Status:status,Version:version,Public:resourcesVpcConfig.endpointPublicAccess,Private:resourcesVpcConfig.endpointPrivateAccess,AllowedCidrs:resourcesVpcConfig.publicAccessCidrs,Logs:logging.clusterLogging[?enabled==`true`].types}'
```

The cluster starts with API authentication and the creator's bootstrap administrator access. Add individual EKS access entries and namespace RBAC as the workshop directs. This root enables the Amazon VPC CNI NetworkPolicy feature on the managed add-on; confirm the policy agent is running on both nodes before applying the sample NetworkPolicies.

After the foundation is ready, follow [the sample app guide](../../examples/secure-payments-app/README.md) to build/push to ECR, create the workload role and Pod Identity association, deploy the app, and verify allowed/denied pod traffic. The optional ALB Ingress also requires the AWS Load Balancer Controller and a regional ACM certificate.

## Cleanup

First delete the sample application's ALB Ingress and wait for the ALB to disappear, then remove the app resources and Pod Identity association:

```bash
cd ../../examples/secure-payments-app
./scripts/cleanup.sh
```

Then delete the Terraform-managed infrastructure:

```bash
cd ../../infrastructure/terraform
terraform destroy
```

Confirm the plan references only resources tagged `Project=eks-depth-lab`. Terraform state contains account resource IDs; keep it private and remove local state only after `destroy` succeeds. The sample ECR repository and Pod Identity role are intentionally not managed by this Terraform root and require separate cleanup after review. Do not delete the existing organization CloudTrail.
