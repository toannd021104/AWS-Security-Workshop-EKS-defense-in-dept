---
title: "Pod Security Standards & Pod Security Admission"
weight: 4
chapter: false
pre: "<b>3.4.</b> "
---

## Vấn đề

Một manifest có thể yêu cầu chạy container bằng root hoặc cấp quyền Linux không cần thiết. Bài này đặt chuẩn Restricted cho namespace ứng dụng để từ chối cấu hình không phù hợp ngay khi tạo pod.

## Kiến thức cần dùng

Pod Security Standards có ba mức Privileged, Baseline và Restricted. Pod Security Admission (PSA) thực thi theo namespace labels. Nó không scan lỗ hổng trong image hoặc kiểm tra HTTP request.

## Thực hiện

### Quan sát cấu hình hiện tại

EKS → Resources → Namespaces → `notes`: quan sát labels. AWS Console có thể không hỗ trợ chỉnh tất cả labels; dùng Kubernetes API cho thay đổi sau.

### Áp dụng Restricted cho namespace

```bash
kubectl label namespace notes \
  pod-security.kubernetes.io/enforce=restricted \
  pod-security.kubernetes.io/enforce-version=v1.35 \
  pod-security.kubernetes.io/audit=restricted \
  pod-security.kubernetes.io/warn=restricted --overwrite
```

Pin version giúp việc upgrade chuẩn Restricted được review thay vì đổi ngầm. Không áp dụng Restricted lên `kube-system` tùy tiện: CNI và một số add-on cần quyền hệ thống.

## Kiểm chứng kết quả

### Thử manifest không đáp ứng Restricted

```bash
kubectl run psa-negative -n notes --image=nginx:1.28-alpine \
  --dry-run=server -o yaml
```

Pod mặc định thiếu cấu hình Restricted nên admission phải từ chối, giải thích `runAsNonRoot`, seccomp/capabilities. `--dry-run=server` chạy admission nhưng không lưu pod. Test không bypass admission hoặc chạy host mount.

### Kiểm tra workload hợp lệ

```bash
kubectl get pods -n notes
kubectl get deployment api -n notes -o jsonpath='{.spec.template.spec.securityContext}'
```

Workloads hợp lệ vẫn Running/Ready sau rollout. Label PSA không đuổi mọi pod đang chạy; cần review/redeploy workload để chứng minh pod template đáp ứng chuẩn.

Trong manifest lab, `securityContext` do `render.py` tạo, tách pod-level và container-level settings. Bài tiếp theo giải thích ý nghĩa của từng trường thay vì chỉ copy YAML.
