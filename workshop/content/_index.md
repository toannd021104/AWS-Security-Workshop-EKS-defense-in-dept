---
title: "Defense in Depth for Amazon EKS"
weight: 0
chapter: false
pre: ""
---

<span class="lab-tag">HANDS-ON WORKSHOP · AWS + KUBERNETES</span>

# Từ Internet đến pod: hiểu đường đi, xây từng lớp bảo vệ

Một website chạy được chưa chứng minh rằng các thành phần chỉ truy cập được đúng nơi cần thiết. Workshop này giúp bạn dựng một ứng dụng EKS, theo dõi request từ ALB đến pod, rồi giới hạn network và quyền của từng chủ thể.

Bạn đã biết AWS/Kubernetes nhưng quên một số khái niệm? Mỗi bài nhắc lại đúng kiến thức sắp dùng, giải thích lựa chọn và dẫn đến một thao tác có thể kiểm chứng. Không cần học thuộc danh sách dịch vụ trước khi bắt đầu.

![High-level architecture: ứng dụng, quản trị và workload identity](/images/high-level.svg "Ba workload: frontend, API, worker. RDS và SQS là dịch vụ managed.")

### Sau workshop, bạn làm được gì?

- Giải thích chính xác ALB target type `ip` đưa request đến pod như thế nào.
- Xây VPC hai AZ, EKS private workers, ALB HTTPS, RDS private và SQS.
- Giới hạn frontend → API → database; kiểm tra pod không liên quan bị chặn.
- Cấp quyền Kubernetes cho người vận hành và quyền AWS riêng cho API/worker.
- Áp dụng pod hardening, kiểm tra image, ký digest và đặt admission gate.
- Chứng minh bằng cả hành động được phép và hành động bị từ chối.

### Bắt đầu

Đọc [Chuẩn bị và cách dùng workshop](/preparation/) trước. [Tải mã lab ZIP](/downloads/eks-defense-in-depth-lab.zip) để chạy các bài thực hành; source Hugo được giữ cùng repository. Bạn chọn **một** cách tạo hạ tầng: Console, CLI/API hoặc Terraform. Các cách mô tả cùng thiết kế; không tạo lại cùng tài nguyên bằng cả ba.

| Module | Câu hỏi dẫn đường |
|---|---|
| [1. Introduction](/1-introduction/) | Mỗi lớp bảo vệ giải quyết khoảng trống nào? |
| [2. Network Security](/2-network-security/) | Request từ Internet đến private pod bằng đường nào? |
| [3. Kubernetes Security](/3-kubernetes-security/) | Pod được kết nối và chạy với đặc quyền gì? |
| [4. Identity & Access Management](/4-identity/) | Ai được thao tác Kubernetes và AWS? |
| [5. Supply Chain & Data Security](/5-supply-chain-data/) | Image nào được chạy, dữ liệu được bảo vệ ở đâu? |

Kết quả thực nghiệm được ghi riêng tại [Kiểm chứng và trạng thái sandbox](/validation/). Một bước có hướng dẫn không đồng nghĩa đã chạy thành công trong sandbox. Xem [Cleanup](/cleanup/) khi kết thúc; tài nguyên AWS tiếp tục tính phí khi bạn đóng trình duyệt.

Threat detection, GuardDuty, incident response và slide không thuộc phiên bản này.
