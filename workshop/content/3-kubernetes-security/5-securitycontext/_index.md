---
title: "Container Hardening với SecurityContext"
weight: 5
chapter: false
pre: "<b>3.5.</b> "
---

## Vấn đề

Các workload cần đáp ứng chuẩn Restricted và vẫn phục vụ ứng dụng bình thường. Bài này cấu hình quyền thực thi tối thiểu cho container, xác định nơi được ghi file và kiểm tra các giới hạn ngay trong runtime.

## Kiến thức cần dùng

Nếu ứng dụng bị thực thi code ngoài ý muốn, container không nên tự có quyền root hoặc ghi tùy ý vào root filesystem. Các trường cấu hình dưới đây được áp dụng ở pod hoặc container theo phạm vi tương ứng.

`runAsNonRoot` yêu cầu UID không phải root. `allowPrivilegeEscalation: false` hạn chế tăng quyền qua cơ chế như setuid; không phải sandbox tuyệt đối. `RuntimeDefault` áp dụng seccomp runtime. Bỏ capabilities giảm quyền Linux không cần thiết.

## Thực hiện

### Cấu hình pod và container

Trong `k8s/application.yaml`, đối chiếu `spec.template.spec.securityContext` và `containers[].securityContext` của API với các trường sau:

```yaml
securityContext:
  runAsNonRoot: true
  runAsUser: 10001
  runAsGroup: 10001
  seccompProfile:
    type: RuntimeDefault
containers:
  - name: api
    # image và các trường còn lại xem manifest đầy đủ
    securityContext:
      allowPrivilegeEscalation: false
      readOnlyRootFilesystem: true
      capabilities:
        drop: ["ALL"]
```

Đây là một phần của Pod spec. Manifest đầy đủ do `scripts/render.py` tạo đã bao gồm các trường này cho ứng dụng lab. Khi thay đổi pod template, áp dụng lại và chờ rollout hoàn tất:

```bash
kubectl apply -f k8s/application.yaml
kubectl rollout status deployment/api -n notes
```

### Ứng dụng cần ghi file ở đâu?

Nginx cần PID/temp directories. Lab dùng image unprivileged, listen 8080 và mount `emptyDir` có giới hạn tại `/tmp`; cấu hình đưa PID/cache paths đến đó. Không mở writable toàn root filesystem chỉ để hết lỗi.

Python tắt bytecode writes và đọc CA bundle đã có trong image. Resource requests/limits giới hạn ngân sách CPU/RAM, nhưng không phải cơ chế chống mọi kiểu DoS.

Nguồn: [Dockerfile](/source/app/Dockerfile), [render.py](/source/scripts/render.py). Non-root/Restricted không thay thế cập nhật dependencies hoặc application authorization.

## Kiểm chứng kết quả

### Kiểm tra quyền thực thi trong container

EKS Console → Pod API → xem cấu hình. Sau đó:

```bash
kubectl exec -n notes deployment/api -- id
kubectl exec -n notes deployment/api -- python -c \
  'from pathlib import Path; Path("/app/should-not-write").write_text("test")'
```

Mong đợi UID 10001 và lần ghi bị từ chối (`Read-only file system` hoặc permission error). Sau đó API health vẫn 200:

```bash
curl -fsS "https://$APP_HOST/api/healthz"
```
