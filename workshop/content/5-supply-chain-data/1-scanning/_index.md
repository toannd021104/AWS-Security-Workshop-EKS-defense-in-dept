---
title: "Container Image Scanning với ECR & Inspector"
weight: 1
chapter: false
pre: "<b>5.1.</b> "
---

## Tìm lỗ hổng trước khi quyết định release

Image scanning tìm các package/dependency có vulnerability đã biết. Kết quả cần được đánh giá theo mức độ, khả năng khai thác, bản sửa và exception có thời hạn. Scan không tự ngăn Kubernetes chạy image.

### Console: basic và enhanced scanning

1. ECR → Private registry → Features & Settings → Scanning: xem loại scanning đang dùng. Basic scan tập trung OS packages; enhanced scanning tích hợp Inspector, có thể theo dõi cả language packages theo khả năng hỗ trợ.
2. Inspector → Activate → ECR scanning, nếu sandbox cho phép. Đây là cấu hình account/Region; review phạm vi trước khi đổi trong account dùng chung.
3. Chọn repository `eks-did/notes`, xem digest đã push và scan findings. Chờ scan hoàn tất; “không thấy findings” trong lúc pending không phải kết quả sạch.
4. Mở một finding, xem affected package, installed/fixed version và severity. Không đưa finding vào bài như bằng chứng exploit đã xảy ra.



![Ảnh AWS Console thực tế](/images/console-ecr.png "Repository thật: app image pin digest, Cosign signature artifact và unsigned image chỉ dùng negative test.")

### CLI/API: build rồi đọc findings

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

### Release gate có hành vi thật

```bash
python3 scripts/scan-gate.py
```

Script yêu cầu coverage đã scan, đọc findings của **đúng deployed digest**, trả exit 1 nếu có HIGH/CRITICAL hoặc chưa có coverage hoàn tất. [Kết quả scan thực tế](/evidence/image-scan.json) trong lượt lab ghi 4 HIGH, 8 MEDIUM, 2 LOW, 2 UNTRIAGED; 4 HIGH chưa có bản sửa theo Inspector. Gate trả `BLOCK`, không tự miễn trừ vì chưa có fix. App vẫn được dùng trong sandbox để kiểm tra network/identity; kết quả đó không phải phê duyệt release production.

Khi có bản vá, cập nhật base/dependency, build digest mới, scan lại rồi mới review gate. Đừng trộn kết quả scan image unsigned với image đang chạy.

### Terraform và gate

`aws_ecr_repository.app` bật immutable tags/basic scan; optional `aws_inspector2_enabler.ecr` bật ECR Inspector. Account có registry filters cần review để chắc repository lab nằm trong coverage. Tạo image mới với tag mới thay vì overwrite tag immutable.

Workshop ghi kết quả scan thực tế; không hứa “zero CVE”. Nếu muốn gate theo severity, thêm bước CI đọc findings rồi cho phép/từ chối release theo policy. Không gọi scan thành công là deploy bị chặn tự động.
