---
title: "A Layered Approach to Amazon EKS Security"
weight: 0
chapter: false
pre: ""
---

## Bảo vệ một ứng dụng, từng lớp một

Một ứng dụng chạy được trên Amazon EKS chưa trả lời hết các câu hỏi về bảo mật. Request từ Internet đi vào pod nào? Frontend có thể kết nối thẳng đến database không? API có cần quyền nhận message mà worker đang xử lý không?

Workshop này sử dụng **Notes**, một ứng dụng lưu ghi chú và tạo báo cáo, để trả lời từng câu hỏi bằng cấu hình và phép thử thực tế. Bắt đầu với ứng dụng hoạt động qua HTTPS, các bài tiếp theo lần lượt kiểm tra đường mạng, giới hạn kết nối giữa workload, thu hẹp quyền truy cập và kiểm chứng cách bảo vệ image, secrets, dữ liệu.

Sau mỗi thay đổi, chạy lại luồng lưu ghi chú và tạo báo cáo. Kết quả cần đạt gồm hai phần: thao tác hợp lệ vẫn hoạt động, còn kết nối hoặc quyền không cần thiết bị từ chối.

## Bạn sẽ thực hiện những gì?

- Lần theo request từ Internet qua ALB đến frontend và API trên EKS; đối chiếu listener, target group và pod IP.
- Giới hạn đường kết nối bằng Security Groups và NetworkPolicy, rồi so sánh trước và sau khi áp dụng policy.
- Kiểm tra pod hardening, quyền quản trị qua IAM/RBAC và AWS role riêng cho API, worker.
- Scan và ký image, thử admission policy, kiểm tra quyền truy cập secrets và mã hóa dữ liệu.

## Ứng dụng xuyên suốt workshop

Frontend phục vụ giao diện và chuyển lời gọi đến API. API lưu ghi chú trong RDS PostgreSQL; khi có yêu cầu tạo báo cáo, API gửi message đến SQS. Worker nhận message, xử lý và lưu kết quả vào database. Ba workload chạy trên EKS; database nằm ngoài cluster, sử dụng RDS.

![Kiến trúc tổng quan của Notes](/images/high-level.svg "Frontend, API và worker có nhiệm vụ riêng. Các bài thực hành lần lượt giới hạn kết nối và quyền theo những nhiệm vụ đó.")

Không cần xây một ứng dụng mới ở mỗi chương. Cùng một request và cùng một luồng nghiệp vụ được dùng để kiểm tra tác động của các lớp bảo vệ.

## Workshop dành cho ai?

Người đã làm quen với AWS và Kubernetes, muốn thực hành bảo mật một ứng dụng EKS theo đường truy cập thực tế. Nên biết cách dùng terminal và đọc YAML cơ bản; khái niệm Pod, Service, IAM, Security Groups được nhắc lại tại bước cần sử dụng.

Cần một **tài khoản AWS**, quyền tạo các tài nguyên của lab và domain public có thể cấu hình DNS. Phần chuẩn bị hướng dẫn từ công cụ, VPC và cluster đến triển khai ứng dụng; không giả định bạn đã có lab chạy sẵn.

## Lộ trình thực hành

| Phần | Công việc chính | Thời gian dự kiến |
|---|---|---|
| [1. Introduction](/1-introduction/) | Hiểu bối cảnh, kiến trúc và các ranh giới bảo vệ | 20–30 phút |
| [Chuẩn bị lab](/preparation/) | Tạo hạ tầng, triển khai Notes và kiểm tra baseline | 90–150 phút |
| [2. Network Security](/2-network-security/) | Theo request và kiểm tra lớp mạng AWS | 60–90 phút |
| [3. Kubernetes Security](/3-kubernetes-security/) | Giới hạn kết nối và quyền thực thi workload | 75–105 phút |
| [4. Identity & Access Management](/4-identity/) | Kiểm chứng quyền của người dùng và ứng dụng | 60–90 phút |
| [5. Supply Chain & Data Security](/5-supply-chain-data/) | Kiểm tra image, admission, secrets và encryption | 60–90 phút |
| [Tổng kết](/summary/) và [Cleanup](/cleanup/) | Đối chiếu bằng chứng và gỡ tài nguyên | 15–30 phút |

Dự trù khoảng **6–10 giờ**, có thể chia thành nhiều buổi. Đây là ước lượng để lên kế hoạch; thời gian tạo tài nguyên và kinh nghiệm thao tác sẽ ảnh hưởng thời lượng thực tế.

Mỗi phần sử dụng kết quả của phần trước. Bắt đầu với **Introduction**, tiếp tục **Chuẩn bị lab**, rồi thực hành chương 2–5. Dùng nút **Trước / Tiếp** ở cuối trang hoặc menu bên trái để di chuyển. Các bước AWS ưu tiên Console; CLI/API hỗ trợ thao tác Kubernetes và kiểm tra kết quả, Terraform là nhánh triển khai thay thế.

> **Chi phí:** Các tài nguyên AWS do bạn tạo được tính phí theo tài khoản đang sử dụng. Đóng trình duyệt không dừng tài nguyên; thực hiện [Cleanup](/cleanup/) khi kết thúc hoặc khi không tiếp tục lab.

Mã nguồn có trong [gói lab ZIP](/downloads/eks-defense-in-depth-lab.zip). [Báo cáo kiểm chứng](/validation/results/) ghi kết quả đã quan sát trên lab tham chiếu; [image scan](/evidence/image-scan.json) có gate riêng và có thể chặn release dù ứng dụng chạy được.
