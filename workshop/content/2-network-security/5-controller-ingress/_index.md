---
title: "AWS Load Balancer Controller và Kubernetes Ingress"
weight: 5
chapter: false
pre: "<b>2.5.</b> "
---

## Ingress là cấu hình, controller là bộ điều khiển

Ingress mô tả host/path/backend. AWS Load Balancer Controller theo dõi Ingress, Service và EndpointSlice rồi gọi ELB/EC2 APIs tạo ALB, listener, target group và rule SG. Controller không proxy từng HTTP request của ứng dụng.

### Console trước: kiểm tra quyền controller

IAM → Roles → `eks-did-controller`: trust principal `pods.eks.amazonaws.com`, actions `sts:AssumeRole` và `sts:TagSession`. EKS → Access → Pod Identity associations: namespace `kube-system`, ServiceAccount `aws-load-balancer-controller`, role trên. Policy lấy từ release controller, không dùng `AdministratorAccess`.

AWS Console không cung cấp trình soạn đầy đủ mọi Kubernetes resource. Vì vậy cài Helm chart và tạo Ingress bằng CLI là bước cần thiết.



![Ảnh AWS Console thực tế](/images/console-alb.png "ALB do controller tạo: Active, internet-facing và trải hai AZ.")

### CLI: cài controller và triển khai Ingress

Script [deploy.sh](/source/scripts/deploy.sh) pin chart `3.6.2`, truyền region và VPC ID để controller không cần lấy thông tin qua IMDS:

```bash
source scripts/env.sh
bash scripts/deploy.sh
kubectl -n kube-system rollout status deployment/aws-load-balancer-controller
kubectl -n notes get ingress notes -o yaml
```

Các annotation chính trong [render.py](/source/scripts/render.py):

```yaml
alb.ingress.kubernetes.io/scheme: internet-facing
alb.ingress.kubernetes.io/target-type: ip
alb.ingress.kubernetes.io/healthcheck-path: /healthz
alb.ingress.kubernetes.io/listen-ports: '[{"HTTP":80},{"HTTPS":443}]'
alb.ingress.kubernetes.io/ssl-redirect: '443'
```

Certificate ARN, public subnet IDs và WAF ARN được render từ cấu hình account, không hardcode ví dụ của người khác.

```bash
kubectl get ingress -n notes --watch
# Khi ADDRESS có hostname ALB, dừng watch bằng Ctrl-C.
python3 scripts/publish-dns.py
```

### Kiểm chứng và gotchas

EC2 Console phải thấy ALB và target group do controller quản lý; `curl https://$APP_HOST/` phải thành công sau khi DNS cập nhật. Nếu chưa có ALB, xem controller logs và events trước khi kiểm tra app. Không sửa ALB thủ công để “fix” cấu hình mà controller sẽ reconcile lại.

Quyền sửa Ingress cũng có thể thay đổi tài nguyên AWS. Lab không dùng shared IngressGroup; chỉ admin lab được tạo/sửa Ingress. IAM policy phiên bản được lưu tại [controller-policy.json](/source/terraform/controller-policy.json).
