---
title: "Chuẩn bị domain, ACM certificate và WAF"
weight: 50
chapter: false
pre: "<b>0.5.</b> "
---

## Mục tiêu chuẩn bị

Ứng dụng sẽ sử dụng hostname `notes.<domain>`. Certificate cần có trước khi tạo Ingress HTTPS; record ứng dụng trỏ đến ALB sẽ được tạo sau khi ALB xuất hiện.

## Xác nhận public hosted zone

1. Route 53 → **Hosted zones**, chọn public hosted zone của domain bạn quản lý. Ghi tên zone, ví dụ `example.com.`.
2. Đối chiếu NS records với nameservers được delegate ở domain cha/registrar. Nếu hosted zone đã được cấu hình, kiểm tra và giữ nguyên delegation đang sử dụng.
3. Trong terminal, đặt tên zone thực tế:

```bash
export DNS_ZONE_NAME='example.com.'
export APP_HOST="notes.${DNS_ZONE_NAME%.}"
printf '%s\n' "$APP_HOST"
```

Thay `example.com.` trước khi chạy. Domain hiện chưa cần có record ứng dụng; ACM sẽ tạo record DNS validation riêng.

## Yêu cầu certificate trên ACM

1. Mở **ACM tại us-east-1 → Request certificate → Request a public certificate**.
2. Domain name nhập hostname ứng dụng, ví dụ `notes.example.com`; chọn **DNS validation** và tạo request.
3. Mở certificate → **Create records in Route 53**, chọn domain cần xác thực và tạo validation record.
4. Đợi **Status: Issued**, validation **Success**. Copy certificate ARN để đối chiếu. Certificate phải cùng Region với ALB.

![Certificate của ứng dụng](/images/console-acm-certificate.png "① Issued. ② Domain. ③ DNS validation Success.")

## Tạo WAF Web ACL cho lab

1. WAF & Shield → **Web ACLs → Create web ACL**, tên `eks-did`, scope **Regional**, Region `us-east-1`.
2. Chọn default action **Allow**. ALB chưa được tạo nên chưa associate resource tại bước này.
3. Thêm custom rule tên `workshop-header-test`, loại regular rule, match **single header** `x-workshop-test`.
4. Match type **Exactly matches string**, string `block-me`, text transformation **None**, action **Block**. Bật sampled requests/metrics, lưu rule và Web ACL.
5. Copy Web ACL ARN. Script thu thập cấu hình sẽ tìm theo tên `eks-did`; controller gắn Web ACL vào ALB khi tạo Ingress.

![Rule kiểm chứng WAF](/images/console-waf-rule.png "① workshop-header-test. ② Action Block.")

Rule header này tạo ra một kết quả thử rõ ràng; việc lựa chọn managed rules cho production nằm ngoài cấu hình baseline. Nếu gặp lỗi thiếu quyền khi tạo WAF, kiểm tra quyền IAM và chính sách của tổ chức; chỉ kiểm chứng bước này sau khi tạo được Web ACL và gắn vào ALB.

## Kiểm tra trước khi triển khai ứng dụng

```bash
aws acm list-certificates --certificate-statuses ISSUED \
  --query 'CertificateSummaryList[].{Domain:DomainName,ARN:CertificateArn}'
aws wafv2 list-web-acls --scope REGIONAL \
  --query 'WebACLs[?Name==`eks-did`].{Name:Name,ARN:ARN}'
```

Cần thấy certificate đúng hostname và Web ACL `eks-did`. Chưa thử curl domain ở bước này vì chưa có ALB/record ứng dụng. Tiếp tục [cấp quyền workload](/preparation/6-workload-permissions/).
