---
title: "Container Image Scanning với ECR & Inspector"
weight: 1
chapter: false
pre: "<b>5.1.</b> "
---

Image đã build và chạy được vẫn có thể chứa dependency có lỗ hổng đã biết. Bài này bật scanning, đọc kết quả của đúng image digest và thực hiện kiểm tra điều kiện phát hành trước khi chấp nhận image.

## Scan đúng image đang chạy

Image scanning tìm các package/dependency có vulnerability đã biết. Kết quả cần được đánh giá theo mức độ, khả năng khai thác, bản sửa và exception có thời hạn. Scan không tự ngăn Kubernetes chạy image.

## Bước 1: cấu hình scanning cho ECR

1. ECR → Private registry → Features & Settings → Scanning: xem loại scanning đang dùng. Basic scan tập trung OS packages; enhanced scanning tích hợp Inspector, có thể theo dõi cả language packages theo khả năng hỗ trợ.

2. Inspector → Activate → ECR scanning, với quyền quản lý Inspector trong tài khoản AWS. Đây là cấu hình account/Region; review phạm vi trước khi đổi trong account dùng chung.

3. Chọn repository `eks-did/notes`, xem digest đã push và scan findings. Chờ scan hoàn tất; “không thấy findings” trong lúc pending không phải kết quả sạch.

![Image tags và digest trong ECR](/images/console-ecr-images.png "① Image digest. ② Image tags.")

Chọn đúng digest đang triển khai trước khi mở findings. Các artifacts chữ ký và image chưa ký dùng cho phép thử admission không phải kết quả scan của image ứng dụng.

4. Mở một finding, xem affected package, installed/fixed version và severity. Không đưa finding vào bài như bằng chứng exploit đã xảy ra.

## Đọc findings và quyết định của release gate

### Đọc kết quả theo image digest

```bash
source scripts/env.sh
IMAGE=$(python3 scripts/deployed-image.py)
printf '%s\n' "$IMAGE"
aws ecr describe-images --repository-name eks-did/notes \
  --query 'imageDetails[].{digest:imageDigest,tags:imageTags,scan:imageScanStatus.status}'
```

Không build lại image ở bước quan sát này. Script đối chiếu digest trong `.local/image.txt` với Deployment và `imageID` của các pod API/worker đang Ready; nếu khác, dừng thay vì báo scan của image chưa triển khai. Muốn thử bản build khác, triển khai và kiểm tra baseline của bản đó trước khi ghi bằng chứng.

Enhanced scanning dùng Inspector APIs, lọc đúng hash thay vì gom findings của mọi image trong repository:

```bash
SCAN_FILTER=$(jq -cn --arg digest "${IMAGE##*@}" \
  '{ecrImageHash:[{comparison:"EQUALS",value:$digest}],findingStatus:[{comparison:"EQUALS",value:"ACTIVE"}]}')
aws inspector2 batch-get-account-status \
  --account-ids "$(aws sts get-caller-identity --query Account --output text)"
aws inspector2 list-findings --filter-criteria "$SCAN_FILTER" \
  --query 'findings[].{severity:severity,title:title}'
```

Basic scan APIs và Inspector có lifecycle/status khác nhau; không gọi `start-image-scan` như thể nó điều khiển enhanced scanning.

### Kiểm tra điều kiện phát hành

```bash
python3 scripts/scan-gate.py
```

Script yêu cầu coverage đã scan, đọc findings của **đúng deployed digest**, trả exit 1 nếu có HIGH/CRITICAL hoặc chưa có coverage hoàn tất. [Kết quả scan thực tế](/evidence/image-scan.json) ghi kết quả theo timestamp và digest. Lượt scan tham chiếu ngày 2026-11-13 (UTC) ghi 0 CRITICAL, 4 HIGH, 10 MEDIUM, 3 LOW, 0 UNTRIAGED; release gate **BLOCK**. Đọc timestamp, digest và coverage trong báo cáo để đối chiếu đúng lượt build; không suy ra kết quả của image khác hoặc một lần scan mới. Gate không tự miễn trừ HIGH/CRITICAL khi chưa có fix. Ứng dụng vẫn được dùng trong môi trường thực hành để kiểm tra network/identity; kết quả đó không phải phê duyệt release production.

Khi có bản vá, cập nhật base/dependency rồi build digest mới. Trước khi ký hoặc deploy, chạy `python3 scripts/scan-gate.py --candidate`: script kiểm tra repository/account và scan chính digest trong `.local/image.txt`, không yêu cầu digest đó đang chạy. Đợi Inspector hoàn tất coverage rồi chạy lại nếu gate đang BLOCK vì chưa có kết quả. Chỉ tiếp tục phát hành khi gate ALLOW; kết quả lưu riêng tại `evidence/candidate-image-scan.json`. Khi có HIGH/CRITICAL, tiếp tục sửa image thay vì bỏ qua gate. Sau rollout, chạy gate mặc định để đối chiếu image thực sự chạy. Đừng trộn bằng chứng candidate với deployed image.

### Cấu hình repository và scanning coverage

`aws_ecr_repository.app` bật immutable tags/basic scan; optional `aws_inspector2_enabler.ecr` bật ECR Inspector. Account có registry filters cần review để chắc repository lab nằm trong coverage. Tạo image mới với tag mới thay vì overwrite tag immutable.

Workshop ghi kết quả scan thực tế; không hứa “zero CVE”. Script gate của lab trả exit code để sử dụng trong quy trình phát hành. Việc scanning được bật riêng lẻ không tự chặn một deployment Kubernetes.

Điều kiện đạt của bài là xác định đúng deployed digest, chờ coverage hoàn tất và đọc đúng quyết định của gate. Gate `BLOCK` khi còn HIGH/CRITICAL là kết quả thực thi đúng policy; đó không phải kết luận image đã đủ điều kiện phát hành.
