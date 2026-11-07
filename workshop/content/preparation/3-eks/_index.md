---
title: "Tạo EKS, CNI role và managed worker nodes"
weight: 30
chapter: false
pre: "<b>0.3.</b> "
---

## Mục tiêu chuẩn bị

Tạo EKS managed control plane và hai EC2 managed worker nodes trong private application subnets. VPC CNI sử dụng IAM role riêng để node có thể yêu cầu IMDSv2 với hop limit 1 mà vẫn khởi tạo mạng pod.

## Tạo IAM roles cho cluster và node

Trong **IAM → Roles → Create role**:

| Role | Trusted entity | Permissions |
|---|---|---|
| `eks-did-cluster-role` | AWS service → EKS → EKS Cluster | `AmazonEKSClusterPolicy` |
| `eks-did-node-role` | AWS service → EC2 | `AmazonEKSWorkerNodePolicy`, `AmazonEC2ContainerRegistryPullOnly` |

Cluster role được EKS control plane sử dụng; node role được các EC2 worker nodes sử dụng. Quyền SQS và database của ứng dụng được cấp cho workload roles ở bước sau.

## Tạo EKS cluster

1. Mở **EKS → Clusters → Add cluster → Create**, tên `eks-did`, Kubernetes version **1.35**, chọn cluster role vừa tạo.
2. Chọn cấu hình tùy chỉnh với **managed node groups**, tắt **EKS Auto Mode** cho kiến trúc lab.
3. Phần networking: VPC `eks-did`, chọn **hai private application subnets**. Giữ cluster Security Group do EKS quản lý.
4. Chọn endpoint **Public and private**. Lấy IP public của máy quản trị:

```bash
curl -fsS https://checkip.amazonaws.com
```

Nhập IP đó với suffix `/32` vào public access CIDRs. Ví dụ `203.0.113.10/32` chỉ là địa chỉ minh họa, phải thay bằng kết quả thực tế.

5. Authentication mode chọn **EKS API**, giữ quyền cluster admin bootstrap cho principal đang tạo cluster. Các bước sau dùng danh tính này để triển khai Kubernetes resources.
6. Giữ CoreDNS, kube-proxy và VPC CNI managed add-ons tương thích với cluster. Tạo cluster và chờ **Active**; chưa tạo node group ở bước này.

Nếu principal trong terminal khác principal tạo cluster trên Console, cần cấp đường quản trị cho CLI trước khi dùng kubectl: EKS → **Access → Create access entry**, chọn IAM principal của CLI, type **Standard**, associate **AmazonEKSClusterAdminPolicy** với scope **Cluster** cho người quản trị lab. Với credentials assume-role/SSO, dùng IAM role ARN từ IAM Console, không dùng STS session ARN `assumed-role/…`. Đây là quyền bootstrap admin để dựng lab; role observer ở chương 4 sẽ được cấp quyền đọc riêng.


![Thông tin cluster đã tạo](/images/console-eks.png "Cluster Active và Kubernetes version của môi trường lab.")

Trong giao diện EKS mới, networking nằm ở **Configuration → Networking**. Đối chiếu endpoint access và allowlist:

![Cấu hình endpoint của EKS](/images/console-eks-endpoint.png "① Public and private endpoint. ② Public access CIDR giới hạn theo workstation.")

## Tạo OIDC provider và IRSA role cho VPC CNI

1. EKS → cluster → xem **OpenID Connect provider URL**, copy issuer URL.
2. IAM → **Identity providers → Add provider → OpenID Connect**, nhập issuer URL; audience `sts.amazonaws.com`. Tạo provider.
3. IAM → Roles → Create role → **Web identity**, chọn provider trên và audience `sts.amazonaws.com`; gắn `AmazonEKS_CNI_Policy`, tên `eks-did-vpc-cni-role`.
4. Mở role → **Trust relationships → Edit trust policy**, giới hạn đúng ServiceAccount của CNI. Thay `ACCOUNT_ID` và `OIDC_HOSTPATH` trong JSON bằng account và issuer của bạn; `OIDC_HOSTPATH` là issuer **bỏ phần `https://`**:

```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": {"Federated": "arn:aws:iam::ACCOUNT_ID:oidc-provider/OIDC_HOSTPATH"},
    "Action": "sts:AssumeRoleWithWebIdentity",
    "Condition": {"StringEquals": {
      "OIDC_HOSTPATH:aud": "sts.amazonaws.com",
      "OIDC_HOSTPATH:sub": "system:serviceaccount:kube-system:aws-node"
    }}
  }]
}
```

Có thể đọc các giá trị để đối chiếu bằng CLI:

```bash
aws sts get-caller-identity --query Account --output text
aws eks describe-cluster --name eks-did --query 'cluster.identity.oidc.issuer' --output text
```

5. EKS → **Add-ons → Amazon VPC CNI → Edit**. Chọn role `eks-did-vpc-cni-role` ở mục IAM role for service account (IRSA). Trong optional configuration, thêm:

```json
{"enableNetworkPolicy":"true"}
```

Giữ các cấu hình tùy chỉnh khác nếu có. Lưu và đối chiếu đúng role/configuration. Trạng thái các add-ons và pods được kiểm tra sau khi có worker nodes; CoreDNS có thể Pending khi cluster chưa có compute. Chưa áp dụng NetworkPolicy cho ứng dụng ở bước này.

6. Trong Add-ons, chọn **Get more add-ons → Amazon EKS Pod Identity Agent**, tạo managed add-on tương thích với cluster. Chờ agent có node để chạy ở bước tiếp theo.

![Các add-ons của lab](/images/console-eks-addons.png "① Pod Identity Agent. ② VPC CNI. ③ IRSA role của CNI.")

## Tạo launch template và managed node group

1. EC2 → **Launch templates → Create launch template**, tên `eks-did-nodes`. Giữ AMI, instance type, subnet, IAM instance profile và Security Groups không được chỉ định trong template; EKS/node group sẽ cung cấp các giá trị đó. Không chọn key pair.
2. Storage: root device `/dev/xvda`, EBS **20 GiB gp3**, encryption Enabled, Delete on termination Enabled.
3. Advanced details → Metadata options: metadata endpoint Enabled, **IMDSv2 required**, response hop limit **1**. Tạo template và ghi lại version.
4. EKS → cluster → **Compute → Add node group**, tên `private-workers`, node IAM role `eks-did-node-role`. Bật sử dụng launch template vừa tạo, đúng version.
5. Chọn AL2023 x86_64 phù hợp EKS, instance type `t3.medium`, On-Demand; desired/min/max đều **2** cho lab. Nếu giao diện khóa AMI/instance type, kiểm tra template có đang ghi đè các trường này không.
6. Chọn **hai private application subnets**, tắt remote SSH access. Tạo node group và chờ **Active**.

## Kết nối kubectl và kiểm tra

```bash
source scripts/env.sh
aws eks update-kubeconfig --name eks-did --alias eks-did --kubeconfig "$KUBECONFIG"
kubectl get nodes -o wide
kubectl get pods -n kube-system
```

Kết quả minh họa, tên và IP sẽ khác:

```text
NAME                         STATUS   ROLES    AGE   VERSION
ip-10-20-35-10.ec2.internal   Ready    <none>   5m    v1.35.x
ip-10-20-51-20.ec2.internal   Ready    <none>   5m    v1.35.x
```

Cần có hai nodes `Ready`, không có external public IP; aws-node, CoreDNS, kube-proxy và Pod Identity Agent hoạt động. Nếu node chưa join, đối chiếu NAT route, CNI IRSA role và node IAM policies. Nếu kubectl không kết nối được, kiểm tra workstation IP còn nằm trong endpoint allowlist.

Tiếp tục [tạo RDS, SQS và ECR](/preparation/4-data-services/).
