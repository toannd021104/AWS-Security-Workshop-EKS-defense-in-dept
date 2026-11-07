---
title: "Container Image Scanning với ECR & Inspector"
weight: 1
chapter: false
pre: "<b>5.1.</b> "
---

## Vấn đề

Image đã build và chạy được vẫn có thể chứa dependency có lỗ hổng đã biết. Bài này bật scanning, đọc kết quả của đúng image digest và thực hiện kiểm tra điều kiện phát hành trước khi chấp nhận image.

## Kiến thức cần dùng

Image scanning tìm các package/dependency có vulnerability đã biết. Kết quả cần được đánh giá theo mức độ, khả năng khai thác, bản sửa và exception có thời hạn. Scan không tự ngăn Kubernetes chạy image.

## Thực hiện

### Cấu hình scanning cho ECR

1. ECR → Private registry → Features & Settings → Scanning: xem loại scanning đang dùng. Basic scan tập trung OS packages; enhanced scanning tích hợp Inspector, có thể theo dõi cả language packages theo khả năng hỗ trợ.

2. Inspector → Activate → ECR scanning, với quyền quản lý Inspector trong tài khoản AWS. Đây là cấu hình account/Region; review phạm vi trước khi đổi trong account dùng chung.

3. Chọn repository `eks-did/notes`, xem digest đã push và scan findings. Chờ scan hoàn tất; “không thấy findings” trong lúc pending không phải kết quả sạch.

![Image tags và digest trong ECR](/images/console-ecr-images.png "① Image digest. ② Image tags.")

Chọn đúng digest đang triển khai trước khi mở findings. Các artifacts chữ ký và image chưa ký dùng cho phép thử admission không phải kết quả scan của image ứng dụng.

4. Mở một finding, xem affected package, installed/fixed version và severity. Không đưa finding vào bài như bằng chứng exploit đã xảy ra.

## Kiểm chứng kết quả

### Đọc kết quả theo image digest

```bash
bash scripts/build-push.sh
IMAGE=$(cat .local/image.txt)
aws ecr describe-images --repository-name eks-did/notes \
  --query 'imageDetails[].{digest:imageDigest,tags:imageTags,scan:imageScanStatus.status}'
```

Enhanced scanning dùng Inspector APIs:

```bash
aws inspector2 batch-get-account-status \
  --account-ids "$(aws sts get-caller-identity --query Account --output text)"
aws inspector2 list-findings --filter-criteria \
  '{"ecrImageRepositoryName":[{"comparison":"EQUALS","value":"eks-did/notes"}],"findingStatus":[{"comparison":"EQUALS","value":"ACTIVE"}]}' \
  --query 'findings[].{severity:severity,title:title}'
```

Basic scan APIs và Inspector có lifecycle/status khác nhau; không gọi `start-image-scan` như thể nó điều khiển enhanced scanning.

### Kiểm tra điều kiện phát hành

```bash
python3 scripts/scan-gate.py
```

Script yêu cầu coverage đã scan, đọc findings của **đúng deployed digest**, trả exit 1 nếu có HIGH/CRITICAL hoặc chưa có coverage hoàn tất. [Kết quả scan thực tế](/evidence/image-scan.json) trong lượt lab ghi 4 HIGH, 8 MEDIUM, 2 LOW, 2 UNTRIAGED; 4 HIGH chưa có bản sửa theo Inspector. Gate trả `BLOCK`, không tự miễn trừ vì chưa có fix. Ứng dụng vẫn được dùng trong môi trường thực hành để kiểm tra network/identity; kết quả đó không phải phê duyệt release production.

Khi có bản vá, cập nhật base/dependency, build digest mới, scan lại rồi mới review gate. Đừng trộn kết quả scan image unsigned với image đang chạy.

### Cấu hình repository và scanning coverage

`aws_ecr_repository.app` bật immutable tags/basic scan; optional `aws_inspector2_enabler.ecr` bật ECR Inspector. Account có registry filters cần review để chắc repository lab nằm trong coverage. Tạo image mới với tag mới thay vì overwrite tag immutable.

Workshop ghi kết quả scan thực tế; không hứa “zero CVE”. Script gate của lab trả exit code để sử dụng trong quy trình phát hành. Việc scanning được bật riêng lẻ không tự chặn một deployment Kubernetes.

Điều kiện đạt của bài là xác định đúng deployed digest, chờ coverage hoàn tất và đọc đúng quyết định của gate. Gate `BLOCK` khi còn HIGH/CRITICAL là kết quả thực thi đúng policy; đó không phải kết luận image đã đủ điều kiện phát hành.
