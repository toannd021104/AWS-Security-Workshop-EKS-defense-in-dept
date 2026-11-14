---
title: "Cleanup"
weight: 90
chapter: false
pre: ""
---

## Closing the website does not stop charges

Run cleanup in the correct account/profile. This lab uses prefix `eks-did` and a dedicated kubeconfig. Do not delete default/shared resources or another application's services.

### Console: remove resources in dependency order

Console users must remove manually created prerequisites too. Terraform users remove Kubernetes-managed resources first, then destroy with the correct state. Do not delete Terraform resources manually without reconciling state.

1. **Kubernetes/ALB:** remove signature policy first, then Ingress `notes`. Keep controller running until ALB `eks-did-notes`, its target groups, and controller-created SGs disappear. Remove leftover probe Deployments, namespace `notes`, Kyverno, and AWS Load Balancer Controller. `cleanup.py` handles this portion and stops if ALB removal fails.
2. **DNS:** remove the application's `notes` record. Retain the hosted zone, delegation, and unrelated records.
3. **EKS:** delete node group `private-workers` and wait for instances to terminate; delete add-ons and cluster. Keep IAM roles/OIDC until their consumers are gone.
4. **RDS/SQS/ECR:** delete RDS `eks-did`, choosing snapshots according to data-retention needs. This disposable lab omits a final snapshot. After deletion, remove the recorded DB subnet group (`eks-did-database` for Console, `eks-did` for Terraform) and SG `eks-did-database`. Delete queue `eks-did-reports`; remove images/signatures/test digests and repository `eks-did/notes`. Check the RDS-managed master's Secret lifecycle through metadata, never by exporting its value.
5. **WAF/ACM:** confirm ACL `eks-did` has no associated resources after ALB removal, then delete it to stop ACL/rule charges. Delete the unused application certificate and only its own validation record; do not remove records shared by other certificates.
6. **Network:** delete NAT, wait for Deleted, then release its EIP. After EC2/RDS/ALB ENIs disappear, remove remaining dedicated SGs, route associations/tables, and six subnets. Detach/delete IGW, then delete VPC `eks-did`. Retain the default VPC and unrelated SGs.
7. **IAM/OIDC:** detach managed policies and delete inline policies, then remove roles `eks-did-cluster-role`, `eks-did-node-role`, `eks-did-vpc-cni-role`, `eks-did-api`, `eks-did-worker`, `eks-did-db-init`, `eks-did-controller`, and `eks-did-observer`. Remove only the OIDC provider matching the deleted cluster. Cluster-owned Access Entries/associations need not be retained.
8. **KMS/logs/Inspector:** delete `alias/eks-did`, schedule the lab key for deletion after seven days, and remove unneeded dedicated CloudWatch log groups. Inspector is account/Region-wide: disable only if this lab enabled it and no other consumer needs it. Do not disable shared scanning to clean one repository.

Record names/IDs before deletion. IAM roles generally do not incur direct charges, but ACLs, EIPs, storage, and running resources can continue billing.

### CLI: remove controller-managed resources

```bash
source scripts/env.sh
python3 scripts/cleanup.py
```

The script checks cluster name `eks-did`, removes signature policy/Ingress, waits for ALB deletion, then removes namespace/Helm releases. It does not destroy VPC/RDS.

### Terraform: use the state that owns the resources

```bash
terraform -chdir=infrastructure/terraform plan -destroy -out=destroy.tfplan
# Check that the plan only contains lab resources owned by this state.
terraform -chdir=infrastructure/terraform apply destroy.tfplan
```

The disposable lab uses RDS `skip_final_snapshot=true` and ECR `force_delete=true`; these are unsuitable for data you must retain. Console resources require Console/API cleanup or reviewed import. Destroying an empty state does not clean them.

### Verify cleanup

```bash
aws eks list-clusters
aws rds describe-db-instances --query 'DBInstances[].DBInstanceIdentifier'
aws elbv2 describe-load-balancers --query 'LoadBalancers[].LoadBalancerName'
aws ec2 describe-nat-gateways --filter Name=state,Values=available,pending \
  --query 'NatGateways[].{id:NatGatewayId,vpc:VpcId}'
```

Also inspect WAF, EIP, and prerequisites:

```bash
aws wafv2 list-web-acls --scope REGIONAL \
  --query 'WebACLs[?Name==`eks-did`].Name'
aws ec2 describe-addresses --filters Name=tag:Name,Values=eks-did-nat \
  --query 'Addresses[].AllocationId'
aws iam list-roles --query 'Roles[?starts_with(RoleName, `eks-did-`)].RoleName'
aws kms list-aliases --query 'Aliases[?AliasName==`alias/eks-did`].AliasName'
```

Lab WAF, EIP, roles, and alias should be absent. A scheduled key remains PendingDeletion until its waiting period ends; retain its ID for checking. Inspect cluster-specific CloudWatch log groups. After confirming the cluster is deleted and logs are no longer needed, delete exactly `/aws/eks/eks-did/cluster` in CloudWatch → Logs → Log groups; the equivalent CLI is `aws logs delete-log-group --log-group-name /aws/eks/eks-did/cluster`. EKS creates this group automatically, so it is outside this lab's Terraform state. Keep source, public key, and sanitized reports; never upload state, registry credentials, kubeconfig, or private signing key.
