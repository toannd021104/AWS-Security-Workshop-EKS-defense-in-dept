---
title: "ALB Target Types: Instance vs IP"
weight: 6
chapter: false
pre: "<b>2.6.</b> "
---

An ALB target group can register EC2 instances or IP addresses. That choice changes the request path and backend configuration. Compare both, use IP targets here, and observe target updates during rollout.

## Two backend paths

| | Instance target | IP target — this lab |
|---|---|---|
| Registered target | EC2 instance ID | Pod IP |
| Receiving port | NodePort | Container/target port 8080 |
| Data path | ALB → node → Service routing → pod | ALB → pod IP |
| Suitable when | A node/NodePort design is required, or pod networking is not directly routable from ALB | VPC CNI pod IPs are routable from ALB; Fargate also requires IP targets |
| Observe | NodePort, kube-proxy/routing, node SG | EndpointSlice, pod readiness, target health, pod IP |

The lab chooses `ip` because VPC CNI private pod IPs are already VPC-routable, avoiding an unnecessary NodePort hop. Instance mode remains valid for architectures needing it.

## Step 1: inspect the target group

**EC2 → Target Groups**: select the group belonging to `eks-did-notes`. Confirm type `IP`, port 8080, and frontend pod IPs. During rollout, old IPs may be draining as new ones register.

![IP targets and health](/images/console-targets.png "① IP target type. ② HTTP:8080. ③ Healthy targets. ④ Registered pod IPs.")

## Verify pod IPs and rollout behavior

### Compare targets with pods

```bash
kubectl get pods -n notes -l app=frontend -o wide
kubectl get endpointslices -n notes -l kubernetes.io/service-name=frontend -o yaml
aws elbv2 describe-target-groups \
  --query 'TargetGroups[?starts_with(TargetGroupName, `k8s-notes`)].{arn:TargetGroupArn,type:TargetType,port:Port}'
export ALB_ARN=$(aws elbv2 describe-load-balancers --names eks-did-notes \
  --query 'LoadBalancers[0].LoadBalancerArn' --output text)
export TARGET_GROUP_ARN=$(aws elbv2 describe-target-groups --load-balancer-arn "$ALB_ARN" \
  --query 'TargetGroups[0].TargetGroupArn' --output text)
aws elbv2 describe-target-health --target-group-arn "$TARGET_GROUP_ARN"
```

Registered IPs should match frontend pod IPs and be `healthy`. The Service helps the controller discover backends, but ALB does not send traffic through its ClusterIP. Nginx-to-API **does** use Service DNS/ClusterIP.

### Perform a controlled rollout

```bash
kubectl rollout restart deployment/frontend -n notes
kubectl rollout status deployment/frontend -n notes
curl -fsS "https://$APP_HOST/" -o /dev/null
```

The controller should update targets as pods change. One successful curl does not prove zero downtime; availability testing requires continuous traffic measurement, readiness, and target-registration observation. Next, inspect connections inside the cluster.
