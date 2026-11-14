---
title: "AWS Shared Responsibility Model"
weight: 3
chapter: false
pre: "<b>1.3.</b> "
---

The AWS Shared Responsibility Model divides security responsibilities between AWS and the customer. For EKS, AWS operates the Kubernetes control plane infrastructure. You manage cluster access and the workloads running on it.

This workshop uses EKS managed node groups. AWS supplies node-group provisioning and update mechanisms; the operator still chooses versions, schedules updates, configures IAM roles, and controls EC2 Instance Metadata Service access. This boundary differs for compute choices such as Fargate or EKS Auto Mode.

![Reference EKS cluster](/images/console-eks.png "The lab uses EKS 1.35. AWS manages the control plane; access and workload configuration remain the deployer's responsibility.")

| Component | AWS manages | You configure |
|---|---|---|
| EKS control plane | Infrastructure and control plane operation | Endpoint access, Access Entries, and authorization |
| Managed node group | Provisioning and update mechanisms | AMI release, update rollout, IAM role, IMDS, and workload placement |
| VPC | AWS network infrastructure | Subnets, route tables, Security Groups, and NACLs |
| Kubernetes workload | Underlying service platform | Image, SecurityContext, NetworkPolicy, and workload identity |
| RDS | Managed database infrastructure | Network access, users, SQL grants, backups, and encryption settings |

RDS supports storage encryption and master credential management, but you must choose appropriate settings and limit access. EKS supports NetworkPolicy through VPC CNI, but policies only work when enforcement is enabled and rules are correct.

In the next architecture lesson, connect each security boundary to a component and a responsibility. This determines what you will configure in the exercises.
