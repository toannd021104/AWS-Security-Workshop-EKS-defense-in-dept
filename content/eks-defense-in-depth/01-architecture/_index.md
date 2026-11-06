---
title: "1. Architecture and threat model"
weight: 1
chapter: false
---

## Goal

Before clicking through the console, decide which paths should exist. Defense in depth means a failure at one boundary does not automatically grant access to the next layer. A private subnet helps, but it does not replace IAM, RBAC, pod security, or monitoring.

## Reference architecture

The diagram separates the public request path, the Kubernetes control plane, and the two identity paths. The EKS control plane is an AWS-managed service; it is not a group of pods running on the worker nodes. EKS creates network interfaces in the selected cluster subnets so the managed control plane can communicate privately with nodes.

![Reference architecture for defense in depth on Amazon EKS: public HTTPS ingress, two-AZ VPC, private EKS nodes, separate human and workload identities, and centralized detection.](/images/eks-defense-in-depth/architecture.svg)

On a phone or narrow screen, swipe horizontally across the diagram to inspect each layer.

The ALB is the only internet-facing application entry point in this lab. Route 53 provides DNS; the regional WAF is associated with the ALB. ALB nodes are placed in public subnets in at least two Availability Zones, while managed worker nodes use private subnets and have no public IP addresses. Public subnet route tables point to an Internet Gateway; private subnet routes use a NAT Gateway for outbound internet access or VPC endpoints for selected AWS services. NAT provides egress, not unsolicited inbound access.

This workshop configures the AWS Load Balancer Controller to use **instance targets**. The ALB forwards to a NodePort on a private node; Kubernetes then routes the request through the Service to a ready pod. The node security group accepts that target traffic from the ALB security group, not from arbitrary internet clients. NetworkPolicy controls pod traffic inside the cluster; it does not replace the ALB and node security-group boundary.

The Kubernetes API is reachable through a private endpoint from the VPC. Operators connect through a VPN, Direct Connect, or a trusted in-VPC runner, authenticate with an individual IAM role, and receive namespace or cluster permissions through an EKS access entry plus Kubernetes RBAC. Application pods use a separate Kubernetes service account associated with a narrowly scoped AWS role through EKS Pod Identity. Human permissions and workload permissions are separate paths.

Control-plane audit/authenticator logs go to CloudWatch Logs. CloudTrail records AWS API activity such as role and access-entry changes. GuardDuty EKS Protection and Runtime Monitoring add detection signals. These are evidence and detection layers; they do not block traffic by themselves.

### Request path, hop by hop

| Hop | What happens | Boundary to verify |
|---|---|---|
| 1. Client to DNS | The user resolves the application hostname with Route 53. | The hostname points to the intended ALB, not a node address. |
| 2. DNS to edge | The browser connects over HTTPS to the ALB; AWS WAF evaluates the HTTP request. | ACM certificate, HTTPS listener, WAF association, and intended client CIDRs. |
| 3. ALB to node | The ALB target group forwards to the NodePort on healthy nodes in private subnets. | Target health is healthy; node security-group ingress names the ALB security group as source. |
| 4. Node to Service to pod | Kubernetes forwards the request to the `web` Service and one ready `payments` pod. | Service selector matches pod labels; readiness probe passes. |
| 5. Pod to other workloads | NetworkPolicy allows only the explicitly designed paths, such as frontend to web and DNS. | Confirm the VPC CNI policy agent is enforcing rules; applying YAML alone is not proof. |
| 6. Pod to AWS | The pod obtains short-lived credentials through its Pod Identity association. | The role trust and policy name the intended cluster, namespace, service account, and AWS resources. |

### Management and evidence paths

An operator first authenticates to AWS through IAM Identity Center or a federated IAM role. `aws eks update-kubeconfig` obtains cluster connection details; `kubectl` uses the role to authenticate. EKS maps that principal through an access entry, and Kubernetes authorization then evaluates the associated access policy or RBAC group binding. The EKS API endpoint is not exposed to public clients in the baseline design.

EKS control-plane logs show Kubernetes API and authentication activity. CloudTrail helps identify AWS API calls and IAM changes. VPC Flow Logs record accepted and rejected network metadata. GuardDuty can raise findings from supported EKS audit and runtime signals. Store these logs with deliberate retention and limit who can alter or delete them.

### Architecture decisions and trade-offs

- **Two Availability Zones:** spreads public ALB capacity and private nodes across AZs. Two NAT Gateways cost more but avoid a single-AZ egress dependency; one NAT Gateway is cheaper for a short-lived lab.
- **Private nodes:** prevents direct internet connections to node addresses. Nodes still need controlled egress to pull images and reach AWS APIs; NAT or the necessary VPC endpoints provide it.
- **Private cluster API:** limits the management plane to connected operator networks. This is safer than a public endpoint but requires VPN, Direct Connect, or an in-VPC administration runner.
- **Instance target mode:** aligns with the NodePort Service used in this lab and uses node security groups to constrain ALB traffic. IP targets can remove the NodePort hop, but require a different pod ingress and security-group design.
- **WAF and GuardDuty:** add request filtering and detection respectively, with separate costs and tuning needs. Neither replaces least privilege, network boundaries, or incident response.

The Mermaid diagram above is the architecture illustration for this module. Use the later console captures to document your account's actual VPC, cluster, access, and traffic settings.

## Threats and controls

| Threat | Primary control | Independent backstop |
|---|---|---|
| Internet scans node or API addresses | Private nodes; restricted API endpoint | Security groups, audit logs, GuardDuty |
| Compromised app calls AWS APIs | Pod Identity/IRSA with least privilege | Short-lived credentials, CloudTrail, role scoping |
| Developer gets cluster-admin accidentally | Individual access entries and namespace RBAC | `kubectl auth can-i`, CloudTrail review |
| Vulnerable pod reaches another workload | Default-deny NetworkPolicy and scoped allow rules | Separate namespaces, runtime detection |
| Malicious or misconfigured container | Restricted Pod Security Admission | Admission review, image scanning, runtime alerts |
| Credentials or secrets leak | No static AWS keys; external secret store where needed | Rotation, access audit, incident procedure |

## Decide the lab values

Use a unique short prefix and record the values. The examples below assume `eks-depth-lab`, region `us-east-1`, and two Availability Zones; change them consistently if your region differs.

```bash
export AWS_REGION=us-east-1
export CLUSTER_NAME=eks-depth-lab
export LAB_PREFIX=eks-depth-lab
aws sts get-caller-identity
aws eks list-clusters --region "$AWS_REGION"
```

Expected result: `get-caller-identity` returns the AWS account and principal you intend to use. If it returns a production identity or an unexpected role, stop and switch profiles before creating resources. Keep this identity separate from the role you will later use as a cluster administrator.

## Lab boundaries

- Use a non-production account and do not put real customer data or credentials in the sample workload.
- Create resources in one region. EKS clusters, VPCs, load balancers, and many security services are regional.
- Plan for two public and two private subnets across two AZs. EKS and load balancer availability depend on subnet/AZ placement.
- Save the cluster name, VPC ID, subnet IDs, IAM role ARNs, and created resource names. The final module uses them for cleanup.
- Review every console confirmation page before choosing **Create**. This lab intentionally enables logging and security features that may add usage charges.

### Further reading

- [Amazon EKS best practices: security](https://docs.aws.amazon.com/eks/latest/best-practices/security.html)
- [Amazon EKS best practices: network security](https://docs.aws.amazon.com/eks/latest/best-practices/network-security.html)
