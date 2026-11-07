---
title: "A Layered Approach to Amazon EKS Security"
weight: 0
chapter: false
pre: ""
---

<span class="lab-tag">AWS · KUBERNETES · HANDS-ON WORKSHOP</span>

# A Layered Approach to Amazon EKS Security

*Từ Internet đến Pod: xây dựng và kiểm chứng từng lớp bảo mật.*

## Tổng quan

Workshop này trình bày cách bảo vệ một ứng dụng trên Amazon EKS theo từng lớp, bắt đầu từ đường truy cập qua ALB, tiếp tục đến kết nối giữa các pod và quyền truy cập dịch vụ AWS. Các bài thực hành kết hợp cấu hình AWS với cơ chế bảo mật của Kubernetes trên cùng một hệ thống.

Ứng dụng mẫu gồm frontend, API và worker. Ghi chú được lưu trên RDS PostgreSQL; yêu cầu tạo báo cáo được gửi qua SQS để worker xử lý. Kiến trúc này được sử dụng xuyên suốt workshop để giải thích các quyết định về network, workload và permissions.

![High-level architecture của ứng dụng](/images/high-level.svg "Frontend nhận request; API xử lý nghiệp vụ; worker xử lý báo cáo qua SQS. Database sử dụng RDS bên ngoài cluster.")

Phần đầu giới thiệu nguyên tắc bảo mật nhiều lớp và kiến trúc EKS. Các phần tiếp theo triển khai những kiểm soát cụ thể: HTTPS/WAF, Security Groups, NetworkPolicy, pod hardening, IAM/RBAC và bảo vệ image, secrets, dữ liệu. Mỗi bài thực hành nêu vấn đề, giải thích kiến thức cần dùng, thực hiện cấu hình và kiểm chứng kết quả.

Đọc [Chuẩn bị thực hành](/preparation/) trước khi tạo tài nguyên. Workshop sử dụng tài nguyên AWS có tính phí; thực hiện [Cleanup](/cleanup/) khi kết thúc. Mã thực hành có trong [gói lab ZIP](/downloads/eks-defense-in-depth-lab.zip).

## Nội dung

1. [Introduction to Defense in Depth](/1-introduction/)

2. [Network Security — Securing the Request Path](/2-network-security/)

3. [Kubernetes Security — Securing Workloads](/3-kubernetes-security/)

4. [Identity & Access Management — Securing Permissions](/4-identity/)

5. [Supply Chain & Data Security](/5-supply-chain-data/)

[Kết quả kiểm chứng trên sandbox](/validation/results/) và [kết quả image scan](/evidence/image-scan.json) được công bố riêng. Các phép thử chức năng đạt không thay thế điều kiện chấp nhận image trước khi phát hành.
