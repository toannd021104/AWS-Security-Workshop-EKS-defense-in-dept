---
title: "Edge Security: AWS WAF, ALB và HTTPS"
weight: 3
chapter: false
pre: "<b>2.3.</b> "
---

## Ba thành phần giải quyết ba việc

ALB định tuyến HTTP, ACM cung cấp certificate cho TLS và WAF kiểm tra request HTTP. WAF gắn vào ALB, không phải một máy proxy đặt trước ALB.

### Console: cấp chứng chỉ và tạo một rule kiểm chứng được

1. Route 53 → chọn public hosted zone bạn quản lý. Dùng hostname `notes.<zone>`; không tạo hosted zone mới rồi bỏ qua delegation.
2. ACM tại **us-east-1** → Request public certificate → nhập hostname → DNS validation. Chọn Create records in Route 53; đợi **Issued**. Certificate phải cùng Region với ALB.
3. WAF → Web ACLs → Create → Regional, tên `eks-did`. Default action Allow.
4. Thêm custom rule `workshop-header-test`, match **single header** `x-workshop-test`, exactly matches `block-me`, transformation None, action Block. Bật sampled requests/metrics.
5. Ingress ở 2.5 dùng ARN certificate và ARN Web ACL. Sau khi ALB xuất hiện, kiểm tra WAF resource association.

Rule header là bài test quyết định rõ ràng; nó không đại diện cho bộ rule production chống SQLi/XSS. Managed rules/rate limiting cần tuning và đánh giá false positives riêng.

### CLI/API: xác minh HTTPS và WAF

```bash
aws acm list-certificates --certificate-statuses ISSUED
curl -sS -o /dev/null -w '%{http_code}\n' "http://$APP_HOST/"
curl -sS -o /dev/null -w '%{http_code}\n' "https://$APP_HOST/"
curl -sS -o /dev/null -w '%{http_code}\n' -H 'x-workshop-test: block-me' "https://$APP_HOST/"
```

Mong đợi HTTP redirect, HTTPS 200, request có header 403. Không dùng `curl -k`: lệnh phải xác minh certificate và hostname.

Nếu dùng CLI thay Console để yêu cầu cert:

```bash
aws acm request-certificate --domain-name "$APP_HOST" --validation-method DNS
```

Sau đó đọc `describe-certificate`, tạo record validation và đợi `ISSUED`. Không yêu cầu lại cert nếu đã dùng Terraform. [Terraform WAF/ACM](/source/terraform/data-services.tf) chứa cấu hình đầy đủ.

### TLS kết thúc ở đâu?

Client → ALB dùng HTTPS với certificate ACM. TLS kết thúc tại ALB; ALB → frontend pod dùng HTTP port `8080`, và frontend → API cũng dùng HTTP. API/worker → RDS dùng TLS xác minh CA/hostname.

> **Lựa chọn của lab:** Giữ HTTP ở hai chặng nội bộ để đơn giản hóa cấu hình certificate, gia hạn và vận hành TLS. Các kết nối được giới hạn bằng Security Groups và NetworkPolicy. Những cơ chế này kiểm soát truy cập, **không mã hóa dữ liệu**; việc nằm trong mạng AWS không đồng nghĩa kết nối đã được mã hóa.

Thiết kế này **không mã hóa toàn bộ request path**. Nếu chính sách bảo mật hoặc yêu cầu tuân thủ đòi hỏi mã hóa các chặng nội bộ, cần cấu hình HTTPS từ ALB đến frontend và TLS cho frontend → API. ALB không xác thực certificate của HTTPS target; yêu cầu xác minh danh tính workload cần được thiết kế riêng.
