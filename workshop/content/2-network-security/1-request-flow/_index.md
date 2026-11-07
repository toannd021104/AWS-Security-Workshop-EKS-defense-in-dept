---
title: "Request Flow: Internet → ALB → Pod"
weight: 1
chapter: false
pre: "<b>2.1.</b> "
---

## Theo dõi một request thay vì đọc danh sách dịch vụ

![Request path từ client đến PostgreSQL](/images/request-path.svg "ALB gửi đến frontend pod IP; frontend gọi API qua Service nội bộ.")

Khi mở `https://notes.<domain>`, client phân giải DNS rồi mở TLS đến ALB. DNS không proxy HTTP. ALB kết thúc TLS, kiểm tra listener rule, chọn target healthy và mở kết nối HTTP riêng đến frontend pod `:8080`. Nginx nhận `/api/notes` và proxy đến `api.notes.svc.cluster.local:8080/notes`. API mở kết nối PostgreSQL TLS đến RDS `:5432`.

> **Lưu ý về mã hóa:** HTTPS kết thúc tại ALB. Chặng ALB → frontend pod dùng HTTP port `8080`; frontend → API cũng dùng HTTP. Lab giữ lựa chọn này để đơn giản hóa cấu hình certificate và vận hành TLS nội bộ. Security Groups và NetworkPolicy giới hạn các kết nối được phép, nhưng không mã hóa lưu lượng. Việc nằm trong mạng AWS không đồng nghĩa kết nối đã được mã hóa.

### Console: đối chiếu từng đoạn

1. Route 53 → Hosted zones → zone lab → record `notes`: điểm đến phải là ALB của lab.
2. EC2 → Load Balancers → `eks-did-notes` → Listeners: HTTP 80 redirect sang HTTPS 443; HTTPS forward đến target group frontend.
3. Target Groups → Targets: chọn IP target, xem port 8080 và health status.
4. EKS → Resources → Pods: so IP frontend với các target IP.

### CLI/API: gửi và theo dõi

```bash
source scripts/env.sh
curl -sS -o /dev/null -w '%{http_code}\n' "https://$APP_HOST/"
curl -fsS "https://$APP_HOST/api/healthz"
kubectl get pods -n notes -l app=frontend -o wide
kubectl logs -n notes -l app=frontend --tail=10
```

Mong đợi HTTP 200 và `workload: api` ở API health endpoint. Frontend access log có request tương ứng. Đó là hai phép kiểm tra khác nhau: trang chủ thành công chưa chứng minh API hay DB hoạt động.

```bash
curl -fsS "https://$APP_HOST/api/notes" \
  -H 'Content-Type: application/json' -d '{"body":"Hello from the request path"}'
curl -fsS "https://$APP_HOST/api/notes"
```

POST phải trả ID, GET phải có ghi chú. Không ghi chú thật hoặc dữ liệu nhạy cảm vì app chưa có user authentication.

### Giới hạn và bước tiếp theo

`X-Forwarded-For` mang IP client trong HTTP header; đây không nhất thiết là source IP mà NetworkPolicy thấy trên kết nối ALB → pod. Không dùng header để viết rule L3/L4. Các bài 2.2–2.6 sẽ giải thích mạng và target registration đằng sau đường đi này. Cấu hình có trong [render.py](/source/scripts/render.py).
