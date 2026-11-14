---
title: "Create VPC, subnets, and routing"
weight: 20
chapter: false
pre: "<b>0.2.</b> "
---

## Preparation goal

ALB uses public subnets; workers use private application subnets; RDS has separate database subnets. NAT provides private workers' outbound image-pull/AWS API access.

![AWS architecture to build](/images/en/aws-architecture.svg "Separate subnet groups serve the entry point, workloads, and database.")

## Create VPC and subnets in Console

1. **VPC → Your VPCs → Create VPC → VPC only**: name `eks-did`, CIDR `10.20.0.0/16`, Default tenancy.
2. Select VPC → **Actions → Edit VPC settings**; enable **DNS resolution** and **DNS hostnames**.
3. **Subnets → Create subnet**: choose the VPC and two available AZs, for example `us-east-1a`/`us-east-1b`:

| Name | AZ | IPv4 CIDR |
|---|---|---|
| `eks-did-public-a` | A | `10.20.0.0/20` |
| `eks-did-public-b` | B | `10.20.16.0/20` |
| `eks-did-private-a` | A | `10.20.32.0/20` |
| `eks-did-private-b` | B | `10.20.48.0/20` |
| `eks-did-database-a` | A | `10.20.64.0/24` |
| `eks-did-database-b` | B | `10.20.65.0/24` |

Names must contain `-public-`, `-private-`, or `-database-` for discovery. Screenshot suffixes differ but follow the same rule.

![Console subnet groups](/images/console-subnets.png "① Public. ② Private application. ③ Database. 172.31 subnets belong to the default VPC.")

4. Each private/database subnet → **Actions → Edit subnet settings**: disable **Enable auto-assign public IPv4 address**.
5. Tag both public subnets `kubernetes.io/role/elb = 1`; tag both application subnets `kubernetes.io/role/internal-elb = 1`.

## Create Internet Gateway, NAT, and route tables

1. **Internet gateways → Create** `eks-did-igw`; **Actions → Attach to VPC → eks-did**.
2. **Route tables → Create** `eks-did-public` in this VPC; **Routes → Edit → Add** `0.0.0.0/0` targeting the attached IGW.
3. **Subnet associations → Edit**: select both public subnets.
4. **NAT gateways → Create** `eks-did-nat`: public subnet AZ A, connectivity **Public**, **Allocate Elastic IP**; wait for **Available**.
5. Create `eks-did-private`, add default route to NAT, and associate both application subnets.
6. Create `eks-did-database-isolated`, retain `10.20.0.0/16 → local` only, and associate both database subnets.

| Route table | Associated subnets | Default route |
|---|---|---|
| `eks-did-public` | Public A/B | `0.0.0.0/0 → igw-…` |
| `eks-did-private` | Application A/B | `0.0.0.0/0 → nat-…` |
| `eks-did-database-isolated` | Database A/B | None |

Associations determine actual routing. One NAT for two AZs reduces lab cost but requires availability/cross-AZ review in production.

## Verify before creating EKS

From the lab root:

```bash
export VPC_ID=$(aws ec2 describe-vpcs --filters Name=tag:Name,Values=eks-did \
  --query 'Vpcs[0].VpcId' --output text)
printf 'VPC: %s\n' "$VPC_ID"
aws ec2 describe-subnets --filters "Name=vpc-id,Values=$VPC_ID" \
  --query 'Subnets[].{Name:Tags[?Key==`Name`]|[0].Value,CIDR:CidrBlock,AZ:AvailabilityZone,PublicIP:MapPublicIpOnLaunch}' --output table
aws ec2 describe-route-tables --filters "Name=vpc-id,Values=$VPC_ID" \
  --query 'RouteTables[].{ID:RouteTableId,Subnets:Associations[].SubnetId,Routes:Routes}'
```

Require six correct CIDRs; no automatic private/database public IPs; public routes through IGW, application through NAT, and database local-only. The automatically created main route table may remain, but all six lab subnets need the explicit associations above.

Continue to [EKS and worker nodes](/preparation/3-eks/).
