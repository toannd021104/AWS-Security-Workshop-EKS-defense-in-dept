---
title: "Introduction to Defense in Depth"
weight: 1
chapter: false
pre: "<b>1.</b> "
---

Notes has three workloads, but only the frontend receives Internet requests. The API needs the database and queue; the worker processes messages and writes results. These differences determine where protection belongs.

This section introduces Defense in Depth, AWS and customer responsibilities, and two architectural views: the business flow, followed by the AWS/Kubernetes components implementing it. No commands are required yet.

After reviewing the architecture, move to [Lab preparation](/preparation/) to build the application before following a request in chapter 2.

## Lessons

1.1. [What is Defense in Depth?](/1-introduction/1-defense-in-depth/)

1.2. [Why does Amazon EKS need Defense in Depth?](/1-introduction/2-why-eks/)

1.3. [AWS Shared Responsibility Model](/1-introduction/3-shared-responsibility/)

1.4. [Architecture and security layers](/1-introduction/4-architecture/)
