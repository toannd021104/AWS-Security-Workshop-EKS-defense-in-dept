---
title: "NetworkPolicy Enforcement với Amazon VPC CNI"
weight: 3
chapter: false
pre: "<b>3.3.</b> "
---

Kubernetes có thể chấp nhận một NetworkPolicy dù chưa có thành phần thực thi rule. Bài này bật tính năng NetworkPolicy của Amazon VPC CNI và xác nhận agent hoạt động trên worker nodes trước khi kiểm tra kết nối.

## Thành phần nào thực thi NetworkPolicy?

NetworkPolicy lưu các rule qua Kubernetes API. Amazon VPC CNI sử dụng network policy agent trên từng Linux worker node để thực thi bằng eBPF. Lab bật agent trên EC2 managed nodes; cần kiểm tra điều kiện hỗ trợ trước khi chọn compute platform khác.

## Bước 1: bật NetworkPolicy trên VPC CNI

1. EKS → cluster → Add-ons → Amazon VPC CNI → Edit.

2. Chọn version tương thích EKS/kernel/instance theo tài liệu AWS.

3. Optional configuration → configuration values, bật `enableNetworkPolicy`:

```json
{"enableNetworkPolicy":"true"}
```

4. Save, đợi add-on `ACTIVE`. Nếu tự quản lý add-on, không chạy thêm một managed copy chồng lên DaemonSet hiện có.

![VPC CNI và Pod Identity Agent trong EKS](/images/console-eks-addons.png "① Pod Identity Agent. ② Amazon VPC CNI. ③ IAM role riêng của VPC CNI.")

Ảnh xác nhận add-ons và role CNI được cài đặt. Cấu hình `enableNetworkPolicy` và container policy agent tiếp tục được xác minh bằng các lệnh bên dưới.

### Cấu hình tương đương qua EKS API (tùy chọn)

Nếu chưa bật, API tương ứng:

```bash
aws eks update-addon --cluster-name eks-did --addon-name vpc-cni \
  --configuration-values '{"enableNetworkPolicy":"true"}' --resolve-conflicts PRESERVE
```

`configuration-values` cần giữ các custom settings hiện có; đọc cấu hình trước khi update. Terraform dùng `aws_eks_addon.vpc_cni` trong [main.tf](/source/terraform/main.tf).

## Kiểm tra agent trên từng worker node

### Xác nhận cấu hình và policy agent

```bash
aws eks describe-addon --cluster-name eks-did --addon-name vpc-cni \
  --query 'addon.{version:addonVersion,status:status,configuration:configurationValues}'
kubectl get daemonset aws-node -n kube-system
kubectl get pods -n kube-system -l k8s-app=aws-node \
  -o jsonpath='{range .items[*]}{.metadata.name}{"  "}{.spec.containers[*].name}{"\n"}{end}'
```

Phải thấy container `aws-eks-nodeagent` (network policy agent) bên cạnh `aws-node`. Tên container có thể khác theo release; đối chiếu image và add-on version. Hai nodes phải được DaemonSet bao phủ.

### Standard và strict mode

Lab bắt đầu với standard mode: pod mới có thể có khoảng thời gian trước khi policy hoàn tất. Strict mode default-deny ngay lúc startup, nhưng cần DNS, credentials và các dependency đã được cho phép. Đây là mode của policy enforcement, khác mode của Security Groups for Pods.

Không kết luận chỉ từ trạng thái add-on. Phải chạy cùng một connectivity test trước/sau policy. Ghi rõ startup window là giới hạn; bài này không khẳng định zero-window isolation.

Tham khảo [EKS NetworkPolicy](https://docs.aws.amazon.com/eks/latest/userguide/cni-network-policy.html) để đối chiếu các giới hạn hiện hành trước khi đổi compute/CNI.

Add-on `ACTIVE` và agent trên mỗi node là điều kiện thực thi. Bằng chứng kết nối được kiểm tra ở bài 3.2: frontend gọi API thành công trong khi pod không liên quan bị chặn. Chỉ nhìn thấy NetworkPolicy trong `kubectl get` chưa xác nhận được enforcement.
