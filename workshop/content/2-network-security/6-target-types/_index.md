---
title: "ALB Target Types: Instance vs IP"
weight: 6
chapter: false
pre: "<b>2.6.</b> "
---

## Hai cách đều hợp lệ, nhưng data path khác nhau

| | Instance target | IP target — đường chính của lab |
|---|---|---|
| Target đăng ký | EC2 instance ID | Pod IP |
| Cổng nhận | NodePort | Container/target port 8080 |
| Data path | ALB → node → Service routing → pod | ALB → pod IP |
| Khi phù hợp | Thiết kế node targets/NodePort; pod network không trực tiếp routable từ ALB | VPC CNI và pod IP được ALB định tuyến tới; Fargate cũng yêu cầu IP targets |
| Cần quan sát | NodePort, kube-proxy/routing, node SG | EndpointSlice, pod readiness, target health, pod IP |

Lab chọn `ip` vì private pod IP của VPC CNI đã routable trong VPC, tránh bước NodePort không cần thiết. Đây là lựa chọn phù hợp kiến trúc hiện tại, không phải khẳng định instance mode luôn sai.

### Console: đối chiếu target với pod

EC2 → Target Groups → chọn target group của `eks-did-notes`. Target type phải `IP`, port 8080. EKS → Pods → frontend phải có các IP trùng với targets. Trong rollout có thể thấy IP cũ đang draining và IP mới đang đăng ký.



![Ảnh AWS Console thực tế](/images/console-targets.png "① IP target type và port 8080. ② Hai targets healthy. ③ Pod IPs; target test cũ có thể đang draining.")

### CLI/API: kiểm tra cơ chế

```bash
kubectl get pods -n notes -l app=frontend -o wide
kubectl get endpointslices -n notes -l kubernetes.io/service-name=frontend -o yaml
aws elbv2 describe-target-groups \
  --query 'TargetGroups[?starts_with(TargetGroupName, `k8s-notes`)].{arn:TargetGroupArn,type:TargetType,port:Port}'
# Export TARGET_GROUP_ARN từ kết quả trên.
aws elbv2 describe-target-health --target-group-arn "$TARGET_GROUP_ARN"
```

Mong đợi registered IPs là frontend pod IPs và health `healthy`. Service vẫn để controller tìm backend, nhưng ALB không phải gửi request qua Service ClusterIP. Ngược lại, Nginx → API **có dùng** Service DNS/ClusterIP.

### Thử rollout có kiểm soát

```bash
kubectl rollout restart deployment/frontend -n notes
kubectl rollout status deployment/frontend -n notes
curl -fsS "https://$APP_HOST/" -o /dev/null
```

Controller phải cập nhật targets theo pods mới. Không dùng một lần curl thành công làm bằng chứng “zero downtime”: kiểm chứng availability khi rollout cần liên tục đo traffic, readiness và target registration. Module kế tiếp đi vào các kết nối bên trong cluster.
