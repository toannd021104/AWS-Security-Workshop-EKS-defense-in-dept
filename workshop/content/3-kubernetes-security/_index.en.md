---
title: "Kubernetes Security – Securing Workloads"
weight: 4
chapter: false
pre: "<b>3.</b> "
---

Security Groups now restrict AWS connections, but frontend and API still share an EKS cluster. A namespace organizes workloads; it does not automatically stop an unrelated pod calling the API.

Test connectivity before NetworkPolicy, add the necessary allow rules, then repeat the tests. Next inspect enforcement, Restricted admission, container privileges, and node metadata access.

The CNI policy agent was enabled during [EKS preparation](/preparation/3-eks/); lesson 3.3 explains that prerequisite. The frontend must still reach API and Notes must still save notes/process reports, while an unrelated pod is blocked. PSA and SecurityContext tests verify execution boundaries.

## Lessons

3.1. [Kubernetes Networking: Pod, Service, and Namespace](/3-kubernetes-security/1-networking/)

3.2. [Network Segmentation with Kubernetes NetworkPolicy](/3-kubernetes-security/2-networkpolicy/)

3.3. [NetworkPolicy Enforcement with Amazon VPC CNI](/3-kubernetes-security/3-vpc-cni/)

3.4. [Pod Security Standards & Pod Security Admission](/3-kubernetes-security/4-pod-security/)

3.5. [Container Hardening with SecurityContext](/3-kubernetes-security/5-securitycontext/)

3.6. [Worker Node Security and IMDSv2](/3-kubernetes-security/6-node-imds/)
