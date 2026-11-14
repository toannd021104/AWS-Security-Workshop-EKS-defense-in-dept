---
title: "Kiểm chứng và kết quả thực hành"
weight: 80
chapter: false
pre: ""
---

## Ý định và kết quả là hai thứ khác nhau

Chạy trang này sau khi hoàn thành NetworkPolicy, IAM/RBAC, PSA và KMS. Bộ kiểm tra tạo/xóa probe pods, tạo dữ liệu Notes/báo cáo và **áp dụng lại NetworkPolicy của lab**; vì vậy không dùng nó để ghi baseline trước cách ly. Dùng `network-proof.py --stage before` trong bài 3.2 cho phép thử baseline độc lập.

Hướng dẫn trong từng bài mô tả kết quả mong đợi. Báo cáo tại đây ghi những gì bộ kiểm tra thực sự quan sát. `PASS` chỉ áp dụng cho phép thử được nêu, không phải chứng nhận production-ready.

```bash
source scripts/env.sh
python3 scripts/verify.py
# Sau khi hoàn thành signing/admission và tạo unsigned image:
python3 scripts/verify.py --supply-chain
```

Bộ kiểm tra chạy app flow, WAF, network allow/deny, observer credentials, IAM deny, PostgreSQL grants, PSA, IMDS và KMS round-trip. Các bài kiểm tra không khai thác lỗ hổng hoặc chạy workload privileged.

Image scanning và release gate có [báo cáo riêng](/evidence/image-scan.json): gate có thể chặn release dù các test chức năng/phân quyền PASS. Tải [SBOM CycloneDX thực tế](/evidence/sbom.cdx.json) để xem thành phần image. [Ghi nhận review độc lập và phạm vi kiểm thử](/evidence/workshop-review.md) giải thích những lỗi đã sửa và giới hạn kiểm chứng.

## Review theo góc nhìn người học

[Review hai ngôn ngữ ban đầu ngày 2026-11-14](/evidence/learner-review-2026-11-14.md) và [kiểm tra local/trình duyệt](/evidence/bilingual-validation-2026-11-14.json) được thực hiện khi môi trường tham chiếu cũ đã dừng, chưa chạy lại AWS.

Sau đó, [lượt thực hành AWS mới cùng ngày](/evidence/live-learner-replay-2026-11-14.json) bắt đầu từ clone GitHub và Terraform state mới. Lượt này phát hiện EBS default key không còn tồn tại và lỗi 502 khi rollout frontend; source đã bổ sung key EBS rõ ràng, ALB readiness gates và thời gian shutdown. Sau sửa, 25/25 phép thử cuối đạt, network proof trước/sau đạt 4/4 và 5/5; 28/28 mẫu HTTP trong một rollout trả 200. [Chi tiết 59 khối lệnh đã chạy](/evidence/executed-command-blocks-2026-11-14.json) giữ cả lần lỗi ban đầu và kết quả chạy lại.

Phạm vi thực tế là nhánh Terraform và các bài vận hành, có bước khôi phục node group; chưa chạy mới toàn bộ nhánh Console. Cleanup đã xóa 65 tài nguyên Terraform và đạt 18/18 kiểm tra sau dọn dẹp, giữ lại hosted zone có sẵn; demo KMS key đang chờ xóa theo thời hạn bảy ngày. Timeout RDS ban đầu và recovery được ghi riêng trong báo cáo; kết quả không có nghĩa hướng dẫn gốc chạy thành công ngay lần đầu. [Báo cáo cũ ngày 2026-11-13](/evidence/archive/2026-11-13/verification.json) được lưu riêng; kết quả bên dưới mang timestamp của lượt mới.

## Đọc một kết quả bị từ chối

| Bằng chứng | Lớp đang kiểm tra | Điều kiện đối chứng |
|---|---|---|
| Header thử WAF trả HTTP 403 | WAF gắn ALB | Cùng URL không có header trả 200 |
| Pod untrusted kết nối API bằng IP bị timeout | NetworkPolicy | Probe frontend và nghiệp vụ API vẫn hoạt động |
| Observer nhận `Forbidden` khi đọc Kubernetes Secret | Kubernetes authorization | Cùng observer vẫn list được pods |
| API nhận `AccessDenied` khi ReceiveMessage | IAM action/resource của workload | API vẫn SendMessage, worker vẫn xử lý report |
| API insert reports gặp `InsufficientPrivilege` | PostgreSQL grants | API vẫn tạo/đọc ghi chú |
| Pod dry-run bị báo `violates PodSecurity` | Pod Security Admission | Manifest Restricted hợp lệ vẫn được chấp nhận |
| Digest chưa ký bị webhook từ chối | Image signature admission | Digest đã ký trong cùng repo được chấp nhận |

Tên lỗi không tự chứng minh nguyên nhân. Đọc đúng request, identity và đối chứng thành công trước khi kết luận lớp bảo vệ có hiệu lực. Lỗi hết hạn credentials hoặc dependency chưa sẵn sàng không được tính là negative test đạt.

Xem [báo cáo thực nghiệm](/validation/results/) để biết test đã chạy và giới hạn. Script lưu log chi tiết trong `.local/` được gitignore; bản public chỉ lưu kết quả đã lọc.
