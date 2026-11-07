---
title: "Tại sao Amazon EKS cần Defense in Depth?"
weight: 2
chapter: false
pre: "<b>1.2.</b> "
---

## Managed control plane không tự bảo vệ ứng dụng

EKS giảm công việc vận hành Kubernetes control plane. Bạn vẫn quyết định ai vào cluster, pod nào được kết nối, container chạy quyền gì và role AWS nào gắn vào workload.

Với ứng dụng mẫu, xem bốn trường hợp:

1. **API có lỗ hổng:** NetworkPolicy giới hạn kết nối nhưng không hiểu logic nghiệp vụ hoặc sửa lỗi code.
2. **Developer được `pods/exec`:** người đó có thể thực thi code trong container và sử dụng quyền hợp pháp của workload.
3. **Frontend không có Pod Identity:** nếu vẫn lấy được node credentials qua IMDS, việc bỏ role riêng chưa đủ.
4. **Image đã ký nhưng có lỗ hổng:** signature chứng minh nguồn ký/tính toàn vẹn, không chứng minh code an toàn.

### Quan sát cấu hình

**Console:** EKS → cluster → Access xem danh tính được cấp quyền. EC2 → Instances → node → Security kiểm tra IAM role; không nên thấy quyền SQS của ứng dụng trên node.

```bash
aws eks list-access-entries --cluster-name eks-did
kubectl get deployments -n notes
kubectl get rolebindings -n notes
```

Kết quả cần đọc: ba Deployment khác chức năng, identity riêng; không phải ba replica của một app.

### Thiết kế để giới hạn tác động

Frontend không cần AWS role và không có đường egress đến RDS. API chỉ gửi vào một queue. Worker chỉ nhận/xóa từ queue đó. PostgreSQL cấp SQL privileges riêng cho API và worker. Những giới hạn này vẫn có ý nghĩa khi một workload bị lỗi.

Không thực hiện exploit trong bài này. Ta dùng probe có kiểm soát để kiểm tra các ranh giới. Phần ứng dụng chưa có đăng nhập người dùng và không được dùng lưu dữ liệu nhạy cảm; network/IAM không thay thế application authorization.
