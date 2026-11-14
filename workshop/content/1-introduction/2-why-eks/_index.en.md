---
title: "Why does Amazon EKS need Defense in Depth?"
weight: 2
chapter: false
pre: "<b>1.2.</b> "
---

Amazon EKS provides an AWS-managed Kubernetes control plane. Applications still depend on network configuration, worker nodes, container images, and access permissions. Managed Kubernetes therefore needs workload-specific controls.

A request crosses several boundaries. On AWS, ALB accepts the connection, Security Groups restrict traffic, and VPC routing provides connectivity. In the cluster, Services, pod labels, and NetworkPolicy determine how workloads communicate. Calls to SQS and RDS are also governed by IAM and database privileges.

Private subnets let worker nodes serve the application through ALB without public IPs. However, pods in the VPC may still communicate without additional restrictions. A dedicated API role is only useful if the pod cannot obtain broader permissions from its worker node.

The lab separates three workloads by responsibility. The frontend serves the interface and forwards API calls. The API performs synchronous business operations. The worker processes reports in the background and exposes no user endpoint. RDS runs outside the cluster as a managed service.

This separation supports precise boundaries: no application AWS role for the frontend; send-only access to the lab queue for the API; receive/delete access to that queue for the worker. PostgreSQL permissions also differ between API and worker.

The following chapters implement and verify those boundaries. The sample application teaches networking and authorization and has no end-user login; use test data only.
