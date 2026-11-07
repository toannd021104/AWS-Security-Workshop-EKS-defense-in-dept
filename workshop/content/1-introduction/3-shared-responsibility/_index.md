---
title: "AWS Shared Responsibility Model"
weight: 3
chapter: false
pre: "<b>1.3.</b> "
---

AWS Shared Responsibility Model phân chia trách nhiệm bảo mật giữa AWS và người sử dụng dịch vụ. Với Amazon EKS, AWS vận hành hạ tầng của Kubernetes control plane. Người dùng quản lý cách truy cập cluster và cấu hình các workload chạy trên đó.

Workshop sử dụng EKS managed node groups. AWS cung cấp cơ chế tạo và cập nhật node group; người vận hành vẫn lựa chọn phiên bản, lên lịch cập nhật, cấu hình IAM role và kiểm soát truy cập EC2 Instance Metadata Service. Ranh giới này khác với các lựa chọn compute như Fargate hoặc EKS Auto Mode.

![Thông tin cluster EKS thực tế](/images/console-eks.png "Cluster của lab sử dụng EKS 1.35. AWS quản lý control plane; cấu hình truy cập và workload thuộc trách nhiệm của người triển khai.")

| Thành phần | AWS quản lý | Người dùng cấu hình |
|---|---|---|
| EKS control plane | Hạ tầng và vận hành control plane | Endpoint access, Access Entries và authorization |
| Managed node group | Cơ chế provisioning và update | AMI release, rollout cập nhật, IAM role, IMDS và workload placement |
| VPC | Hạ tầng mạng AWS | Subnets, route tables, Security Groups và NACLs |
| Kubernetes workload | Nền tảng dịch vụ bên dưới | Image, SecurityContext, NetworkPolicy và workload identity |
| RDS | Hạ tầng database managed | Network access, users, SQL grants, backup và encryption settings |

Ví dụ, RDS hỗ trợ mã hóa storage và quản lý master credentials, nhưng người triển khai phải lựa chọn cấu hình phù hợp và giới hạn quyền truy cập. EKS hỗ trợ NetworkPolicy qua VPC CNI, nhưng policy chỉ có hiệu lực khi tính năng thực thi được bật và các rule được khai báo đúng.

Khi đọc kiến trúc ở bài tiếp theo, mỗi ranh giới bảo mật sẽ gắn với một thành phần và một trách nhiệm cụ thể. Đây là cơ sở để xác định cấu hình cần thực hiện trong các bài thực hành.
