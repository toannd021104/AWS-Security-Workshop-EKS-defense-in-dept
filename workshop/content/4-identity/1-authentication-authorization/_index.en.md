---
title: "Authentication vs Authorization"
weight: 1
chapter: false
pre: "<b>4.1.</b> "
---

Operators use kubectl, while API and worker call AWS services. Different authentication and authorization systems handle those activities. Distinguish them to identify why a request succeeds or fails.

## Two access decisions

Authentication identifies the principal. Authorization determines its allowed actions and resources. Both questions arise in Kubernetes, AWS APIs, and PostgreSQL, but different systems answer them.

| Operation | Authentication | Authorization |
|---|---|---|
| Operator runs `kubectl get pods` | EKS IAM authentication | EKS access policy / Kubernetes RBAC |
| API sends an SQS message | AWS temporary credentials | IAM and queue resource policy |
| API writes to RDS | IAM DB token | `rds-db:connect` and PostgreSQL grants |
| User reads notes | Not implemented in demo | Not implemented; do not use sensitive data |

## Step 1: compare identities

Inspect the API IAM role and observer Access Entry in their respective Consoles. Then distinguish the terminal's AWS principal from Kubernetes permissions.

## Verify identity and permissions

### Observe current access

In the administrator terminal:

```bash
aws sts get-caller-identity
kubectl auth can-i list pods -n notes
kubectl auth can-i get secrets -n notes
```

An administrator may receive `yes` for both permissions. That proves nothing about observer restrictions; lesson 4.4 tests real observer credentials.

### Identify the rejection layer

A network timeout is not `AccessDenied`. Kubernetes returns `Forbidden` when a received request lacks required authorization. AWS returns an authorization error for insufficient permission or explicit deny. PostgreSQL may accept a connection and reject a particular SQL statement.

Terraform creates roles and Access Entries; Role/RoleBinding YAML defines Kubernetes verbs. Do not change NetworkPolicy to resolve `sqs:SendMessage AccessDenied`, or add IAM permissions to fix a connection timeout.

`get-caller-identity` identifies the terminal AWS principal. `kubectl auth can-i` tests the currently selected Kubernetes identity. Retain the admin result for comparison in 4.4; it is not observer evidence.
