---
title: "Worker Node Security và IMDSv2"
weight: 6
chapter: false
pre: "<b>3.6.</b> "
---

## Vấn đề

Worker node có IAM role để vận hành EKS. Nếu application pod lấy được credentials của node qua IMDS, nó có thể sử dụng quyền ngoài role được cấp riêng. Bài này cấu hình metadata options và kiểm tra truy cập IMDS từ pod thông thường.

## Kiến thức cần dùng

EC2 Instance Metadata Service (IMDS) cung cấp thông tin instance và credentials tạm thời của instance role qua địa chỉ `169.254.169.254`. IMDSv2 yêu cầu lấy session token trước khi truy cập metadata. Cấu hình response hop limit giới hạn số network hops của phản hồi lấy token.

Node role cần pull image và thực hiện chức năng EKS. Quyền SQS/RDS của ứng dụng không nên gắn lên role này. Nếu pod lấy được node credentials qua EC2 IMDS, việc cấp role riêng theo workload có thể bị suy yếu.

## Thực hiện

### Cấu hình metadata options trong launch template

1. EC2 → Launch templates → template node lab → Advanced details → Metadata options.

2. Metadata accessible: enabled; **IMDSv2 required**, response hop limit **1**.

3. Không mở SSH từ Internet, EBS encrypted. CNI role riêng cho `aws-node`, không bắt CNI pod phụ thuộc metadata hop 1.

4. EKS node group dùng đúng template version. Sửa launch template không tự cập nhật mọi node cũ; rollout node group có kiểm soát.

## Kiểm chứng kết quả

### Đọc cấu hình của EC2 instances đang chạy

```bash
aws ec2 describe-instances \
  --filters Name=tag:eks:cluster-name,Values=eks-did Name=instance-state-name,Values=running \
  --query 'Reservations[].Instances[].{id:InstanceId,publicIP:PublicIpAddress,metadata:MetadataOptions,profile:IamInstanceProfile.Arn}'
```

Mong đợi nodes không có public IP, `HttpTokens=required`, `HttpPutResponseHopLimit=1`. Terraform dùng `aws_launch_template.nodes`.

### Thử truy cập IMDS từ application pod

```bash
kubectl exec -n notes deployment/api -- python -c '
import urllib.request
r=urllib.request.Request("http://169.254.169.254/latest/api/token",method="PUT",headers={"X-aws-ec2-metadata-token-ttl-seconds":"60"})
try:
    urllib.request.urlopen(r,timeout=3)
    raise SystemExit("UNEXPECTED: pod reached IMDS; investigate")
except (TimeoutError, OSError):
    print("Expected: ordinary application pod cannot obtain IMDS token")'
```

Sau default-deny, NetworkPolicy cũng có thể chặn đường này. Kiểm tra metadata instance và chạy probe **trước policy** nếu muốn phân biệt tác động hop limit với policy. Không gán mọi timeout sau hardening riêng cho IMDSv2.

IMDSv2 required một mình không chặn pod yêu cầu token; hop limit và network restrictions mới là phần bổ sung. `hostNetwork` có đặc điểm khác và bị baseline ứng dụng loại trừ. Xem module 4 để pod vẫn có temporary credentials đúng role qua Pod Identity Agent.
