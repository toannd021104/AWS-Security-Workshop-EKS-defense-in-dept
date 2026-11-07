---
title: "Container Hardening với SecurityContext"
weight: 5
chapter: false
pre: "<b>3.5.</b> "
---

## Giảm đặc quyền mà vẫn giữ app hoạt động

Nếu ứng dụng bị thực thi code ngoài ý muốn, container không nên tự có quyền root hoặc ghi tùy ý vào root filesystem. Lab dùng cấu hình:

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

`runAsNonRoot` yêu cầu UID không phải root. `allowPrivilegeEscalation: false` hạn chế tăng quyền qua cơ chế như setuid; không phải sandbox tuyệt đối. `RuntimeDefault` áp dụng seccomp runtime. Bỏ capabilities giảm quyền Linux không cần thiết.

### Console và CLI: kiểm tra runtime thực tế

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

### Ứng dụng cần ghi file ở đâu?

Nginx cần PID/temp directories. Lab dùng image unprivileged, listen 8080 và mount `emptyDir` có giới hạn tại `/tmp`; cấu hình đưa PID/cache paths đến đó. Không mở writable toàn root filesystem chỉ để hết lỗi.

Python tắt bytecode writes và đọc CA bundle đã có trong image. Resource requests/limits giới hạn ngân sách CPU/RAM, nhưng không phải cơ chế chống mọi kiểu DoS.

Nguồn: [Dockerfile](/source/app/Dockerfile), [render.py](/source/scripts/render.py). Non-root/Restricted không thay thế cập nhật dependencies hoặc application authorization.
