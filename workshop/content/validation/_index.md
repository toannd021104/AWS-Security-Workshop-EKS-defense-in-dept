---
title: "Kiểm chứng và kết quả thực hành"
weight: 80
chapter: false
pre: ""
---

## Ý định và kết quả là hai thứ khác nhau

Hướng dẫn trong từng bài mô tả kết quả mong đợi. Báo cáo tại đây ghi những gì bộ kiểm tra thực sự quan sát. `PASS` chỉ áp dụng cho phép thử được nêu, không phải chứng nhận production-ready.

```bash
source scripts/env.sh
python3 scripts/verify.py
# Sau khi hoàn thành signing/admission và tạo unsigned image:
python3 scripts/verify.py --supply-chain
```

Bộ kiểm tra chạy app flow, WAF, network allow/deny, observer credentials, IAM deny, PostgreSQL grants, PSA, IMDS và KMS round-trip. Các bài kiểm tra không khai thác lỗ hổng hoặc chạy workload privileged.

Image scanning và release gate có [báo cáo riêng](/evidence/image-scan.json): gate có thể chặn release dù các test chức năng/phân quyền PASS. Tải [SBOM CycloneDX thực tế](/evidence/sbom.cdx.json) để xem thành phần image.

Xem [báo cáo thực nghiệm](/validation/results/) để biết test đã chạy và giới hạn. Script lưu log chi tiết trong `.local/` được gitignore; bản public chỉ lưu kết quả đã lọc.
