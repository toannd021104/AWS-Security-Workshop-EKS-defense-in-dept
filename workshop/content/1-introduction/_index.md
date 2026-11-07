---
title: "Introduction to Defense in Depth"
weight: 1
chapter: false
pre: "<b>1.</b> "
---

Notes có ba workload nhưng chỉ frontend nhận request từ Internet. API cần database và queue; worker cần xử lý message và ghi kết quả. Những khác biệt này là điểm bắt đầu để xác định lớp bảo vệ cần đặt ở đâu.

Phần này giới thiệu Defense in Depth, trách nhiệm của AWS/người triển khai và hai góc nhìn kiến trúc: luồng nghiệp vụ tổng quan, sau đó là các thành phần AWS/Kubernetes thực hiện luồng đó. Chưa cần chạy lệnh.

Sau khi đọc kiến trúc, chuyển sang [Chuẩn bị lab](/preparation/) để tạo ứng dụng trước khi lần theo request ở chương 2.

## Các bài trong phần này

1.1. [Defense in Depth là gì?](/1-introduction/1-defense-in-depth/)

1.2. [Tại sao Amazon EKS cần Defense in Depth?](/1-introduction/2-why-eks/)

1.3. [AWS Shared Responsibility Model](/1-introduction/3-shared-responsibility/)

1.4. [Tổng quan kiến trúc và các Security Layers](/1-introduction/4-architecture/)
