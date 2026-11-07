---
title: "Kiểm tra lab hoạt động trước khi học các lớp bảo vệ"
weight: 8
chapter: false
pre: "<b>0.8.</b> "
---

## Mục tiêu kiểm tra

Trước khi thử NetworkPolicy hoặc phân quyền nâng cao, xác nhận đường truy cập và nghiệp vụ của ứng dụng đang hoạt động. Kết quả baseline giúp phân biệt hành vi bị chặn có chủ đích với một thành phần chưa được triển khai đúng.

Các output dưới đây là mẫu; tên pod, IP, ID ghi chú và thời gian thay đổi theo lượt thực hành.

## Nạp cấu hình và kiểm tra frontend

```bash
source scripts/env.sh
printf 'Hostname: %s\n' "$APP_HOST"
curl -sS -o /dev/null -w '%{http_code}\n' "https://$APP_HOST/"
```

Ví dụ:

```text
Hostname: notes.example.com
200
```

`source` nạp cấu hình từ `.local/lab.env`, thường không tự in gì. `curl` bỏ nội dung HTML và chỉ in status 200. Kết quả xác nhận domain HTTPS truy cập được frontend qua ALB.

## Kiểm tra đường frontend → API

```bash
curl -fsS "https://$APP_HOST/api/healthz"
printf '\n'
```

Kết quả:

```json
{"status": "ok", "workload": "api"}
```

Request đã đến API qua Nginx frontend. Health endpoint chưa kiểm tra thao tác database, nên cần phép thử tiếp theo.

## Lưu và đọc lại ghi chú

```bash
curl -fsS "https://$APP_HOST/api/notes" \
  -H 'Content-Type: application/json' -d '{"body":"baseline-note"}'
printf '\n'
curl -fsS "https://$APP_HOST/api/notes"
printf '\n'
```

POST trả một object có `id` và `body`; GET trả danh sách chứa ghi chú vừa tạo:

```json
{"id": 1, "body": "baseline-note"}
```

```json
[{"id": 1, "body": "baseline-note"}]
```

ID thực tế có thể lớn hơn 1 và danh sách có thể đã có dữ liệu thử khác. Việc đọc lại đúng ghi chú xác nhận luồng API → RDS và quyền SQL cần thiết.

## Gửi yêu cầu báo cáo cho worker

```bash
curl -fsS -X POST "https://$APP_HOST/api/reports"
printf '\n'
```

Kết quả có dạng:

```json
{"id": "…", "status": "queued"}
```

Chờ worker xử lý rồi đọc lại:

```bash
curl -fsS "https://$APP_HOST/api/reports"
printf '\n'
kubectl logs deployment/worker -n notes --tail=10
```

GET phải có report cùng ID đã gửi, với số lượng ghi chú `note_count`. Nếu lượt GET đầu chưa có, thực hiện lại sau vài giây. Kết quả xác nhận đường API → SQS → worker → RDS hoạt động.

## Đối chiếu pod IP và access logs

```bash
kubectl get pods -n notes -l app=frontend -o wide
```

Ví dụ:

```text
NAME                        READY   STATUS    RESTARTS   AGE   IP
frontend-7c8d9f6b5d-abc12    1/1     Running   0          10m   10.20.44.78
frontend-7c8d9f6b5d-def34    1/1     Running   0          10m   10.20.54.165
```

Đối chiếu cột IP với targets Healthy trong ALB target group. `READY 1/1` cho biết container của pod đã sẵn sàng.

```bash
kubectl logs -n notes -l app=frontend --tail=10 --prefix=true
```

Ví dụ một phần access log:

```text
[pod/frontend-…/frontend] … "GET /api/healthz HTTP/1.1" 200 …
```

`--prefix=true` thêm tên pod/container để biết pod nào nhận request. Log còn có thể chứa health checks của ALB; số dòng cuối không bảo đảm chứa mọi request vừa gửi.

## Điều kiện hoàn thành chuẩn bị

| Kiểm tra | Kết quả cần đạt |
|---|---|
| EKS nodes | Hai nodes Ready, private IP |
| Job db-init | Complete |
| Deployments | Frontend 2/2, API 2/2, worker 1/1 |
| Domain và HTTPS | Trang chủ trả 200, certificate hợp lệ |
| API | Health trả `workload: api` |
| RDS | Đọc lại được ghi chú vừa tạo |
| SQS/worker | Nhận được report cùng ID đã gửi |
| NetworkPolicy baseline | Chưa áp dụng policies của chương 3 |

```bash
kubectl get networkpolicy -n notes
```

Ở một lab mới, kết quả cuối là `No resources found in notes namespace.` Nếu đang dùng lại lab đã harden, ghi nhận policies đã tồn tại; không coi đó là baseline trước policy.

![Ứng dụng đã triển khai](/images/application-live.png "Frontend, API và worker cùng hoạt động với RDS/SQS.")

Khi các điều kiện trên đạt, đọc [Request Flow: Internet → ALB → Pod](/2-network-security/1-request-flow/). Từ đây, các lệnh sử dụng `$APP_HOST` và pod ứng dụng đã có đầy đủ đầu vào để chạy.
