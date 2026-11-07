---
title: "Kubernetes Networking: Pod, Service và Namespace"
weight: 1
chapter: false
pre: "<b>3.1.</b> "
---

## Vấn đề

Frontend cần gọi API ổn định dù pod API có thể được thay thế sau mỗi lần triển khai. Bài này xác định quan hệ giữa Pod, Service và EndpointSlice, đồng thời xem namespace tạo ra những ranh giới nào trong cluster.

## Kiến thức cần dùng

Pod là đơn vị chạy container, thường có IP riêng. Deployment có thể thay pod khi rollout, nên không hardcode pod IP trong Nginx. Service chọn pods bằng label; EndpointSlice thể hiện danh sách endpoints. Namespace nhóm resources và là phạm vi của nhiều policy, nhưng không tự tạo network isolation.

## Thực hiện

### Xem workloads và Services

EKS → cluster → Resources → Workloads → Deployments: frontend và API có hai replicas, worker có một. Trong Service and networking, hai Service `frontend`/`api` đều là ClusterIP. Worker không cần Service vì chỉ chủ động long-poll SQS.

## Kiểm chứng kết quả

### Đối chiếu Service selectors với endpoints

```bash
kubectl get pods -n notes -o wide --show-labels
kubectl get services -n notes
kubectl get endpointslices -n notes -l kubernetes.io/service-name=api
kubectl get deployment frontend -n notes -o yaml
```

Kiểm tra selector Service `app: api` trùng pod labels. Service port/targetPort lab đều 8080, tránh thêm một lần đổi port khi học traffic flow. Với VPC CNI policy engine cần đối chiếu các giới hạn port/protocol trong tài liệu phiên bản sử dụng.

```bash
kubectl exec -n notes deployment/frontend -- \
  wget -qO- http://api.notes.svc.cluster.local:8080/healthz
```

Mong đợi JSON health API. DNS name chọn Service, Service routing chọn endpoint healthy. Đối với ALB IP targets, Service vẫn là backend reference cho controller nhưng không phải hop trên traffic ALB → frontend.

![Giao diện ứng dụng chạy thật trên ALB HTTPS](/images/application-live.png "Ghi chú được lưu qua API vào RDS; báo cáo do worker xử lý qua SQS.")

### Điều gì namespace chưa làm?

Trước khi áp dụng policy, pod ở namespace khác vẫn có thể kết nối API nếu routing/security rules cho phép. Module 3.2 sẽ kiểm chứng điều đó rồi thu hẹp. Người có quyền tạo pod tùy ý có thể gắn label giống workload tin cậy, nên NetworkPolicy phải đi cùng RBAC; label không phải danh tính bất khả giả mạo.

Manifest đầy đủ được tạo bởi [render.py](/source/scripts/render.py); cấu hình Nginx và ứng dụng có trong nguồn tải về.

Đối chiếu selector `app: api`, labels của API pods và addresses trong EndpointSlice. Lệnh gọi health từ frontend trả JSON `workload: api` xác nhận DNS nội bộ và đường Service → pod cùng hoạt động.
