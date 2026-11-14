---
title: "A Layered Approach to Amazon EKS Security"
weight: 0
chapter: false
pre: ""
---

## Protect an application, one layer at a time

An application running on Amazon EKS still leaves security questions unanswered. Which pod receives a request from the Internet? Can the frontend connect directly to the database? Does the API need permission to receive messages processed by the worker?

This workshop uses **Notes**, an application for storing notes and generating reports, to answer those questions through configuration and practical tests. Start with a working HTTPS application, then examine its network path, restrict workload connections, narrow access permissions, and verify protection for images, secrets, and data.

After each change, save another note and generate a report. Both outcomes matter: legitimate operations must still work, and unnecessary connections or permissions must be denied.

Before each test, predict the result and identify the layer making the decision. Compare the output with your prediction: a timeout, `Forbidden`, and `AccessDenied` mean different things. By the end, you should explain both **why a legitimate request succeeds** and **why another operation is blocked**.

Click a Console screenshot or diagram to enlarge it. Choose **Original size** to read IP addresses, policies, and red callouts, then close the image to return to the lesson.

## What will you build and verify?

- Follow a request from the Internet through ALB to the frontend and API on EKS; compare listeners, target groups, and pod IPs.
- Restrict connections with Security Groups and NetworkPolicy; compare behavior before and after isolation.
- Check pod hardening, administrator access through IAM/RBAC, and dedicated AWS roles for the API and worker.
- Scan and sign images, test admission policies, and verify secret access and data encryption.

## One application throughout the workshop

The frontend serves the interface and forwards calls to the API. The API stores notes in RDS PostgreSQL and sends report requests to SQS. The worker receives those messages, processes them, and stores results in the database. All three workloads run on EKS; the database runs outside Kubernetes in RDS.

![Notes high-level architecture](/images/en/high-level.svg "Frontend, API, and worker have different responsibilities. Each exercise restricts connections and permissions according to those responsibilities.")

You do not build a different application in each chapter. The same request and business transactions reveal the effect of each security layer.

## Who is this workshop for?

Readers familiar with AWS and Kubernetes who want to secure an EKS application along its actual access path. Basic terminal and YAML skills are useful. Pod, Service, IAM, and Security Group concepts are revisited where they become relevant.

You need an **AWS account**, permissions to create the lab resources, and a public domain whose DNS you can configure. Preparation covers tools, VPC, cluster, and application deployment; it does not assume an existing lab.

## Learning path

| Part | Main task | Estimated time |
|---|---|---|
| [1. Introduction](/1-introduction/) | Understand the context, architecture, and security boundaries | 20–30 minutes |
| [Lab preparation](/preparation/) | Create infrastructure, deploy Notes, and check the baseline | 90–150 minutes |
| [2. Network Security](/2-network-security/) | Follow the request and verify AWS network controls | 60–90 minutes |
| [3. Kubernetes Security](/3-kubernetes-security/) | Restrict workload connections and execution privileges | 75–105 minutes |
| [4. Identity & Access Management](/4-identity/) | Verify human and application permissions | 60–90 minutes |
| [5. Supply Chain & Data Security](/5-supply-chain-data/) | Inspect images, admission, secrets, and encryption | 60–90 minutes |
| [Summary](/summary/) and [Cleanup](/cleanup/) | Compare evidence and remove resources | 15–30 minutes |

Allow **6–10 hours**, split across sessions if needed. These are planning estimates; provisioning time and your experience affect the actual duration.

Each part builds on the previous one. Start with **Introduction**, continue to **Lab preparation**, then complete chapters 2–5. Use **Previous / Next** or the left menu. AWS instructions prioritize Console; CLI/API supports Kubernetes operations and verification, with Terraform as an alternative infrastructure path.

> **Cost:** Resources are billed to your AWS account. Closing the browser does not stop them; complete [Cleanup](/cleanup/) when finished or when you will not continue the lab.

Download the [lab source ZIP](/downloads/eks-defense-in-depth-lab.zip). The [verification report](/validation/results/) records observed results from the reference lab. The [image scan](/evidence/image-scan.json) has a separate release gate that can block release even when the application works.
