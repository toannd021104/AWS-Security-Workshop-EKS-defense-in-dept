---
title: "Request Flow: Internet → ALB → Pod"
weight: 1
chapter: false
pre: "<b>2.1.</b> "
---

Ứng dụng được truy cập qua một domain public, trong khi các pod nằm trong private subnets. Trước khi cấu hình các lớp bảo vệ, cần xác định request đi qua những thành phần nào và cách kiểm tra từng chặng. Bài này đối chiếu đường đi của request với cấu hình ALB, pod IP và kết quả đọc/ghi dữ liệu.

## Request đi qua những đâu?

![Request path từ client đến PostgreSQL](/images/request-path.svg "ALB gửi đến frontend pod IP; frontend gọi API qua Service nội bộ.")

Lấy ví dụ người dùng mở `https://notes.<domain>` để xem danh sách ghi chú. Trình duyệt cần tải giao diện trước, sau đó gọi API để lấy dữ liệu. Hai việc này đi qua các thành phần sau:

1. **DNS giúp trình duyệt tìm địa chỉ ALB.** Trình duyệt tra tên miền `notes.<domain>` để biết địa chỉ cần kết nối. DNS chỉ giúp tìm địa chỉ; request của ứng dụng được gửi đến ALB.

2. **ALB nhận kết nối HTTPS từ trình duyệt.** Người dùng truy cập bằng HTTPS trên cổng `443`. ALB xử lý phần mã hóa của kết nối này, sau đó chọn một frontend pod đang sẵn sàng và chuyển request đến pod đó bằng HTTP trên cổng `8080`.

3. **Frontend trả giao diện, rồi chuyển tiếp các lời gọi API.** Nginx trong frontend pod trả HTML và JavaScript cho trình duyệt. JavaScript tiếp tục gửi `GET /api/notes` để lấy danh sách ghi chú. Request này cũng đi qua ALB đến frontend, nhưng Nginx chuyển nó đến API thay vì trả một file giao diện.

4. **Kubernetes Service giúp frontend tìm API pod.** Nginx gọi Service `api` trong namespace `notes`, qua địa chỉ nội bộ `api.notes.svc.cluster.local:8080`. Khi chuyển tiếp, Nginx bỏ phần `/api/` ở đầu đường dẫn: `/api/notes` trở thành `/notes`, là endpoint mà API xử lý.

5. **API đọc dữ liệu từ RDS và trả kết quả.** API kết nối đến RDS PostgreSQL trên cổng `5432`, sử dụng TLS để mã hóa kết nối database. Sau khi đọc các ghi chú, API trả dữ liệu JSON về qua frontend và ALB. Trình duyệt nhận JSON rồi hiển thị danh sách trên giao diện.

Với thao tác lấy danh sách ghi chú, đường đi là **trình duyệt → ALB → frontend → API → RDS**. Frontend chuyển tiếp lời gọi đến API; API là thành phần truy vấn database.

> **Phạm vi mã hóa và bảo vệ kết nối:** Lab sử dụng HTTPS để mã hóa lưu lượng từ Internet đến ALB. Từ ALB đến frontend pod và từ frontend đến API, ứng dụng sử dụng HTTP qua địa chỉ IP nội bộ trong VPC. Security Groups giới hạn kết nối ở lớp hạ tầng; Kubernetes NetworkPolicy được bổ sung trong chương 3 để giới hạn kết nối theo workload. Đây là lựa chọn của lab để tập trung thực hành bảo mật mạng và workload trên EKS.

Bài này quan sát lab đã chạy, sử dụng tài nguyên được tạo ở phần chuẩn bị. Hoàn thành [bước 0.8 — Kiểm tra baseline](/preparation/8-baseline/) trước khi chạy các lệnh bên dưới.

## Bước 1: đối chiếu đường đi trên AWS Console

Các bước sau chỉ đọc cấu hình, không tự tạo hoặc đăng ký thêm target. Mục đích là nối domain, listener, target group và pod thành một đường truy cập có thể kiểm tra.

1. Mở **Route 53 → Hosted zones → public zone của lab**, chọn record `notes`. Đọc phần value/alias target và đối chiếu với DNS name của ALB `eks-did-notes`.
2. Mở **EC2 → Load Balancers → eks-did-notes → Listeners and rules**. Listener HTTP:80 cần redirect đến HTTPS:443; listener HTTPS:443 cần forward đến target group frontend. Ghi lại target group đang được dùng.
3. Mở target group đó → tab **Targets**. Xem Target type **IP**, protocol/port **HTTP:8080** và các targets **Healthy**. Đây là danh sách do controller đăng ký, không yêu cầu bạn thêm IP bằng tay.
4. Mở **EKS → cluster → Resources → Workloads → Pods**, lọc namespace `notes`, chọn frontend pod và đọc **Pod IP**. So IP này với các targets Healthy. Resource browser yêu cầu danh tính có quyền đọc Kubernetes; có thể dùng `kubectl get pods` ở phần dưới để lấy cùng thông tin.

Ví dụ, pod IP `10.20.44.78` xuất hiện trong target group với port `8080` giúp xác nhận ALB sử dụng frontend pod đó làm backend. IP thật thay đổi theo lượt triển khai.

![Đối chiếu ALB IP targets với frontend pods](/images/console-targets.png "① Target type IP. ② Backend HTTP:8080. ③ Hai targets healthy. ④ Địa chỉ IP và port của pods.")

Ảnh được chụp trong một lượt rollout nên có một target cũ ở trạng thái Draining. Khi đối chiếu với pod hiện tại, tập trung vào các targets Healthy.

## Kiểm tra request thực sự đến ứng dụng

### Gửi request và đọc kết quả

Nạp hostname và kubeconfig của lab:

```bash
source scripts/env.sh
printf 'Hostname: %s\n' "$APP_HOST"
```

`source` thường không in gì. Dòng `printf` phải in hostname đã được tạo ở bước chuẩn bị; nếu trống, hoàn thành [thu thập cấu hình ở bước 0.7](/preparation/7-deploy-application/) trước khi gửi request.

Kiểm tra frontend:

```bash
curl -sS -o /dev/null -w '%{http_code}\n' "https://$APP_HOST/"
```

Kết quả cần thấy:

```text
200
```

`-o /dev/null` bỏ HTML, `-w` chỉ in HTTP status. Trang chủ trả 200 xác nhận frontend phản hồi qua domain HTTPS.

Tiếp tục gọi API thông qua frontend:

```bash
curl -fsS "https://$APP_HOST/api/healthz"
printf '\n'
```

Kết quả:

```json
{"status": "ok", "workload": "api"}
```

Phản hồi này đến từ API sau khi request qua ALB và Nginx frontend. Health endpoint chưa chứng minh thao tác database hoạt động.

Đọc pod IPs để so với AWS target group:

```bash
kubectl get pods -n notes -l app=frontend -o wide
```

Ví dụ, tên và IP trong môi trường của bạn sẽ khác:

```text
NAME                        READY   STATUS    RESTARTS   AGE   IP
frontend-7c8d9f6b5d-abc12    1/1     Running   0          10m   10.20.44.78
frontend-7c8d9f6b5d-def34    1/1     Running   0          10m   10.20.54.165
```

Cột IP là địa chỉ dùng để đối chiếu targets; READY 1/1 cho biết container trong pod đã sẵn sàng. Đọc access log:

```bash
kubectl logs -n notes -l app=frontend --tail=10 --prefix=true
```

Log có thể chứa dòng tương tự:

```text
[pod/frontend-…/frontend] … "GET /api/healthz HTTP/1.1" 200 …
```

Tên pod/container trong prefix cho biết backend nhận request. ALB health checks cũng xuất hiện trong log, và mười dòng cuối có thể không còn chứa request vừa gửi.

### Kiểm tra đường API đến database

```bash
curl -fsS "https://$APP_HOST/api/notes" \
  -H 'Content-Type: application/json' -d '{"body":"Hello from the request path"}'
curl -fsS "https://$APP_HOST/api/notes"
```

POST phải trả ID, GET phải có ghi chú. Không ghi chú thật hoặc dữ liệu nhạy cảm vì app chưa có user authentication.

### Đọc đúng địa chỉ nguồn của request

`X-Forwarded-For` mang IP client trong HTTP header; đây không nhất thiết là source IP mà NetworkPolicy thấy trên kết nối ALB → pod. Không dùng header để viết rule L3/L4. Các bài 2.2–2.6 sẽ giải thích mạng và target registration đằng sau đường đi này. Cấu hình có trong [render.py](/source/scripts/render.py).

Kết quả cần đối chiếu gồm target IP trùng frontend pod IP, HTTP status 200 ở trang chủ/API health và ghi chú vừa POST xuất hiện trong GET. Ba bằng chứng này lần lượt xác nhận backend registration, đường HTTP và thao tác database.
