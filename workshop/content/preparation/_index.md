---
title: "Chuẩn bị và cách dùng workshop"
weight: 1
chapter: false
pre: ""
---

## Môi trường thực hành

Đọc chương 1 để nắm kiến trúc trước khi tạo tài nguyên. Các bài thực hành được tổ chức theo bốn phần: vấn đề, kiến thức cần dùng, thực hiện và kiểm chứng kết quả. Ảnh khoanh đỏ đánh dấu trường hoặc kết quả cần đối chiếu trên Console.

Các bước dưới đây chuẩn bị ứng dụng nền. `deploy.sh` chưa áp dụng NetworkPolicy; phép thử trước/sau isolation được thực hiện ở bài 3.2. Một số quyền và cấu hình cần thiết để chạy ứng dụng được tạo trong phần chuẩn bị và sẽ được phân tích, kiểm tra chi tiết ở các chương sau.

[Tải mã lab](/downloads/eks-defense-in-depth-lab.zip), giải nén và mở terminal tại thư mục chứa `app/`, `scripts/`, `infrastructure/`. ZIP không chứa credentials hoặc Terraform state.

Ứng dụng ghi chú gồm Nginx frontend, Python API và Python worker. Frontend proxy `/api/` đến API; API lưu ghi chú trên RDS PostgreSQL và gửi yêu cầu báo cáo đến SQS. Worker chủ động đọc queue và ghi kết quả vào RDS. Worker không có public endpoint.

### 1. Kiểm tra account và công cụ

**Console:** đăng nhập sandbox, kiểm tra account ở góc phải, chọn **US East (N. Virginia), us-east-1**. Mở EKS, VPC, RDS, ECR, SQS, IAM và Route 53 để xác nhận quyền xem. Có quyền xem chưa chứng minh có quyền tạo.

**CLI/API:** chạy từ thư mục dự án mới:

```bash
export AWS_PROFILE=guru AWS_REGION=us-east-1
aws sts get-caller-identity
aws eks list-clusters
aws route53 list-hosted-zones --query 'HostedZones[].Name'
aws --version
kubectl version --client
helm version --short
docker version
terraform version
python3 -m pip install boto3 PyYAML
source scripts/env.sh
```

Bạn cần AWS CLI v2, kubectl tương thích minor EKS, Helm 3, Docker, Python 3 và Hugo Extended. Terraform chỉ bắt buộc khi chọn đường IaC. Không đưa access key vào manifest hay website.

### 2. Chọn một đường triển khai

- **Console:** làm theo 2.2, 2.4 và hướng dẫn dựng cluster bên dưới; sau đó tạo RDS/SQS/ECR trong phần nền ứng dụng. Dùng `capture-config.py` để thu thập cấu hình, không cần Terraform state.
- **CLI/API:** các bài đưa lệnh cho thao tác khó biểu diễn trên Console và đọc kết quả chính xác. Không chạy lệnh tạo nếu tài nguyên đã được tạo qua Console.
- **Terraform:** mã đầy đủ ở `infrastructure/terraform/`, giúp dựng cùng lab để học các bài kiểm soát. Script này không bật GuardDuty.

```bash
cp infrastructure/terraform/terraform.tfvars.example infrastructure/terraform/terraform.tfvars
# Sửa admin_cidr thành IP public /32 hiện tại và dns_zone_name thành hosted zone bạn quản lý.
terraform -chdir=infrastructure/terraform init
terraform -chdir=infrastructure/terraform fmt -check
terraform -chdir=infrastructure/terraform validate
terraform -chdir=infrastructure/terraform plan -out=lab.tfplan
# Đọc account/Region, chỉ chấp nhận tài nguyên lab mới và không có xóa ngoài dự kiến.
terraform -chdir=infrastructure/terraform apply lab.tfplan
```

State chứa metadata nhạy cảm. Không upload `.terraform`, `terraform.tfvars`, state, plan hoặc `.local` lên GitHub/Hugo. Với nhóm nhiều người, dùng remote backend và locking trước khi cộng tác.

### 3. Dựng EKS qua Console nếu không dùng Terraform

1. IAM → Roles → Create role → AWS service → **EKS – Cluster**. Đặt `eks-did-cluster-role`, gắn `AmazonEKSClusterPolicy`.

2. Tạo role EC2 `eks-did-node-role`, gắn `AmazonEKSWorkerNodePolicy` và `AmazonEC2ContainerRegistryPullOnly`. Không gắn quyền ứng dụng lên node role. VPC CNI dùng role IRSA riêng theo bước 5.

3. EKS → Add cluster → Create → tên `eks-did`, version `1.35`, chọn role cluster. **Không chọn Auto Mode**: lab dùng managed node group để quan sát CNI và IMDS.

4. Networking → VPC lab, hai private application subnets. Endpoint **Public and private**, Public access CIDRs = IP workstation `/32`. Authentication mode chọn **EKS API**, giữ quyền bootstrap cho người tạo đến khi đã kiểm chứng danh tính quản trị khác.

5. Chọn add-ons VPC CNI, CoreDNS, kube-proxy, Pod Identity Agent. Bật NetworkPolicy trong VPC CNI theo 3.3. Chọn bản add-on tương thích version cluster. Sau khi cluster Active, copy OIDC issuer trong EKS Overview → IAM → Identity providers → Add OpenID Connect provider, audience `sts.amazonaws.com`. Tạo web-identity role `eks-did-vpc-cni-role` cho provider này, gắn `AmazonEKS_CNI_Policy`; trust phải giới hạn `sub=system:serviceaccount:kube-system:aws-node` và `aud=sts.amazonaws.com`. Chọn role này ở VPC CNI add-on IAM role. [Terraform trust tương đương](/source/terraform/main.tf) có đủ điều kiện; không để trust cho mọi ServiceAccount.

6. Tạo EC2 Launch Template cho node: không SSH key, IMDS **token required**, response hop limit **1**, EBS 20 GiB gp3 mã hóa. Dùng template này khi tạo managed node group `private-workers`, hai private subnets, `t3.medium`, min/desired/max đều 2 cho lab. Không chỉ định AMI tùy ý; để EKS chọn AL2023 phù hợp.

7. Compute → Node group phải `ACTIVE`, hai node `Ready`. Nếu node không join, kiểm tra NAT route, CNI role và IAM policies trước khi đổi endpoint CIDR.

```bash
aws eks update-kubeconfig --name eks-did --alias eks-did --kubeconfig "$KUBECONFIG"
kubectl get nodes -o wide
```

Kubeconfig của lab nằm trong `.local/`, không thay context mặc định của các cluster khác.

### 4. Nền ứng dụng: RDS, SQS và ECR

**RDS Console:** Create database → Standard create → PostgreSQL 17 (lab pin `17.11`), identifier `eks-did`, database `notes`, master username `labadmin`, **Manage master credentials in Secrets Manager**. Chọn `db.t3.micro`, storage gp3 20 GiB mã hóa, Single-AZ cho lab. DB subnet group chứa hai database subnets, Public access **No**. SG database chỉ nhận TCP 5432 từ cluster/node SG. Bật **Password and IAM database authentication**, backup một ngày. Single-AZ và xóa không snapshot chỉ là đánh đổi của sandbox.

**SQS Console:** tạo Standard queue `eks-did-reports`, visibility 60 giây, retention 1 ngày, bật SSE-SQS. API chỉ gửi; worker nhận/xóa. Bài 4.6 cấu hình IAM trước khi chạy app.

**ECR Console:** tạo private repository `eks-did/notes`, immutable tags, AES-256 encryption, basic scan on push. Module 5 bổ sung enhanced scanning nếu được phép.

**ACM/Route 53:** làm 2.3 để có cert `ISSUED` trước khi dựng Ingress. Không có domain hợp lệ thì chưa hoàn thành bài HTTPS.

### 5. Cấp identity và triển khai

Terraform đã tạo các role/association của 4.5–4.6. Người chọn Console làm hai bài đó trước khi deploy. `db-init` chỉ đọc master secret để tạo SQL roles; API/worker dùng IAM database authentication, không dùng tài khoản master.

```bash
python3 scripts/capture-config.py
source scripts/env.sh
bash scripts/build-push.sh
bash scripts/deploy.sh
python3 scripts/publish-dns.py
```

Tên subnet phải chứa `-public-`, `-private-`, `-database-` để script xác định đúng vai trò. Nếu account có nhiều hosted zone, export `DNS_ZONE_NAME=example.com.` trước khi capture. Mã nguồn [render manifests](/source/scripts/render.py) và [ứng dụng](/source/app/main.py) có thể đọc trực tiếp.

### Chi phí và giới hạn

EKS control plane, hai EC2 nodes, NAT, public IPv4, ALB, RDS, WAF, KMS và Inspector có thể tính phí; giá phụ thuộc Region và thời gian chạy. Đây không phải lab miễn phí. Các quyền IAM/CreateRole/PassRole, EKS, EC2, ELB, RDS, SQS, ECR, ACM, Route 53 là điều kiện chính. WAF/Inspector/CMK có thể bị SCP chặn; ghi đúng dịch vụ/action bị từ chối, không tìm cách vượt SCP.

Sau khi môi trường nền hoạt động, bắt đầu chương 2 để theo dõi request và kiểm tra cấu hình mạng. [Cleanup](/cleanup/) là bước bắt buộc khi ngừng sử dụng lab.
