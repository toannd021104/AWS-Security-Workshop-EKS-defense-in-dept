---
title: "Build image và triển khai ứng dụng lên EKS"
weight: 70
chapter: false
pre: "<b>0.7.</b> "
---

## Mục tiêu chuẩn bị

Bước này đưa source code thành các workload Kubernetes. API, worker và Job db-init sử dụng cùng image nhưng chạy chức năng khác nhau; frontend dùng Nginx. Database và queue đã được tạo bên ngoài cluster.

## Thu thập cấu hình account

Tại thư mục mã nguồn, kích hoạt virtual environment và khai báo đúng public zone:

```bash
source .venv/bin/activate
export AWS_PROFILE=guru AWS_REGION=us-east-1
export DNS_ZONE_NAME='example.com.'
# Thay example.com. bằng public hosted zone đã xác thực certificate.
source scripts/env.sh
python3 scripts/capture-config.py
```

Kết quả mong đợi:

```text
Saved .local/lab.json and .local/lab.env; no secret values are fetched.
```

Script đọc EKS, RDS, subnets, queue, ECR, certificate và hosted zone để tạo metadata cho account của bạn. Nó không cần Terraform state và không lấy giá trị master password. Nếu có nhiều public zones, `DNS_ZONE_NAME` giúp chọn đúng zone.

Nạp các biến vừa tạo:

```bash
source scripts/env.sh
printf 'App: %s\nVPC: %s\nECR: %s\n' "$APP_HOST" "$VPC_ID" "$ECR_REPO"
```

Bây giờ `APP_HOST` mới được nạp tự động từ `.local/lab.env`. Kết quả phải chứa hostname, VPC ID và ECR URI của lab đã tạo. File này chứa metadata hạ tầng và được giữ trong `.local/`.

## Build và push image lên ECR

```bash
bash scripts/build-push.sh
```

Script thực hiện bốn việc theo thứ tự: lấy ECR login token, Docker build `app/Dockerfile` cho `linux/amd64`, push bằng tag mới và lưu URI có digest vào `.local/image.txt`.

Dòng cuối có dạng:

```text
Pinned image: 123456789012.dkr.ecr.us-east-1.amazonaws.com/eks-did/notes@sha256:…
```

Mở **ECR → eks-did/notes → Images** để đối chiếu image vừa push. Tag giúp nhận diện lượt build; digest xác định nội dung image sẽ triển khai.

![Image trong ECR](/images/console-ecr-images.png "① Image digest. ② Image tags. Danh sách của bạn ban đầu chỉ có image vừa build; signature và image test xuất hiện ở chương 5.")

## Cài controller và triển khai manifests

```bash
bash scripts/deploy.sh
```

Đọc các công việc script thực hiện để đối chiếu với output:

| Bước trong script | Tài nguyên/kết quả |
|---|---|
| Cập nhật kubeconfig | Dùng cluster `eks-did`, file `.local/kubeconfig` |
| Helm install/upgrade controller | Chart `3.6.2`, namespace `kube-system`, ServiceAccount đã có Pod Identity association |
| Chạy `render.py` | Sinh `k8s/application.yaml` và `k8s/network-policies.yaml` theo metadata thực |
| Apply `application.yaml` | Tạo namespace, ConfigMap, ServiceAccounts, RBAC, Job, Deployments, Services và Ingress |
| Chờ Job `db-init` | Tạo schema, users `notes_api`/`notes_worker` và SQL grants trên RDS |
| Chờ rollout | Frontend 2 replicas, API 2 replicas, worker 1 replica |

Kết quả cần thấy gồm Job hoàn tất và các Deployment successfully rolled out. Script đã áp dụng cấu hình chạy non-root/Restricted cho app baseline, nhưng **chưa apply `network-policies.yaml`**. Các bài chương 3 giải thích các trường hardening và thực hành cách ly mạng trước/sau.

Kiểm tra riêng từng thành phần:

```bash
kubectl -n kube-system rollout status deployment/aws-load-balancer-controller
kubectl get job db-init -n notes
kubectl get deployments,pods,services,ingress -n notes
```

Job có completions `1/1`; Deployments có số ready `2/2`, `2/2`, `1/1`. Ingress cần có ADDRESS là DNS name của ALB. Nếu Job không hoàn tất, đọc `kubectl logs job/db-init -n notes`; nếu ALB chưa xuất hiện, đọc controller logs và Ingress events trước khi chuyển sang DNS.

## Tạo record ứng dụng và kiểm tra ALB

```bash
python3 scripts/publish-dns.py
```

Script UPSERT record CNAME cho hostname ứng dụng, trỏ đến hostname của ALB do Ingress tạo. Đây là record `notes`, khác với record DNS validation của ACM.

1. Route 53 → hosted zone → record `notes`: target là ALB của lab.
2. EC2 → Load Balancers → `eks-did-notes`: trạng thái Active; HTTP 80 redirect sang HTTPS 443, HTTPS listener forward đến target group frontend.
3. Target group → Targets: target type IP, backend HTTP:8080; chờ các frontend targets Healthy.

![ALB do controller tạo](/images/console-alb.png "① Load balancer Active, Application và internet-facing.")

![IP targets của frontend](/images/console-targets.png "① IP target type. ② HTTP:8080. ③ Healthy targets. ④ Pod IPs và port. Ảnh trong rollout có thể chứa target cũ Draining.")

**Kết quả cần có:** controller Ready, Job complete, ba Deployments đủ replicas, ALB Active, targets Healthy và record ứng dụng trỏ đúng ALB. Tiếp tục [kiểm tra ứng dụng baseline](/preparation/8-baseline/).
