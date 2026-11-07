---
title: "Tại sao Amazon EKS cần Defense in Depth?"
weight: 2
chapter: false
pre: "<b>1.2.</b> "
---

Amazon EKS cung cấp Kubernetes control plane được AWS quản lý. Ứng dụng chạy trên cluster vẫn phụ thuộc vào cách cấu hình mạng, worker nodes, container images và quyền truy cập. Vì vậy, việc sử dụng managed Kubernetes cần đi cùng các kiểm soát dành cho workload.

Một request đến ứng dụng đi qua nhiều ranh giới. Ở phía AWS, ALB nhận kết nối, Security Groups giới hạn lưu lượng và VPC cung cấp đường định tuyến. Khi request vào cluster, Kubernetes Service, pod labels và NetworkPolicy quyết định cách các workload kết nối. Các lời gọi đến SQS hoặc RDS tiếp tục chịu kiểm soát của IAM và quyền database.

Private subnet giúp worker nodes không cần public IP để phục vụ ứng dụng qua ALB. Tuy nhiên, các pod trong VPC vẫn có thể kết nối với nhau nếu chưa có cơ chế hạn chế. Tương tự, việc cấp IAM role riêng cho API chỉ phát huy tác dụng khi pod không lấy được quyền rộng hơn từ worker node.

Trong lab, ba workload được tách theo chức năng. Frontend phục vụ giao diện và chuyển request đến API. API thực hiện nghiệp vụ đồng bộ. Worker xử lý báo cáo ở phía sau, không mở endpoint cho người dùng. RDS được triển khai bên ngoài cluster bằng dịch vụ managed.

Cách phân chia này cho phép áp dụng các giới hạn cụ thể: frontend không có AWS role ứng dụng; API chỉ gửi vào queue của lab; worker nhận và xóa message từ queue đó. Quyền PostgreSQL cũng được tách theo công việc của API và worker.

Các chương tiếp theo lần lượt triển khai và kiểm chứng những giới hạn này. Ứng dụng mẫu phục vụ việc học network và phân quyền, chưa có cơ chế đăng nhập người dùng; chỉ sử dụng dữ liệu thử nghiệm trong lab.
