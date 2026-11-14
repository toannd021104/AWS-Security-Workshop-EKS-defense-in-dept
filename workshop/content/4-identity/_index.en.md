---
title: "Identity & Access Management – Securing Permissions"
weight: 5
chapter: false
pre: "<b>4.</b> "
---

Reaching an AWS endpoint does not authorize a pod to perform every API operation. Similarly, AWS authentication does not automatically authorize Kubernetes changes.

Follow two paths: humans to EKS API, and workloads to AWS services. Restrict the endpoint, map identities through Access Entries, grant read-only RBAC, and inspect API/worker Pod Identity and IAM policies.

The roles needed by Notes already exist from preparation. Test with real observer credentials and compare legitimate SQS operations with unauthorized ones. Identify both the denied principal and the layer making the decision.

## Lessons

4.1. [Authentication vs Authorization](/4-identity/1-authentication-authorization/)

4.2. [EKS API Endpoint Security](/4-identity/2-endpoint/)

4.3. [Human Access: AWS IAM & EKS Access Entries](/4-identity/3-human-access/)

4.4. [Kubernetes RBAC: Role, ClusterRole, and Bindings](/4-identity/4-rbac/)

4.5. [Workload Identity: IRSA vs EKS Pod Identity](/4-identity/5-workload-identity/)

4.6. [Least Privilege and IAM Policies](/4-identity/6-least-privilege/)
