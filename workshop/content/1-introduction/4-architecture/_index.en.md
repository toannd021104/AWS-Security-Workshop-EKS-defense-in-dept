---
title: "Architecture and security layers"
weight: 4
chapter: false
pre: "<b>1.4.</b> "
---

The workshop application is a notes website on Amazon EKS, split into Nginx frontend, Python API, and Python worker workloads. RDS PostgreSQL stores data; SQS separates report generation from the user's synchronous request.

![Workshop AWS architecture](/images/en/aws-architecture.svg "ALB uses public subnets; worker nodes use private application subnets; RDS uses separate database subnets. Dashed frames represent network and logical boundaries.")

### Application request path

The browser resolves the domain and connects to ALB over HTTPS. ALB terminates TLS and forwards HTTP to frontend pod port 8080. Nginx serves the interface and forwards `/api/` requests to the API Kubernetes Service. The API connects to RDS over TLS using IAM database authentication as `notes_api`.

> **Encryption and connection protection:** HTTPS encrypts Internet-to-ALB traffic. ALB-to-frontend and frontend-to-API use HTTP over private VPC IPs. Security Groups restrict infrastructure connections; chapter 3 adds Kubernetes NetworkPolicy to restrict workload connections. This lab choice keeps the focus on EKS network and workload security. These access controls do not encrypt HTTP.

### Report processing

The API sends an SQS message when a report is requested. The worker polls the queue, reads the necessary data, and writes a report to RDS as `notes_worker`. SQS does not initiate inbound connections to the worker. The worker needs neither a public endpoint nor its own Kubernetes Service.

### Administration and permissions

Operators use `kubectl` to connect to the EKS API endpoint. This management path is separate from the website's ALB. IAM authenticates the identity; EKS Access Entries and Kubernetes RBAC authorize resource operations.

The API and worker use EKS Pod Identity to receive temporary AWS credentials according to their ServiceAccounts. They then call SQS or sign RDS authentication tokens. The frontend needs no application IAM role.

### Lab choices

ALB uses IP targets to reach pod IPs allocated by VPC CNI. NetworkPolicy controls workload traffic while node Security Groups protect AWS resources. Relevant chapters explain these choices and alternatives.

One NAT Gateway and Single-AZ RDS reduce lab costs. Production designs must reconsider availability requirements and private connectivity.

Download the editable [AWS diagram](/images/en/aws-architecture.drawio) and [high-level diagram](/images/en/high-level.drawio). Chapter 2 follows a request through this architecture.
