---
title: "Defense in Depth là gì?"
weight: 1
chapter: false
pre: "<b>1.1.</b> "
---

Defense in Depth là cách phối hợp nhiều lớp bảo vệ để hạn chế khả năng truy cập trái phép và giảm phạm vi ảnh hưởng khi một lớp bị vượt qua. Mỗi lớp kiểm soát một ranh giới khác nhau: kết nối mạng, quyền thực thi, quyền truy cập hoặc dữ liệu.

Trong ứng dụng của workshop, người dùng gửi request qua ALB đến frontend. Frontend gọi API; API lưu ghi chú trên RDS và gửi yêu cầu tạo báo cáo đến SQS. Worker nhận yêu cầu từ SQS và ghi kết quả vào database. Những thành phần này cần các kết nối và quyền khác nhau để hoàn thành công việc.

HTTPS bảo vệ kết nối từ người dùng đến ALB. Security Groups giới hạn kết nối giữa các tài nguyên AWS. NetworkPolicy tiếp tục giới hạn lưu lượng giữa workload trong cluster. Pod Security Admission và SecurityContext kiểm soát cấu hình thực thi của container, còn IAM và RBAC xác định các thao tác được phép.

![Các lớp bảo vệ trên kiến trúc ứng dụng](/images/high-level.svg "Mỗi workload có vai trò riêng; các lớp bảo vệ được áp dụng theo đường truy cập và trách nhiệm của workload.")

Ví dụ, frontend chỉ cần gọi API nên không được kết nối trực tiếp đến RDS. Nếu container frontend gặp sự cố, giới hạn này giúp thu hẹp đường truy cập sang database. API được gửi message vào SQS nhưng không cần nhận hoặc xóa message; những thao tác đó thuộc về worker.

Các lớp bảo vệ cần được kiểm tra cùng nhau. Sau khi cho phép frontend gọi API, cần thử thêm một pod không thuộc ứng dụng để xác nhận nó bị chặn. Sau khi giới hạn quyền AWS của API, chức năng lưu ghi chú và gửi yêu cầu báo cáo vẫn phải hoạt động.

Workshop tập trung vào các lớp bảo vệ này trên Amazon EKS. Phần tiếp theo xác định những ranh giới cần kiểm soát trong một hệ thống kết hợp AWS và Kubernetes.
