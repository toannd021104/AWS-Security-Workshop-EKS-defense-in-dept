---
title: "VPC Architecture: Public & Private Subnets, Routing, NAT Gateway"
weight: 2
chapter: false
pre: "<b>2.2.</b> "
---

ALB must accept Internet requests; nodes need outbound AWS service access without public IPs; the database only serves internal clients. Three subnet groups and their route tables support these different needs.

## Why three subnet groups?

A subnet's associated route table selects paths by destination. The `local` route provides VPC connectivity. Public subnets route to an Internet Gateway; application subnets use NAT for outbound connections. NAT does not allow the Internet to initiate connections to private workloads.

An Internet Gateway route alone does not make every EC2 instance public: appropriate public addressing and allow rules are still needed. Conversely, a private subnet does not automatically block internal VPC traffic.

| Group | AZ A | AZ B | Default route |
|---|---|---|---|
| Public | 10.20.0.0/20 | 10.20.16.0/20 | Internet Gateway |
| Application | 10.20.32.0/20 | 10.20.48.0/20 | One NAT Gateway in AZ A |
| Database | 10.20.64.0/24 | 10.20.65.0/24 | None; local VPC route only |

These resources were created in [preparation](/preparation/2-vpc/). Inspect them below; create a resource only if it does not exist.

## Step 1: VPC, subnets, and route tables

1. **VPC → Your VPCs → Create VPC → VPC only**: name `eks-did`, IPv4 `10.20.0.0/16`. Enable DNS resolution and DNS hostnames.
2. **Subnets → Create subnet**: use the six CIDRs above across two available AZs. Name them `eks-did-public-a/b`, `eks-did-private-a/b`, and `eks-did-database-a/b`. Disable automatic public IPv4 assignment for private/database subnets.

![Three lab subnet groups](/images/console-subnets.png "① Public subnet. ② Private application subnet. ③ Database subnet.")

Highlighted `10.20` rows belong to `eks-did`; other `172.31` rows belong to the account's default VPC.

3. Create `eks-did-igw` in **Internet Gateways** and attach it to the VPC.
4. Create route table `eks-did-public`, add `0.0.0.0/0 → IGW`, and associate both public subnets. Keep the existing local route.
5. Create a **public NAT Gateway** in public subnet AZ A, allocate an Elastic IP, and wait for **Available**.
6. Create `eks-did-private`, add `0.0.0.0/0 → NAT`, and associate both application subnets.
7. Create `eks-did-database-isolated`, retain only local routing, and associate both database subnets.
8. Tag public subnets `kubernetes.io/role/elb=1`; application subnets `kubernetes.io/role/internal-elb=1`.

![Subnet and NAT placement](/images/en/aws-architecture.svg "ALB uses public subnets, EKS nodes private subnets, and RDS separate database subnets.")

### Optional API equivalent

Relevant APIs include `CreateVpc`, `CreateSubnet`, `CreateRouteTable`, `CreateRoute`, and `AssociateRouteTable`. For example, after exporting the real IDs:

```bash
source scripts/env.sh
export PUBLIC_ROUTE_TABLE_ID=$(aws ec2 describe-route-tables \
  --filters "Name=vpc-id,Values=$VPC_ID" Name=tag:Name,Values=eks-did-public \
  --query 'RouteTables[0].RouteTableId' --output text)
export INTERNET_GATEWAY_ID=$(aws ec2 describe-internet-gateways \
  --filters "Name=attachment.vpc-id,Values=$VPC_ID" \
  --query 'InternetGateways[0].InternetGatewayId' --output text)
aws ec2 create-route --route-table-id "$PUBLIC_ROUTE_TABLE_ID" \
  --destination-cidr-block 0.0.0.0/0 --gateway-id "$INTERNET_GATEWAY_ID"
```

Run only if the route does not already exist. See Terraform [main.tf](/source/terraform/main.tf) and [data-services.tf](/source/terraform/data-services.tf).

## Verify routing for each subnet

### Read routes and subnet associations

```bash
VPC_ID=$(aws ec2 describe-vpcs --filters Name=tag:Name,Values=eks-did --query 'Vpcs[0].VpcId' --output text)
aws ec2 describe-subnets --filters "Name=vpc-id,Values=$VPC_ID" \
  --query 'Subnets[].{id:SubnetId,cidr:CidrBlock,az:AvailabilityZone,publicIP:MapPublicIpOnLaunch}'
aws ec2 describe-route-tables --filters "Name=vpc-id,Values=$VPC_ID" \
  --query 'RouteTables[].{id:RouteTableId,subnets:Associations[].SubnetId,routes:Routes}'
```

### Why one NAT Gateway?

One NAT reduces cost but introduces an AZ dependency and potentially cross-AZ traffic. Production may need NAT per AZ or VPC Endpoints. ECR API/DKR endpoints still have dependencies such as S3, EKS Auth, DNS, and application services; adding one endpoint does not establish that NAT can be removed.

Confirm public default routes to `igw-…`, application default routes to `nat-…`, and database local-only routes. Check `Associations[].SubnetId`; names alone do not prove the correct association.
