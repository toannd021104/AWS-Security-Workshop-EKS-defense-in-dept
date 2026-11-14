---
title: "Network Security – Securing the Request Path"
weight: 3
chapter: false
pre: "<b>2.</b> "
---

Notes already works through its HTTPS domain. Now explain why an Internet request reaches a frontend in a private subnet, and which connections the AWS network layer permits.

Start with a real request, compare ALB targets with pod IPs, then trace subnets, routes, and Security Groups. Check HTTPS, WAF, and how the controller manages backends. Infrastructure already exists from preparation; each lesson distinguishes inspection from configuration changes.

Complete the [baseline](/preparation/8-baseline/) first. By the end, verify both a normal HTTPS 200 and a WAF test 403. Chapter 3 continues with pod-level isolation.

## Lessons

2.1. [Request Flow: Internet → ALB → Pod](/2-network-security/1-request-flow/)

2.2. [VPC Architecture: Public & Private Subnets, Routing, NAT Gateway](/2-network-security/2-vpc/)

2.3. [Edge Security: AWS WAF, ALB, and HTTPS](/2-network-security/3-edge/)

2.4. [Network Access Control: Security Groups & NACLs](/2-network-security/4-security-groups/)

2.5. [AWS Load Balancer Controller and Kubernetes Ingress](/2-network-security/5-controller-ingress/)

2.6. [ALB Target Types: Instance vs IP](/2-network-security/6-target-types/)
