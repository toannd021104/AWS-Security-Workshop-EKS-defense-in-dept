---
title: "What is Defense in Depth?"
weight: 1
chapter: false
pre: "<b>1.1.</b> "
---

Defense in Depth combines multiple protective layers to limit unauthorized access and reduce the impact when one layer is bypassed. Each layer controls a different boundary: connectivity, execution, permissions, or data.

In this application, requests pass through ALB to the frontend. The frontend calls the API, which stores notes in RDS and sends report requests to SQS. The worker receives those requests and writes results to the database. Each component needs different connections and permissions.

HTTPS protects the client-to-ALB connection. Security Groups restrict connections between AWS resources. NetworkPolicy further restricts traffic between cluster workloads. Pod Security Admission and SecurityContext control container execution settings, while IAM and RBAC determine permitted operations.

![Application security layers](/images/en/high-level.svg "Each workload has its own role. Apply security layers according to its access path and responsibilities.")

For example, the frontend only needs the API and should not connect directly to RDS. If the frontend container is compromised, that boundary reduces its access to the database. The API sends messages to SQS but does not need to receive or delete them; those operations belong to the worker.

Test these layers together. After allowing frontend-to-API traffic, try a pod outside the application and confirm it is blocked. After restricting the API's AWS permissions, saving notes and requesting reports must still work.

This workshop focuses on these controls on Amazon EKS. Next, identify the boundaries that need protection across AWS and Kubernetes.
