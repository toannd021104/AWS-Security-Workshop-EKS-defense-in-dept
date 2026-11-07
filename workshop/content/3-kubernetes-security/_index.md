---
title: "Kubernetes Security – Securing Workloads"
weight: 4
chapter: false
pre: "<b>3.</b> "
---

Security Groups đã giới hạn kết nối ở lớp AWS, nhưng frontend và API vẫn cùng chạy trên EKS. Namespace giúp tổ chức workload; nó chưa tự ngăn một pod không liên quan gọi API.

Phần này kiểm tra kết nối trước khi áp dụng NetworkPolicy, thêm các allow rules cần thiết và chạy lại cùng phép thử. Sau đó kiểm tra cấu hình thực thi của policy, chuẩn Restricted, quyền container và đường truy cập metadata của node.

CNI policy agent đã được bật ở [bước tạo EKS](/preparation/3-eks/); bài 3.3 giải thích và đối chiếu điều kiện này. Kết quả cần đạt: frontend vẫn gọi API, Notes vẫn lưu ghi chú/tạo báo cáo, còn pod không liên quan bị chặn. Các kiểm tra PSA và SecurityContext xác nhận thêm giới hạn thực thi workload.

## Các bài trong phần này

3.1. [Kubernetes Networking: Pod, Service và Namespace](/3-kubernetes-security/1-networking/)

3.2. [Network Segmentation với Kubernetes NetworkPolicy](/3-kubernetes-security/2-networkpolicy/)

3.3. [NetworkPolicy Enforcement với Amazon VPC CNI](/3-kubernetes-security/3-vpc-cni/)

3.4. [Pod Security Standards & Pod Security Admission](/3-kubernetes-security/4-pod-security/)

3.5. [Container Hardening với SecurityContext](/3-kubernetes-security/5-securitycontext/)

3.6. [Worker Node Security và IMDSv2](/3-kubernetes-security/6-node-imds/)
