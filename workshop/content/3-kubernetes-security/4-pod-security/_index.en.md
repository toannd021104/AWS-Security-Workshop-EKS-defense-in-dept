---
title: "Pod Security Standards & Pod Security Admission"
weight: 4
chapter: false
pre: "<b>3.4.</b> "
---

A manifest can request root execution or unnecessary Linux privileges. Enforce Restricted in the application namespace to reject unsuitable pod configuration at admission.

## What does Restricted check?

Pod Security Standards define Privileged, Baseline, and Restricted levels. Pod Security Admission (PSA) enforces them through namespace labels. It does not scan image vulnerabilities or inspect HTTP requests.

## Step 1: inspect current settings

**EKS → Resources → Namespaces → notes**: inspect labels. Console may not edit every label, so make the following change through the Kubernetes API.

## Step 2: apply Restricted

```bash
kubectl label namespace notes \
  pod-security.kubernetes.io/enforce=restricted \
  pod-security.kubernetes.io/enforce-version=v1.35 \
  pod-security.kubernetes.io/audit=restricted \
  pod-security.kubernetes.io/warn=restricted --overwrite
```

Pinning the version makes standards upgrades explicit. Do not apply Restricted indiscriminately to `kube-system`: CNI and other system add-ons need elevated privileges.

## Test rejected and compliant workloads

### Submit a noncompliant manifest

```bash
kubectl run psa-negative -n notes --image=nginx:1.28-alpine \
  --dry-run=server -o yaml
```

The default pod lacks Restricted settings, so admission should reject it with explanations about non-root, seccomp, or capabilities. `--dry-run=server` runs admission without storing the pod; it neither bypasses admission nor runs host mounts.

### Check compliant workloads

```bash
kubectl get pods -n notes
kubectl get deployment api -n notes -o jsonpath='{.spec.template.spec.securityContext}'
```

Valid workloads remain Running/Ready after rollout. PSA labels do not evict every existing pod; review/redeploy to demonstrate compliant templates.

[render.py](/source/scripts/render.py) supplies pod-level and container-level `securityContext`. Next, examine what each field does.
