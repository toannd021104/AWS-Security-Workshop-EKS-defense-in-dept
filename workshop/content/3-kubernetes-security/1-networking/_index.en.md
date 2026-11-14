---
title: "Kubernetes Networking: Pod, Service, and Namespace"
weight: 1
chapter: false
pre: "<b>3.1.</b> "
---

The frontend needs a stable API address even when API pods are replaced. Examine Pod, Service, and EndpointSlice relationships, then distinguish namespace organization from isolation.

## Pod IPs, Services, and namespaces in Notes

A Pod runs containers and normally has its own IP. Deployments replace pods during rollout, so Nginx must not hardcode pod IPs. Services select pods by label; EndpointSlices record their endpoints. Namespaces group resources and scope many policies but do not create network isolation by themselves.

## Step 1: inspect workloads and Services

**EKS → cluster → Resources → Workloads → Deployments**: frontend/API have two replicas, worker has one. In Service and networking, `frontend` and `api` are ClusterIP Services. The worker only initiates SQS long polling and needs no Service.

## Verify Service backend selection

### Compare selectors and endpoints

```bash
kubectl get pods -n notes -o wide --show-labels
kubectl get services -n notes
kubectl get endpointslices -n notes -l kubernetes.io/service-name=api
kubectl get deployment frontend -n notes -o yaml
```

The API Service selectors must match the API pod labels, including `app: api` and `workshop-serving: "true"`. Lab Service port and targetPort are both 8080, avoiding an extra port translation. Check the selected CNI version's protocol/port limitations.

```bash
kubectl exec -n notes deployment/frontend -- \
  wget -qO- http://api.notes.svc.cluster.local:8080/healthz
```

Expect API health JSON. DNS selects the Service, and Service routing selects a healthy endpoint. For ALB IP targets, the Service is a controller backend reference rather than a data-path hop between ALB and frontend.

![Notes served through ALB HTTPS](/images/application-live.png "The API stores notes in RDS; the worker processes reports through SQS.")

### What has a namespace not done?

Before policy, a pod in another namespace can still reach API when routing/security rules permit. Lesson 3.2 demonstrates and narrows access. Someone allowed to create arbitrary pods can copy trusted labels, so NetworkPolicy must be paired with RBAC. A label is not an unforgeable identity.

[render.py](/source/scripts/render.py) generates the manifests; the source package includes Nginx and application configuration.

Compare API selectors, pod labels, and EndpointSlice addresses. Health JSON containing `workload: api` from the frontend confirms both internal DNS and Service-to-pod connectivity.
