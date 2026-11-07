---
title: "Supply Chain & Data Security"
weight: 6
chapter: false
pre: "<b>5.</b> "
---

Network và IAM đã thu hẹp đường truy cập, nhưng không trả lời image có lỗ hổng hay ai được phép lấy secret. Phần cuối chuyển từ kết nối và permissions sang đầu vào triển khai và dữ liệu mà ứng dụng sử dụng.

Scan đúng digest đang chạy, đọc release gate, tạo SBOM và chữ ký rồi thử admission bằng một image chưa ký. Tiếp theo kiểm tra master secret của RDS, quyền bootstrap và encryption context của KMS.

Kết quả scan phải được đánh giá riêng với chức năng ứng dụng: lab tham chiếu hiện có HIGH findings chưa có bản sửa và release gate trả BLOCK. Hoàn thành phần này rồi dùng [Tổng kết](/summary/) để đối chiếu toàn bộ bằng chứng trước khi cleanup.

## Các bài trong phần này

5.1. [Container Image Scanning với ECR & Inspector](/5-supply-chain-data/1-scanning/)

5.2. [SBOM, Image Signing & Admission Policies](/5-supply-chain-data/2-sbom-signing/)

5.3. [Kubernetes Secrets & AWS Secrets Manager](/5-supply-chain-data/3-secrets/)

5.4. [Data Encryption với AWS KMS](/5-supply-chain-data/4-encryption/)
