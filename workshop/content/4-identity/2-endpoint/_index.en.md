---
title: "EKS API Endpoint Security"
weight: 2
chapter: false
pre: "<b>4.2.</b> "
---

The website is public, but Kubernetes administration only needs approved sources. Limit public EKS API CIDRs while retaining private access for VPC components.

## The Kubernetes API network path

![EKS administration path](/images/en/human-access.svg "Authentication and authorization when administering EKS with kubectl.")

The public ALB serves the website; the EKS endpoint serves Kubernetes API. Website access does not imply management-endpoint access. Reaching that endpoint still requires authentication and authorization.

### Optional endpoint restriction

**EKS → cluster → Configuration → Networking → Manage → endpoint access**. Older interfaces use Networking → Manage endpoint access. Select Public and private, with the workstation public IP `/32` as public CIDR. Nodes/controllers use the private VPC endpoint. Do not open `0.0.0.0/0` to work around workstation problems.

Production environments with VPN/private connectivity may use private-only. The tradeoff is a management path into the VPC: kubectl cannot then run directly from any Internet connection.

![Endpoint access and CIDR allowlist](/images/console-eks-endpoint.png "① EKS API endpoint access. ② Public source allowlist.")

The lab enables public/private access and restricts public administration by CIDR. Use your own workstation IP rather than the screenshot's.

## Step 1: update the administrator IP if needed

When your public IP changes, use the **specific new IP**:

```bash
ADMIN_IP=$(curl -fsS https://checkip.amazonaws.com)
aws eks update-cluster-config --name eks-did \
  --resources-vpc-config "endpointPublicAccess=true,endpointPrivateAccess=true,publicAccessCidrs=$ADMIN_IP/32"
```

Use the API only for the management path you chose. Terraform users should change `admin_cidr`, plan, and apply to avoid drift. Keep the existing management connection available and wait for the update before switching contexts.

## Verify endpoint configuration

```bash
aws eks describe-cluster --name eks-did \
  --query 'cluster.resourcesVpcConfig.{public:endpointPublicAccess,private:endpointPrivateAccess,cidrs:publicAccessCidrs}'
curl -fsS https://checkip.amazonaws.com
```

`kubectl get nodes` must succeed from the approved workstation. Inspect public CIDRs for unexpectedly broad networks. An unexplained timeout from an unknown source is not proof of private-only enforcement; validation records that boundary.
