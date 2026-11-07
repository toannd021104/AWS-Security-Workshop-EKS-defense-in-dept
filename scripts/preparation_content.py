"""Console-first setup lessons, independent of the later security chapters."""
from pathlib import Path

SETUP = [
('1-workstation','Tài khoản AWS, công cụ và mã nguồn',r'''
## Mục tiêu chuẩn bị

Phần thực hành sử dụng một máy Ubuntu Linux x86_64 có kết nối Internet và một tài khoản AWS. Các thao tác AWS ưu tiên Console; terminal được dùng để build container, thao tác Kubernetes và đọc kết quả chính xác.

Tài nguyên được tạo tại **US East (N. Virginia), us-east-1**, với prefix `eks-did`. Chọn cùng account và Region trong cả Console lẫn terminal. Nếu account đã có một lab cùng tên, kiểm tra tài nguyên hiện có trước khi tạo thêm.

## Đăng nhập và kiểm tra tài khoản

1. Đăng nhập AWS Console vào tài khoản AWS của bạn, kiểm tra account ID ở góc phải và chọn Region **us-east-1**.
2. Chuẩn bị một public domain hoặc public Route 53 hosted zone đã được delegate hợp lệ. Lab dùng subdomain `notes.<domain>` và ACM public certificate. Việc chỉ tạo hosted zone chưa làm domain được phân giải trên Internet.
3. Trong terminal, kiểm tra profile đã được cấp:

```bash
export AWS_PROFILE=guru
export AWS_REGION=us-east-1
aws sts get-caller-identity
```

Ví dụ kết quả, các giá trị account và ARN sẽ khác ở account của bạn:

```json
{
  "UserId": "EXAMPLE",
  "Account": "123456789012",
  "Arn": "arn:aws:iam::123456789012:user/lab-user"
}
```

`guru` là tên profile trên máy, không phải tên tài khoản AWS. Nếu chưa có profile, dùng thông tin xác thực AWS của bạn để cấu hình `aws configure --profile guru`. Credentials tạm thời cần đủ session token trong profile và còn hạn; SSO sử dụng quy trình `aws configure sso`. Nếu sử dụng SSO hoặc thông tin xác thực tạm thời, không cần tạo access key dài hạn.

Account trong kết quả phải trùng account đang mở trên Console. Tiếp tục sau khi lệnh STS thành công.

## Chuẩn bị công cụ

Kiểm tra các công cụ đã có trước khi cài:

```bash
aws --version
kubectl version --client
helm version --short
docker version
python3 --version
git --version
```

| Công cụ | Dùng trong lab |
|---|---|
| AWS CLI v2 | Đọc cấu hình AWS và lấy EKS kubeconfig |
| kubectl tương thích EKS 1.35 | Triển khai và kiểm tra tài nguyên Kubernetes |
| Helm 3 | Cài AWS Load Balancer Controller; sau đó là Kyverno |
| Docker | Build và push image API/worker lên ECR |
| Python 3, boto3, PyYAML | Thu thập cấu hình, render manifests và kiểm chứng |
| Git, curl, unzip, jq | Lấy mã nguồn và kiểm tra kết quả |

Nếu sử dụng máy Ubuntu mới, cài các gói nền:

```bash
sudo apt-get update
sudo apt-get install -y ca-certificates curl unzip jq git python3-venv docker.io
sudo systemctl enable --now docker
sudo usermod -aG docker "$USER"
```

Đăng nhập lại terminal để group Docker có hiệu lực, sau đó kiểm tra `docker version` hiển thị cả **Client** và **Server**. Cài [AWS CLI v2](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html), [kubectl](https://docs.aws.amazon.com/eks/latest/userguide/install-kubectl.html) và [Helm 3](https://helm.sh/docs/intro/install/) theo hướng dẫn chính thức cho Linux. Chọn kubectl cùng minor với cluster 1.35, hoặc trong phạm vi version skew được hỗ trợ.

Terraform được dùng ở nhánh triển khai tùy chọn. Hugo Extended chỉ cần khi biên tập hoặc chạy website workshop trên máy.

## Lấy mã nguồn và thiết lập thư mục làm việc

```bash
git clone https://github.com/toannd021104/eks-defense-in-depth-workshop.git
cd eks-defense-in-depth-workshop
mkdir -p .local
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install boto3 PyYAML
export AWS_PROFILE=guru AWS_REGION=us-east-1
source scripts/env.sh
```

Có thể dùng [gói ZIP mã lab](/downloads/eks-defense-in-depth-lab.zip) thay cho Git; giải nén rồi đứng tại thư mục có `app/`, `scripts/`, `k8s/` và `infrastructure/`.

| Thư mục | Nội dung |
|---|---|
| `app/` | Source API/worker, Dockerfile và giao diện frontend |
| `scripts/` | Thu thập cấu hình, build/deploy và các phép thử |
| `k8s/` | Manifests được render cho account của bạn |
| `infrastructure/terraform/` | Hạ tầng tương đương bằng Terraform |
| `.local/` | Kubeconfig, metadata lab và các file tạm trên máy |

`source scripts/env.sh` đặt `KUBECONFIG` vào `.local/kubeconfig`. Ở bước này chưa có `.local/lab.env`, nên biến `APP_HOST` chưa được script tự nạp. Khai báo domain của bạn để sử dụng khi cấp certificate:

```bash
export DNS_ZONE_NAME='example.com.'
# Thay example.com. bằng hosted zone thực tế, giữ dấu chấm cuối.
export APP_HOST="notes.${DNS_ZONE_NAME%.}"
printf 'Region: %s\nApp hostname: %s\n' "$AWS_REGION" "$APP_HOST"
```

Kết quả minh họa:

```text
Region: us-east-1
App hostname: notes.example.com
```

Trong terminal mới, kích hoạt lại `.venv`, đặt profile/Region và `source scripts/env.sh`. Trước khi bước thu thập cấu hình hoàn tất, khai báo lại `DNS_ZONE_NAME` theo giá trị bạn đã chọn.

## Quyền và chi phí

Lab cần quyền tạo/quản lý VPC, EC2, EKS, IAM roles/PassRole, ELB, RDS, SQS, ECR, ACM và Route 53. Tài khoản cần có quyền sử dụng WAF, Inspector và KMS cho các phần thực hành tương ứng. Nếu gặp lỗi thiếu quyền, kiểm tra IAM policies và chính sách của tổ chức trước khi tiếp tục.

EKS, EC2, ALB, NAT Gateway/public IPv4, RDS và các dịch vụ bảo mật có thể phát sinh phí khi lab đang chạy. Xem [Cleanup](/cleanup/) để biết thứ tự gỡ tài nguyên khi kết thúc.

**Kết quả cần có:** STS trả đúng account, các công cụ sẵn sàng, Docker daemon hoạt động và mã nguồn nằm trong thư mục làm việc. Tiếp tục [tạo VPC](/preparation/2-vpc/).
'''),
('2-vpc','Tạo VPC, subnets và đường định tuyến',r'''
## Mục tiêu chuẩn bị

ALB cần public subnets để nhận request từ Internet. Worker nodes chạy trong private application subnets; RDS sử dụng database subnets riêng. NAT Gateway cung cấp outbound cho private workers khi tải image và gọi AWS APIs.

![Kiến trúc AWS sẽ triển khai](/images/aws-architecture.svg "Ba nhóm subnet phục vụ điểm vào, workload và database.")

## Tạo VPC và subnets trên Console

1. Mở **VPC → Your VPCs → Create VPC**, chọn **VPC only**. Đặt Name `eks-did`, IPv4 CIDR `10.20.0.0/16`, tenancy Default.
2. Sau khi tạo, chọn VPC → **Actions → Edit VPC settings**, bật **DNS resolution** và **DNS hostnames**.
3. Mở **Subnets → Create subnet**, chọn VPC vừa tạo. Dùng hai AZ có sẵn trong account, ví dụ `us-east-1a` và `us-east-1b`:

| Name | AZ | IPv4 CIDR |
|---|---|---|
| `eks-did-public-a` | AZ A | `10.20.0.0/20` |
| `eks-did-public-b` | AZ B | `10.20.16.0/20` |
| `eks-did-private-a` | AZ A | `10.20.32.0/20` |
| `eks-did-private-b` | AZ B | `10.20.48.0/20` |
| `eks-did-database-a` | AZ A | `10.20.64.0/24` |
| `eks-did-database-b` | AZ B | `10.20.65.0/24` |

Tên cần chứa `-public-`, `-private-` hoặc `-database-` để script nhận diện vai trò subnet. Tên trong ảnh có hậu tố AZ hoặc số khác bảng nhưng giữ cùng quy tắc này.

![Các nhóm subnet trên Console](/images/console-subnets.png "① Public subnet. ② Private application subnet. ③ Database subnet. Các subnet 172.31 thuộc default VPC.")

4. Chọn từng private/database subnet → **Actions → Edit subnet settings**: tắt **Enable auto-assign public IPv4 address**.
5. Trong **Tags**, thêm `kubernetes.io/role/elb = 1` cho hai public subnets, và `kubernetes.io/role/internal-elb = 1` cho hai private application subnets.

## Tạo Internet Gateway, NAT và route tables

1. **Internet gateways → Create internet gateway**, tên `eks-did-igw`. Sau khi tạo, chọn **Actions → Attach to VPC**, chọn `eks-did`.
2. **Route tables → Create route table**, tên `eks-did-public`, VPC `eks-did`. Mở **Routes → Edit routes → Add route**, destination `0.0.0.0/0`, target Internet Gateway vừa attach.
3. Mở **Subnet associations → Edit subnet associations**, chọn **hai public subnets**, lưu lại.
4. **NAT gateways → Create NAT gateway**, tên `eks-did-nat`, chọn public subnet AZ A, connectivity type **Public**, chọn **Allocate Elastic IP**, tạo và chờ **Available**.
5. Tạo route table `eks-did-private`. Thêm `0.0.0.0/0` đến **NAT Gateway** vừa tạo. Trong Subnet associations, chọn hai private application subnets.
6. Tạo route table `eks-did-database-isolated`. Giữ route `10.20.0.0/16 → local` có sẵn, không thêm default route; associate hai database subnets.

| Route table | Subnets được associate | Default route |
|---|---|---|
| `eks-did-public` | Public A, B | `0.0.0.0/0 → igw-…` |
| `eks-did-private` | Application A, B | `0.0.0.0/0 → nat-…` |
| `eks-did-database-isolated` | Database A, B | Không có |

Route table phải được associate đúng subnet mới có tác dụng. Một NAT cho hai AZ là đánh đổi chi phí của lab; thiết kế production cần đánh giá availability và cross-AZ traffic.

## Kiểm tra trước khi tạo EKS

Từ thư mục lab, chạy:

```bash
export VPC_ID=$(aws ec2 describe-vpcs --filters Name=tag:Name,Values=eks-did \
  --query 'Vpcs[0].VpcId' --output text)
printf 'VPC: %s\n' "$VPC_ID"
aws ec2 describe-subnets --filters "Name=vpc-id,Values=$VPC_ID" \
  --query 'Subnets[].{Name:Tags[?Key==`Name`]|[0].Value,CIDR:CidrBlock,AZ:AvailabilityZone,PublicIP:MapPublicIpOnLaunch}' --output table
aws ec2 describe-route-tables --filters "Name=vpc-id,Values=$VPC_ID" \
  --query 'RouteTables[].{ID:RouteTableId,Subnets:Associations[].SubnetId,Routes:Routes}'
```

Kết quả cần có: sáu subnet đúng CIDR; private/database không tự cấp public IP; hai public subnets dùng IGW; hai application subnets dùng NAT; hai database subnets chỉ dùng local route. Route table main tự tạo của VPC có thể vẫn tồn tại, nhưng sáu subnet lab phải có các explicit associations nêu trên.

Tiếp tục [tạo EKS và worker nodes](/preparation/3-eks/).
'''),
('3-eks','Tạo EKS, CNI role và managed worker nodes',r'''
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
'''),
('4-data-services','Tạo RDS PostgreSQL, SQS và ECR',r'''
## Mục tiêu chuẩn bị

API lưu ghi chú trên RDS. Worker dùng cùng database với SQL user riêng và nhận công việc qua SQS. ECR chứa image do bạn build cho API, worker và Job khởi tạo database.

## Tạo database Security Group và subnet group

1. EKS → cluster → **Configuration → Networking**, copy **Cluster security group ID**. Managed nodes của lab sử dụng group này vì launch template không ghi đè Security Groups.
2. VPC → **Security groups → Create**, tên `eks-did-database`, VPC `eks-did`. Thêm inbound PostgreSQL TCP `5432`, source là **cluster Security Group ID** vừa lấy. Giữ outbound mặc định của lab.
3. RDS → **Subnet groups → Create DB subnet group**, tên `eks-did-database`, VPC `eks-did`. Chọn hai AZ và **hai database subnets** `10.20.64.0/24`, `10.20.65.0/24`.

Security Group này giới hạn nguồn ở mức node. NetworkPolicy sẽ bổ sung giới hạn theo pod trong chương 3.

## Tạo RDS PostgreSQL

1. RDS → **Databases → Create database → Standard create**, engine **PostgreSQL 17**, chọn phiên bản khả dụng trong nhánh 17. Lượt lab dùng `17.11`.
2. DB instance identifier `eks-did`, master username `labadmin`, chọn **Manage master credentials in AWS Secrets Manager**.
3. Chọn instance `db.t3.micro`, Single-AZ, storage **20 GiB gp3**, bật storage encryption. Single-AZ là lựa chọn giảm chi phí của môi trường thực hành.
4. Connectivity: VPC `eks-did`, DB subnet group vừa tạo, **Public access: No**, chỉ gắn Security Group `eks-did-database`. Không tạo thêm kết nối EC2 tự động.
5. Database authentication: **Password and IAM database authentication**. Additional configuration → Initial database name: **`notes`**.
6. Backup retention 1 ngày cho lab; kiểm tra lại các lựa chọn có tính phí trước khi tạo. Đợi database **Available**.

Xác nhận các thông số bằng CLI:

```bash
aws rds describe-db-instances --db-instance-identifier eks-did \
  --query 'DBInstances[0].{Status:DBInstanceStatus,Database:DBName,Public:PubliclyAccessible,IAM:IAMDatabaseAuthenticationEnabled,Encrypted:StorageEncrypted,ResourceID:DbiResourceId,SecretARN:MasterUserSecret.SecretArn}'
```

Kết quả cần có `Status=available`, `Database=notes`, `Public=false`, `IAM=true`, `Encrypted=true`, có ResourceID và SecretARN. Lưu ý **DB resource ID** có dạng `db-…`, dùng cho IAM policy; nó khác identifier `eks-did`.

## Tạo SQS queue

1. SQS → **Queues → Create queue**, type **Standard**, tên `eks-did-reports`.
2. Visibility timeout **60 giây**, message retention **1 ngày**, giữ các cấu hình khác ở giá trị phù hợp cho lab.
3. Encryption: bật server-side encryption, chọn **Amazon SQS key (SSE-SQS)**. Access policy không cấp quyền public; role API/worker sẽ có identity policies riêng.
4. Tạo queue, ghi lại **Queue URL** và **Queue ARN**. URL dùng khi gọi API SQS; ARN dùng trong IAM policy.

![Queue và cơ chế mã hóa](/images/console-sqs-encryption.png "① Cột Encryption. ② Queue sử dụng SSE-SQS.")

## Tạo ECR repository

1. ECR → **Private repositories → Create repository**, tên `eks-did/notes`.
2. Image tag mutability **Immutable**, encryption **AES-256**. Bật basic scan on push ở cấu hình registry nếu được phép; enhanced scanning được thực hành ở chương 5.
3. Tạo repository và ghi Repository URI. Repository chưa có image ở thời điểm này.

## Kiểm tra tài nguyên sẵn sàng

```bash
aws sqs get-queue-url --queue-name eks-did-reports
aws ecr describe-repositories --repository-names eks-did/notes \
  --query 'repositories[0].{URI:repositoryUri,Mutability:imageTagMutability,Encryption:encryptionConfiguration.encryptionType}'
```

SQS trả QueueUrl; ECR trả URI của đúng account, mutability `IMMUTABLE`, encryption `AES256`. RDS phải Available trước khi triển khai Job khởi tạo ở bước 7.

Tiếp tục [chuẩn bị certificate và WAF](/preparation/5-https-waf/).
'''),
('5-https-waf','Chuẩn bị domain, ACM certificate và WAF',r'''
## Mục tiêu chuẩn bị

Ứng dụng sẽ sử dụng hostname `notes.<domain>`. Certificate cần có trước khi tạo Ingress HTTPS; record ứng dụng trỏ đến ALB sẽ được tạo sau khi ALB xuất hiện.

## Xác nhận public hosted zone

1. Route 53 → **Hosted zones**, chọn public hosted zone của domain bạn quản lý. Ghi tên zone, ví dụ `example.com.`.
2. Đối chiếu NS records với nameservers được delegate ở domain cha/registrar. Nếu hosted zone đã được cấu hình, kiểm tra và giữ nguyên delegation đang sử dụng.
3. Trong terminal, đặt tên zone thực tế:

```bash
export DNS_ZONE_NAME='example.com.'
export APP_HOST="notes.${DNS_ZONE_NAME%.}"
printf '%s\n' "$APP_HOST"
```

Thay `example.com.` trước khi chạy. Domain hiện chưa cần có record ứng dụng; ACM sẽ tạo record DNS validation riêng.

## Yêu cầu certificate trên ACM

1. Mở **ACM tại us-east-1 → Request certificate → Request a public certificate**.
2. Domain name nhập hostname ứng dụng, ví dụ `notes.example.com`; chọn **DNS validation** và tạo request.
3. Mở certificate → **Create records in Route 53**, chọn domain cần xác thực và tạo validation record.
4. Đợi **Status: Issued**, validation **Success**. Copy certificate ARN để đối chiếu. Certificate phải cùng Region với ALB.

![Certificate của ứng dụng](/images/console-acm-certificate.png "① Issued. ② Domain. ③ DNS validation Success.")

## Tạo WAF Web ACL cho lab

1. WAF & Shield → **Web ACLs → Create web ACL**, tên `eks-did`, scope **Regional**, Region `us-east-1`.
2. Chọn default action **Allow**. ALB chưa được tạo nên chưa associate resource tại bước này.
3. Thêm custom rule tên `workshop-header-test`, loại regular rule, match **single header** `x-workshop-test`.
4. Match type **Exactly matches string**, string `block-me`, text transformation **None**, action **Block**. Bật sampled requests/metrics, lưu rule và Web ACL.
5. Copy Web ACL ARN. Script thu thập cấu hình sẽ tìm theo tên `eks-did`; controller gắn Web ACL vào ALB khi tạo Ingress.

![Rule kiểm chứng WAF](/images/console-waf-rule.png "① workshop-header-test. ② Action Block.")

Rule header này tạo ra một kết quả thử rõ ràng; việc lựa chọn managed rules cho production nằm ngoài cấu hình baseline. Nếu gặp lỗi thiếu quyền khi tạo WAF, kiểm tra quyền IAM và chính sách của tổ chức; chỉ kiểm chứng bước này sau khi tạo được Web ACL và gắn vào ALB.

## Kiểm tra trước khi triển khai ứng dụng

```bash
aws acm list-certificates --certificate-statuses ISSUED \
  --query 'CertificateSummaryList[].{Domain:DomainName,ARN:CertificateArn}'
aws wafv2 list-web-acls --scope REGIONAL \
  --query 'WebACLs[?Name==`eks-did`].{Name:Name,ARN:ARN}'
```

Cần thấy certificate đúng hostname và Web ACL `eks-did`. Chưa thử curl domain ở bước này vì chưa có ALB/record ứng dụng. Tiếp tục [cấp quyền workload](/preparation/6-workload-permissions/).
'''),
('6-workload-permissions','Cấp IAM roles và Pod Identity cho workload',r'''
## Mục tiêu chuẩn bị

Ứng dụng cần temporary AWS credentials trước khi chạy: API gửi SQS, worker nhận message, Job db-init đọc master secret để khởi tạo database, controller tạo ALB. Tạo các quyền cần thiết ở đây để baseline hoạt động; chương 4 tiếp tục giải thích và kiểm chứng từng ranh giới quyền.

## Chuẩn bị các giá trị ARN

Đọc các giá trị metadata sau, không lấy nội dung master password:

```bash
aws sts get-caller-identity --query Account --output text
aws rds describe-db-instances --db-instance-identifier eks-did \
  --query 'DBInstances[0].{DBResourceID:DbiResourceId,MasterSecretARN:MasterUserSecret.SecretArn}'
QUEUE_URL=$(aws sqs get-queue-url --queue-name eks-did-reports --query QueueUrl --output text)
aws sqs get-queue-attributes --queue-url "$QUEUE_URL" \
  --attribute-names QueueArn --query Attributes.QueueArn --output text
```

Dùng account ID, DB resource ID, secret ARN và queue ARN thực tế để thay các placeholders trong policies dưới đây.

## Tạo bốn IAM roles

Trong IAM → **Roles → Create role → Custom trust policy**, tạo lần lượt:

| Role name | Namespace | ServiceAccount |
|---|---|---|
| `eks-did-api` | `notes` | `api` |
| `eks-did-worker` | `notes` | `worker` |
| `eks-did-db-init` | `notes` | `db-init` |
| `eks-did-controller` | `kube-system` | `aws-load-balancer-controller` |

Dùng trust policy sau cho từng role, thay `NAMESPACE` và `SERVICE_ACCOUNT` theo đúng hàng trong bảng:

```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": {"Service": "pods.eks.amazonaws.com"},
    "Action": ["sts:AssumeRole", "sts:TagSession"],
    "Condition": {"StringEquals": {
      "aws:RequestTag/kubernetes-namespace": "NAMESPACE",
      "aws:RequestTag/kubernetes-service-account": "SERVICE_ACCOUNT"
    }}
  }]
}
```

![Trust policy của API role](/images/console-api-trust.png "① EKS Pod Identity service principal. ② AssumeRole. ③ TagSession. Condition giới hạn namespace và ServiceAccount.")

## Gắn permissions policy cho từng role

Mở từng role → **Permissions → Add permissions → Create inline policy → JSON**. Các placeholders sau cần được thay bằng giá trị ở bước đầu.

**Role API**, policy name `scoped-application`:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {"Effect":"Allow","Action":"sqs:SendMessage","Resource":"QUEUE_ARN"},
    {"Effect":"Allow","Action":"rds-db:connect","Resource":"arn:aws:rds-db:us-east-1:ACCOUNT_ID:dbuser:DB_RESOURCE_ID/notes_api"}
  ]
}
```

**Role worker**, policy name `scoped-application`:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {"Effect":"Allow","Action":["sqs:ReceiveMessage","sqs:DeleteMessage","sqs:GetQueueAttributes"],"Resource":"QUEUE_ARN"},
    {"Effect":"Allow","Action":"rds-db:connect","Resource":"arn:aws:rds-db:us-east-1:ACCOUNT_ID:dbuser:DB_RESOURCE_ID/notes_worker"}
  ]
}
```

**Role db-init**, policy name `read-one-bootstrap-secret`:

```json
{
  "Version": "2012-10-17",
  "Statement": [{"Effect":"Allow","Action":"secretsmanager:GetSecretValue","Resource":"MASTER_SECRET_ARN"}]
}
```

**Role controller**, policy name `load-balancer-controller`: mở [controller-policy.json đã pin theo release](/source/terraform/controller-policy.json), copy toàn bộ JSON vào inline policy editor. Policy dành riêng cho controller; không gắn quyền này lên node role hoặc app roles.

Frontend chỉ phục vụ HTTP/proxy nên không có IAM role ứng dụng. Job db-init dùng master credentials một lần để tạo schema và SQL grants; API/worker sử dụng IAM database authentication với user riêng.

## Tạo EKS Pod Identity associations

1. EKS → cluster `eks-did` → **Access → Pod Identity associations → Create**.
2. Chọn IAM role, namespace và ServiceAccount theo bảng bốn roles ở trên. Giữ session tags hoạt động vì trust policy sử dụng các tags này.
3. Tạo đủ bốn associations. Có thể nhập namespace/ServiceAccount trước khi chúng được manifest tạo ở bước triển khai.
4. Trong **Add-ons**, xác nhận Amazon EKS Pod Identity Agent đang Active trên các nodes.

![Liên kết role với ServiceAccount](/images/console-pod-identity.png "① Namespace notes. ② API ServiceAccount. ③ Worker ServiceAccount. Đọc IAM role ở cùng hàng để đối chiếu.")

## Kiểm tra trước khi deploy

```bash
aws eks list-pod-identity-associations --cluster-name eks-did \
  --query 'associations[].{Namespace:namespace,ServiceAccount:serviceAccount}' --output table
kubectl get daemonset eks-pod-identity-agent -n kube-system
```

Cần có bốn associations đúng namespace/ServiceAccount; DaemonSet agent có desired/current/ready tương ứng hai nodes. Có thể mở từng association trên Console để kiểm tra role ARN.

Tiếp tục [build image và triển khai ứng dụng](/preparation/7-deploy-application/).
'''),
('7-deploy-application','Build image và triển khai ứng dụng lên EKS',r'''
## Mục tiêu chuẩn bị

Bước này đưa source code thành các workload Kubernetes. API, worker và Job db-init sử dụng cùng image nhưng chạy chức năng khác nhau; frontend dùng Nginx. Database và queue đã được tạo bên ngoài cluster.

## Thu thập cấu hình account

Tại thư mục mã nguồn, kích hoạt virtual environment và khai báo đúng public zone:

```bash
source .venv/bin/activate
export AWS_PROFILE=guru AWS_REGION=us-east-1
export DNS_ZONE_NAME='example.com.'
# Thay example.com. bằng public hosted zone đã xác thực certificate.
source scripts/env.sh
python3 scripts/capture-config.py
```

Kết quả mong đợi:

```text
Saved .local/lab.json and .local/lab.env; no secret values are fetched.
```

Script đọc EKS, RDS, subnets, queue, ECR, certificate và hosted zone để tạo metadata cho account của bạn. Nó không cần Terraform state và không lấy giá trị master password. Nếu có nhiều public zones, `DNS_ZONE_NAME` giúp chọn đúng zone.

Nạp các biến vừa tạo:

```bash
source scripts/env.sh
printf 'App: %s\nVPC: %s\nECR: %s\n' "$APP_HOST" "$VPC_ID" "$ECR_REPO"
```

Bây giờ `APP_HOST` mới được nạp tự động từ `.local/lab.env`. Kết quả phải chứa hostname, VPC ID và ECR URI của lab đã tạo. File này chứa metadata hạ tầng và được giữ trong `.local/`.

## Build và push image lên ECR

```bash
bash scripts/build-push.sh
```

Script thực hiện bốn việc theo thứ tự: lấy ECR login token, Docker build `app/Dockerfile` cho `linux/amd64`, push bằng tag mới và lưu URI có digest vào `.local/image.txt`.

Dòng cuối có dạng:

```text
Pinned image: 123456789012.dkr.ecr.us-east-1.amazonaws.com/eks-did/notes@sha256:…
```

Mở **ECR → eks-did/notes → Images** để đối chiếu image vừa push. Tag giúp nhận diện lượt build; digest xác định nội dung image sẽ triển khai.

![Image trong ECR](/images/console-ecr-images.png "① Image digest. ② Image tags. Danh sách của bạn ban đầu chỉ có image vừa build; signature và image test xuất hiện ở chương 5.")

## Cài controller và triển khai manifests

```bash
bash scripts/deploy.sh
```

Đọc các công việc script thực hiện để đối chiếu với output:

| Bước trong script | Tài nguyên/kết quả |
|---|---|
| Cập nhật kubeconfig | Dùng cluster `eks-did`, file `.local/kubeconfig` |
| Helm install/upgrade controller | Chart `3.6.2`, namespace `kube-system`, ServiceAccount đã có Pod Identity association |
| Chạy `render.py` | Sinh `k8s/application.yaml` và `k8s/network-policies.yaml` theo metadata thực |
| Apply `application.yaml` | Tạo namespace, ConfigMap, ServiceAccounts, RBAC, Job, Deployments, Services và Ingress |
| Chờ Job `db-init` | Tạo schema, users `notes_api`/`notes_worker` và SQL grants trên RDS |
| Chờ rollout | Frontend 2 replicas, API 2 replicas, worker 1 replica |

Kết quả cần thấy gồm Job hoàn tất và các Deployment successfully rolled out. Script đã áp dụng cấu hình chạy non-root/Restricted cho app baseline, nhưng **chưa apply `network-policies.yaml`**. Các bài chương 3 giải thích các trường hardening và thực hành cách ly mạng trước/sau.

Kiểm tra riêng từng thành phần:

```bash
kubectl -n kube-system rollout status deployment/aws-load-balancer-controller
kubectl get job db-init -n notes
kubectl get deployments,pods,services,ingress -n notes
```

Job có completions `1/1`; Deployments có số ready `2/2`, `2/2`, `1/1`. Ingress cần có ADDRESS là DNS name của ALB. Nếu Job không hoàn tất, đọc `kubectl logs job/db-init -n notes`; nếu ALB chưa xuất hiện, đọc controller logs và Ingress events trước khi chuyển sang DNS.

## Tạo record ứng dụng và kiểm tra ALB

```bash
python3 scripts/publish-dns.py
```

Script UPSERT record CNAME cho hostname ứng dụng, trỏ đến hostname của ALB do Ingress tạo. Đây là record `notes`, khác với record DNS validation của ACM.

1. Route 53 → hosted zone → record `notes`: target là ALB của lab.
2. EC2 → Load Balancers → `eks-did-notes`: trạng thái Active; HTTP 80 redirect sang HTTPS 443, HTTPS listener forward đến target group frontend.
3. Target group → Targets: target type IP, backend HTTP:8080; chờ các frontend targets Healthy.

![ALB do controller tạo](/images/console-alb.png "① Load balancer Active, Application và internet-facing.")

![IP targets của frontend](/images/console-targets.png "① IP target type. ② HTTP:8080. ③ Healthy targets. ④ Pod IPs và port. Ảnh trong rollout có thể chứa target cũ Draining.")

**Kết quả cần có:** controller Ready, Job complete, ba Deployments đủ replicas, ALB Active, targets Healthy và record ứng dụng trỏ đúng ALB. Tiếp tục [kiểm tra ứng dụng baseline](/preparation/8-baseline/).
'''),
('8-baseline','Kiểm tra lab hoạt động trước khi học các lớp bảo vệ',r'''
## Mục tiêu kiểm tra

Trước khi thử NetworkPolicy hoặc phân quyền nâng cao, xác nhận đường truy cập và nghiệp vụ của ứng dụng đang hoạt động. Kết quả baseline giúp phân biệt hành vi bị chặn có chủ đích với một thành phần chưa được triển khai đúng.

Các output dưới đây là mẫu; tên pod, IP, ID ghi chú và thời gian thay đổi theo lượt thực hành.

## Nạp cấu hình và kiểm tra frontend

```bash
source scripts/env.sh
printf 'Hostname: %s\n' "$APP_HOST"
curl -sS -o /dev/null -w '%{http_code}\n' "https://$APP_HOST/"
```

Ví dụ:

```text
Hostname: notes.example.com
200
```

`source` nạp cấu hình từ `.local/lab.env`, thường không tự in gì. `curl` bỏ nội dung HTML và chỉ in status 200. Kết quả xác nhận domain HTTPS truy cập được frontend qua ALB.

## Kiểm tra đường frontend → API

```bash
curl -fsS "https://$APP_HOST/api/healthz"
printf '\n'
```

Kết quả:

```json
{"status": "ok", "workload": "api"}
```

Request đã đến API qua Nginx frontend. Health endpoint chưa kiểm tra thao tác database, nên cần phép thử tiếp theo.

## Lưu và đọc lại ghi chú

```bash
curl -fsS "https://$APP_HOST/api/notes" \
  -H 'Content-Type: application/json' -d '{"body":"baseline-note"}'
printf '\n'
curl -fsS "https://$APP_HOST/api/notes"
printf '\n'
```

POST trả một object có `id` và `body`; GET trả danh sách chứa ghi chú vừa tạo:

```json
{"id": 1, "body": "baseline-note"}
```

```json
[{"id": 1, "body": "baseline-note"}]
```

ID thực tế có thể lớn hơn 1 và danh sách có thể đã có dữ liệu thử khác. Việc đọc lại đúng ghi chú xác nhận luồng API → RDS và quyền SQL cần thiết.

## Gửi yêu cầu báo cáo cho worker

```bash
curl -fsS -X POST "https://$APP_HOST/api/reports"
printf '\n'
```

Kết quả có dạng:

```json
{"id": "…", "status": "queued"}
```

Chờ worker xử lý rồi đọc lại:

```bash
curl -fsS "https://$APP_HOST/api/reports"
printf '\n'
kubectl logs deployment/worker -n notes --tail=10
```

GET phải có report cùng ID đã gửi, với số lượng ghi chú `note_count`. Nếu lượt GET đầu chưa có, thực hiện lại sau vài giây. Kết quả xác nhận đường API → SQS → worker → RDS hoạt động.

## Đối chiếu pod IP và access logs

```bash
kubectl get pods -n notes -l app=frontend -o wide
```

Ví dụ:

```text
NAME                        READY   STATUS    RESTARTS   AGE   IP
frontend-7c8d9f6b5d-abc12    1/1     Running   0          10m   10.20.44.78
frontend-7c8d9f6b5d-def34    1/1     Running   0          10m   10.20.54.165
```

Đối chiếu cột IP với targets Healthy trong ALB target group. `READY 1/1` cho biết container của pod đã sẵn sàng.

```bash
kubectl logs -n notes -l app=frontend --tail=10 --prefix=true
```

Ví dụ một phần access log:

```text
[pod/frontend-…/frontend] … "GET /api/healthz HTTP/1.1" 200 …
```

`--prefix=true` thêm tên pod/container để biết pod nào nhận request. Log còn có thể chứa health checks của ALB; số dòng cuối không bảo đảm chứa mọi request vừa gửi.

## Điều kiện hoàn thành chuẩn bị

| Kiểm tra | Kết quả cần đạt |
|---|---|
| EKS nodes | Hai nodes Ready, private IP |
| Job db-init | Complete |
| Deployments | Frontend 2/2, API 2/2, worker 1/1 |
| Domain và HTTPS | Trang chủ trả 200, certificate hợp lệ |
| API | Health trả `workload: api` |
| RDS | Đọc lại được ghi chú vừa tạo |
| SQS/worker | Nhận được report cùng ID đã gửi |
| NetworkPolicy baseline | Chưa áp dụng policies của chương 3 |

```bash
kubectl get networkpolicy -n notes
```

Ở một lab mới, kết quả cuối là `No resources found in notes namespace.` Nếu đang dùng lại lab đã harden, ghi nhận policies đã tồn tại; không coi đó là baseline trước policy.

![Ứng dụng đã triển khai](/images/application-live.png "Frontend, API và worker cùng hoạt động với RDS/SQS.")

Khi các điều kiện trên đạt, đọc [Request Flow: Internet → ALB → Pod](/2-network-security/1-request-flow/). Từ đây, các lệnh sử dụng `$APP_HOST` và pod ứng dụng đã có đầy đủ đầu vào để chạy.
'''),
('9-terraform','Tùy chọn: dựng cùng lab bằng Terraform',r'''
## Chọn nhánh triển khai

Nhánh Console gồm các bước 0.2–0.7. Terraform là cách tạo cùng hạ tầng cho người muốn tái tạo lab bằng IaC. Chọn một nhánh tạo tài nguyên cho mỗi môi trường; các bước build/deploy và baseline vẫn dùng chung.

Nếu đã tạo bằng Console, có thể đọc mã Terraform để đối chiếu cấu hình. `terraform apply` với state rỗng sẽ cố tạo lại các tài nguyên cùng tên, nên không dùng nó như bước tiếp theo của nhánh Console.

## Cấu hình đầu vào

Hoàn thành công cụ, profile AWS và domain ở [bước 0.1](/preparation/1-workstation/), cài [Terraform CLI](https://developer.hashicorp.com/terraform/install), rồi chạy từ thư mục source:

```bash
source .venv/bin/activate
export AWS_PROFILE=guru AWS_REGION=us-east-1
aws sts get-caller-identity
curl -fsS https://checkip.amazonaws.com
cp infrastructure/terraform/terraform.tfvars.example infrastructure/terraform/terraform.tfvars
```

Sửa `terraform.tfvars`:

```hcl
admin_cidr = "YOUR_WORKSTATION_IP/32"
dns_zone_name = "YOUR_PUBLIC_ZONE."
enable_waf = true
enable_kms = true
enable_inspector = true
```

Thay IP và zone bằng giá trị thật. Các flags liên quan dịch vụ bị giới hạn bởi quyền truy cập hoặc chính sách tài khoản chỉ được tắt khi đã ghi nhận phần bài tương ứng chưa được kiểm chứng. WAF cần cho phép thử edge; KMS và Inspector được dùng ở chương 5.

## Tạo hạ tầng

```bash
terraform -chdir=infrastructure/terraform init
terraform -chdir=infrastructure/terraform fmt -check
terraform -chdir=infrastructure/terraform validate
terraform -chdir=infrastructure/terraform plan -out=lab.tfplan
```

`validate` cần báo cấu hình hợp lệ. Đọc plan: account/Region đúng, chỉ tạo tài nguyên lab và không có thay đổi tài nguyên khác. Sau đó:

```bash
terraform -chdir=infrastructure/terraform apply lab.tfplan
```

Chờ apply hoàn tất. Terraform tạo VPC, EKS/nodes/add-ons, RDS/SQS/ECR, ACM/WAF, workload roles/associations và các tài nguyên được bật trong cấu hình. Nó chưa build image và chưa triển khai frontend/API/worker.

State và plan lưu thông tin hạ tầng nhạy cảm; giữ ngoài Git và website. Nhóm nhiều người cần remote backend và locking phù hợp trước khi cùng thao tác state.

## Triển khai và kiểm tra

Sau `Apply complete`, tiếp tục [bước 0.7: Build image và triển khai ứng dụng](/preparation/7-deploy-application/), rồi [bước 0.8: Baseline](/preparation/8-baseline/). `capture-config.py` đọc tài nguyên AWS thực tế nên dùng chung cho cả Console và Terraform.

Cleanup của nhánh này gỡ tài nguyên do Kubernetes controller tạo trước, sau đó dùng đúng state để destroy. Xem [hướng dẫn cleanup](/cleanup/).
''')
]

def write_preparation(write):
    body = '''Phần này dựng ứng dụng nền từ một tài khoản AWS trước khi thực hành các lớp bảo vệ. Thực hiện theo thứ tự bên dưới; mỗi trang nêu cấu hình và kết quả cần có để chuyển sang bước tiếp theo.

Ứng dụng gồm frontend, API và worker trên EKS; database dùng RDS và hàng đợi dùng SQS. Có thể xem [kiến trúc tổng quan](/1-introduction/4-architecture/) trước khi bắt đầu.

## Nội dung

'''
    body += '\n\n'.join(f'0.{i}. [{title}](/preparation/{slug}/)' for i,(slug,title,_) in enumerate(SETUP,1))
    body += '''

## Trình tự thực hiện

**Nhánh Console:** 0.1 → 0.2 → 0.3 → 0.4 → 0.5 → 0.6 → 0.7 → 0.8.

**Nhánh Terraform:** 0.1 → 0.9 → 0.7 → 0.8.

Sau bước 0.8, lab có domain HTTPS, ba workload chạy được, đọc/ghi RDS và xử lý SQS. NetworkPolicy chưa được áp dụng để còn quan sát trạng thái trước/sau trong chương 3. Cấu hình non-root và quyền workload cần để chạy ứng dụng đã nằm trong baseline; các chương sau giải thích và kiểm chứng chi tiết.

Ảnh được chụp từ lab tham chiếu; các output mẫu có chú thích và giá trị minh họa. Thay account ID, domain, resource IDs và IP bằng giá trị của môi trường đang sử dụng. [Cleanup](/cleanup/) hướng dẫn dừng tài nguyên có tính phí khi kết thúc.
'''
    write(Path('preparation'), 'Chuẩn bị lab', 2, body)
    for i, (slug, title, content) in enumerate(SETUP, 1):
        write(Path('preparation')/slug, title, i, content, f'<b>0.{i}.</b> ', **({'sequenceSkip': True, 'previousLesson': '/preparation/1-workstation/', 'nextLesson': '/preparation/7-deploy-application/'} if i == 9 else {}))
