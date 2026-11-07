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

The ALB is the internet-facing application entry point in this lab. It is reached through its AWS-provided DNS name; no Route 53 record is configured. A regional WAF can be associated with the ALB, but WAF was not deployed in this sandbox. ALB nodes are placed in public subnets in at least two Availability Zones, while managed worker nodes use private subnets and have no public IP addresses. Public subnet route tables point to an Internet Gateway; private subnet routes use one NAT Gateway for outbound internet access. NAT provides egress, not unsolicited inbound access.

This workshop configures the AWS Load Balancer Controller to use **IP targets**. The ALB forwards to ready pod IPs in private subnets, while the Kubernetes Service remains `ClusterIP`; no NodePort is needed. Security groups on the pod ENIs/nodes accept the app port from the ALB security group. NetworkPolicy separately limits which traffic can reach the selected pods.

The Kubernetes API has a private endpoint and a public endpoint restricted to the sandbox operator's `/32`, allowing CLI access from the test workstation. This management path is separate from the ALB request path. For a private-only production design, operators would connect through a VPN, Direct Connect, or a trusted in-VPC runner. They authenticate with an individual IAM role and receive namespace or cluster permissions through an EKS access entry plus Kubernetes RBAC. Application pods use a separate Kubernetes service account associated with an AWS role through EKS Pod Identity. Human permissions and workload permissions are separate paths.

Control-plane audit/authenticator logs go to CloudWatch Logs. CloudTrail records AWS API activity such as role and access-entry changes. GuardDuty EKS Protection analyzes supported Kubernetes audit signals, while Runtime Monitoring adds host/runtime signals. These are evidence and detection layers; they do not block traffic by themselves. Application, ALB, and WAF logs are separate sources and must be enabled/configured where needed.

### Four security paths

The application request path is only one part of cluster security. Trace these flows separately:

| Flow | Typical path | Main authorization boundary |
|---|---|---|
| User request | Client → ALB → target group → pod | Listener rules, security groups, NetworkPolicy, application authorization |
| Human management | Engineer/CI → IAM role → EKS API → access entry → RBAC/admission | IAM authentication and Kubernetes/EKS authorization |
| Workload to AWS | Pod → ServiceAccount → Pod Identity/IRSA → IAM role → AWS API | Trust policy and least-privilege IAM policy |
| Detection and response | CloudTrail/EKS/Flow/runtime/app logs → alert → responder | Retention, integrity, ownership, and tested runbook |

### Request path, hop by hop

| Hop | What happens | Boundary to verify |
|---|---|---|
| 1. Client to DNS | The user resolves the AWS ALB DNS name, or a Route 53 record if configured. | The hostname points to the intended ALB, not a node address. |
| 2. DNS to edge | The browser connects over HTTPS to the ALB; AWS WAF can evaluate requests if associated. | ACM certificate, HTTPS listener, optional WAF association, and intended client CIDRs. |
| 3. ALB to pod | The ALB target group forwards to healthy pod IPs on the application port. | Targets are pod IPs; pod ENI/node security-group ingress names the ALB security group as source. |
| 4. Service and pod boundary | The `ClusterIP` Service selects ready app pods; NetworkPolicy allows the required ALB and in-cluster paths. | Service selector matches pod labels; readiness probe passes; unrelated namespaces remain blocked. |
| 5. Pod to other workloads | NetworkPolicy allows only the explicitly designed paths, such as frontend to web and DNS. | Confirm the VPC CNI policy agent is enforcing rules; applying YAML alone is not proof. |
| 6. Pod to AWS | The pod obtains short-lived credentials through its Pod Identity association. | The role trust and policy name the intended cluster, namespace, service account, and AWS resources. |

### Management and evidence paths

An operator first authenticates to AWS through IAM Identity Center or a federated IAM role. `aws eks update-kubeconfig` obtains cluster connection details; `kubectl` uses the role to authenticate. EKS maps that principal through an access entry, and Kubernetes authorization then evaluates the associated access policy or RBAC group binding. In this sandbox the public EKS API endpoint is restricted to the operator's `/32`; a private-only production design would make it reachable only from connected networks.

EKS control-plane logs show Kubernetes API and authentication activity. CloudTrail helps identify AWS API calls and IAM changes. VPC Flow Logs record accepted and rejected network metadata. GuardDuty can raise findings from supported EKS audit and runtime signals. Store these logs with deliberate retention and limit who can alter or delete them.

### Architecture decisions and trade-offs

- **Two Availability Zones:** spreads public ALB capacity and private nodes across AZs. Two NAT Gateways cost more but avoid a single-AZ egress dependency; one NAT Gateway is cheaper for a short-lived lab.
- **Private nodes:** prevents direct internet connections to node addresses. Nodes still need controlled egress to pull images and reach AWS APIs; NAT or the necessary VPC endpoints provide it.
- **Restricted cluster API:** the sandbox keeps the public endpoint limited to one trusted `/32` and also enables the private endpoint for VPC clients. A private-only endpoint further limits the management plane to connected operator networks but requires VPN, Direct Connect, or an in-VPC administration runner.
- **IP target mode:** sends traffic directly to pods and avoids NodePort. It requires VPC-routable pod IPs and security-group/NetworkPolicy rules that allow only the ALB path.
- **WAF and GuardDuty:** add request filtering and detection respectively, with separate costs and tuning needs. Neither replaces least privilege, network boundaries, or incident response.
- **Optional controls:** CloudFront, WAF, Network ACLs, Security Groups for Pods, image signatures, and automated EventBridge response are architecture choices. The modules identify prerequisites and trade-offs; they are not all deployed by the sandbox foundation.

The architecture diagram above is the reference view for this module. Use the later console captures to document your account's actual VPC, cluster, access, and traffic settings.

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
