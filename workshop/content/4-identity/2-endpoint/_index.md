---
title: "EKS API Endpoint Security"
weight: 2
chapter: false
pre: "<b>4.2.</b> "
---

## Vấn đề

Website cần public, nhưng endpoint quản trị Kubernetes chỉ cần phục vụ các nguồn được phép. Bài này giới hạn public access CIDRs của EKS API và giữ private access cho các thành phần trong VPC.

## Kiến thức cần dùng

![Đường quản trị EKS](/images/human-access.svg)

ALB public phục vụ website. EKS API endpoint phục vụ Kubernetes API. Một người có thể mở website nhưng không kết nối được endpoint quản trị; một người đến được endpoint vẫn phải qua authentication/authorization.

## Thực hiện

### Giới hạn nguồn truy cập EKS API

EKS → cluster → Configuration → Networking → Manage → endpoint access (giao diện cũ: Networking → Manage endpoint access). Lab chọn Public and private, public CIDRs = IP workstation `/32`. Nodes/controller dùng private endpoint trong VPC. Không mở `0.0.0.0/0` để xử lý lỗi từ workstation.

Thiết kế production có VPN/private connectivity có thể dùng private-only. Đánh đổi: người học từ Internet cần một đường quản trị vào VPC, không thể chỉ chạy kubectl từ bất kỳ đâu.

![Endpoint access và public CIDR allowlist](/images/console-eks-endpoint.png "① EKS API endpoint access. ② Public access source allowlist.")

Lab bật public và private access, đồng thời giới hạn public endpoint bằng CIDR quản trị. Dùng IP workstation của bạn thay cho IP trong ảnh.

### Cập nhật IP quản trị khi cần

Nếu IP workstation đổi, cập nhật **đúng IP mới**:

```bash
ADMIN_IP=$(curl -fsS https://checkip.amazonaws.com)
aws eks update-cluster-config --name eks-did \
  --resources-vpc-config "endpointPublicAccess=true,endpointPrivateAccess=true,publicAccessCidrs=$ADMIN_IP/32"
```

Chỉ dùng API nếu đó là đường quản lý bạn chọn. Với Terraform, sửa `admin_cidr`, plan rồi apply để tránh drift. Giữ kết nối quản trị đang hoạt động và đợi update hoàn tất trước khi thử context mới.

## Kiểm chứng kết quả

### Đọc endpoint configuration và cập nhật CIDR

```bash
aws eks describe-cluster --name eks-did \
  --query 'cluster.resourcesVpcConfig.{public:endpointPublicAccess,private:endpointPrivateAccess,cidrs:publicAccessCidrs}'
curl -fsS https://checkip.amazonaws.com
```


`kubectl get nodes` từ workstation được cho phép phải thành công. Đọc public CIDR từ API để xác nhận không có mạng rộng ngoài dự kiến. Workshop không dùng một timeout từ mạng chưa biết để tuyên bố đã kiểm chứng private-only; giới hạn test được ghi trong validation.
