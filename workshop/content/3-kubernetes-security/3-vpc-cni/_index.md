---
title: "NetworkPolicy Enforcement với Amazon VPC CNI"
weight: 3
chapter: false
pre: "<b>3.3.</b> "
---

## YAML không tự chặn packet

NetworkPolicy API object cần engine thực thi. Lab dùng Amazon VPC CNI trên Linux EC2 managed nodes và bật network policy agent; không mặc định mọi compute platform đều hỗ trợ giống nhau.

### Console: bật khả năng thực thi

1. EKS → cluster → Add-ons → Amazon VPC CNI → Edit.
2. Chọn version tương thích EKS/kernel/instance theo tài liệu AWS.
3. Optional configuration → configuration values, bật `enableNetworkPolicy`:

```json
{"enableNetworkPolicy":"true"}
```

4. Save, đợi add-on `ACTIVE`. Nếu tự quản lý add-on, không chạy thêm một managed copy chồng lên DaemonSet hiện có.

### CLI/API: kiểm tra cấu hình và agent

```bash
aws eks describe-addon --cluster-name eks-did --addon-name vpc-cni \
  --query 'addon.{version:addonVersion,status:status,configuration:configurationValues}'
kubectl get daemonset aws-node -n kube-system
kubectl get pods -n kube-system -l k8s-app=aws-node \
  -o jsonpath='{range .items[*]}{.metadata.name}{"  "}{.spec.containers[*].name}{"\n"}{end}'
```

Phải thấy container `aws-eks-nodeagent` (network policy agent) bên cạnh `aws-node`. Tên container có thể khác theo release; đối chiếu image và add-on version. Hai nodes phải được DaemonSet bao phủ. Nếu chưa bật, API tương ứng:

```bash
aws eks update-addon --cluster-name eks-did --addon-name vpc-cni \
  --configuration-values '{"enableNetworkPolicy":"true"}' --resolve-conflicts PRESERVE
```

`configuration-values` cần giữ các custom settings hiện có; đọc cấu hình trước khi update. Terraform dùng `aws_eks_addon.vpc_cni` trong [main.tf](/source/terraform/main.tf).

### Standard và strict mode

Lab bắt đầu với standard mode: pod mới có thể có khoảng thời gian trước khi policy hoàn tất. Strict mode default-deny ngay lúc startup, nhưng cần DNS, credentials và các dependency đã được cho phép. Đây là mode của policy enforcement, khác mode của Security Groups for Pods.

Không kết luận chỉ từ trạng thái add-on. Phải chạy cùng một connectivity test trước/sau policy. Ghi rõ startup window là giới hạn; bài này không khẳng định zero-window isolation.

Tham khảo [EKS NetworkPolicy](https://docs.aws.amazon.com/eks/latest/userguide/cni-network-policy.html) để đối chiếu các giới hạn hiện hành trước khi đổi compute/CNI.
