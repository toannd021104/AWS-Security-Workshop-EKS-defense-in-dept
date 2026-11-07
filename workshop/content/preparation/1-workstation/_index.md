---
title: "Tài khoản AWS, công cụ và mã nguồn"
weight: 1
chapter: false
pre: "<b>0.1.</b> "
---

## Mục tiêu chuẩn bị

Phần thực hành sử dụng một máy Ubuntu Linux x86_64 có kết nối Internet và một AWS account sandbox. Các thao tác AWS ưu tiên Console; terminal được dùng để build container, thao tác Kubernetes và đọc kết quả chính xác.

Tài nguyên được tạo tại **US East (N. Virginia), us-east-1**, với prefix `eks-did`. Chọn cùng account và Region trong cả Console lẫn terminal. Nếu account đã có một lab cùng tên, kiểm tra tài nguyên hiện có trước khi tạo thêm.

## Đăng nhập và kiểm tra tài khoản

1. Đăng nhập AWS Console bằng phương thức sandbox cấp, kiểm tra account ID ở góc phải và chọn Region **us-east-1**.
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

`guru` là tên profile trên máy, không phải tên tài khoản AWS. Nếu chưa có profile, dùng thông tin được sandbox cấp để cấu hình `aws configure --profile guru`. Credentials tạm thời cần đủ session token trong profile và còn hạn; SSO sử dụng quy trình `aws configure sso`. Không cần tạo access key mới nếu sandbox đã cung cấp cách truy cập.

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

Lab cần quyền tạo/quản lý VPC, EC2, EKS, IAM roles/PassRole, ELB, RDS, SQS, ECR, ACM và Route 53. WAF, Inspector và KMS có thể bị giới hạn trong sandbox; ghi nhận đúng dịch vụ bị từ chối thay vì coi bài đó đã đạt.

EKS, EC2, ALB, NAT Gateway/public IPv4, RDS và các dịch vụ bảo mật có thể phát sinh phí khi lab đang chạy. Xem [Cleanup](/cleanup/) để biết thứ tự gỡ tài nguyên khi kết thúc.

**Kết quả cần có:** STS trả đúng account, các công cụ sẵn sàng, Docker daemon hoạt động và mã nguồn nằm trong thư mục làm việc. Tiếp tục [tạo VPC](/preparation/2-vpc/).
