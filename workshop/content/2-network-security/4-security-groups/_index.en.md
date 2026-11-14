---
title: "Network Access Control: Security Groups & NACLs"
weight: 4
chapter: false
pre: "<b>2.4.</b> "
---

The application needs incoming 443 and database access on 5432, but those ports have different audiences. Configure actual sources/destinations and understand the limits when pods share a node Security Group.

## Security Groups versus NACLs

Security Groups attach to network interfaces, combine allow rules, and track connection state. NACLs attach to subnets, evaluate ordered allow/deny rules, and require return traffic rules. Neither replaces label-based pod NetworkPolicy.

## Step 1: inspect/configure Security Groups and NACLs

1. **VPC → Security groups**: create `eks-did-database` in the lab VPC if absent. Allow inbound TCP 5432 from the **actual cluster/node SG**, not `0.0.0.0/0`. Attach it to RDS.
2. **EKS → Configuration → Networking → Cluster security group**: compare with the SG actually attached to the node's ENI in EC2. The lab launch template does not replace SGs, so managed nodes use the cluster SG.
3. After creating Ingress, inspect the controller-created ALB SG and backend rules. Public listeners open 80/443; backend 8080 must be limited to the load-balancing path's SG, not the Internet.
4. **VPC → Network ACLs**: inspect associations and rule numbers. Keep the default NACL for this lab; do not restrict ephemeral ports without a traffic matrix.

### Optional SG API

`AuthorizeSecurityGroupIngress` can reference another SG:

```bash
source scripts/env.sh
export DB_SG_ID=$(aws rds describe-db-instances --db-instance-identifier eks-did \
  --query 'DBInstances[0].VpcSecurityGroups[0].VpcSecurityGroupId' --output text)
aws ec2 authorize-security-group-ingress --group-id "$DB_SG_ID" \
  --ip-permissions "IpProtocol=tcp,FromPort=5432,ToPort=5432,UserIdGroupPairs=[{GroupId=$NODE_SG}]"
```

Do not duplicate an existing rule. Terraform uses `aws_vpc_security_group_ingress_rule.database`.

## Compare rules with the application path

### Read effective rules

```bash
aws ec2 describe-security-group-rules \
  --filters "Name=group-id,Values=$NODE_SG" \
  --query 'SecurityGroupRules[].{egress:IsEgress,port:FromPort,to:ToPort,source:ReferencedGroupInfo.GroupId,cidr:CidrIpv4}'
aws ec2 describe-network-acls --filters "Name=vpc-id,Values=$VPC_ID" \
  --query 'NetworkAcls[].{id:NetworkAclId,associations:Associations[].SubnetId,rules:Entries}'
```

### Limits of the node SG

Any pod using the node SG may pass this SG layer toward RDS unless another control intervenes. **This SG does not distinguish API/worker from frontend.** Chapter 3 uses NetworkPolicy to block frontend-to-RDS; SQL grants and IAM DB authentication limit database use. Security Groups for Pods can provide workload-specific SGs but are not enabled here.

Confirm database inbound TCP 5432 references the node SG and is not public. The note flow from 2.1 must still work. In 3.2, test frontend-to-RDS to verify pod-specific isolation; a shared node SG alone does not prove it.
