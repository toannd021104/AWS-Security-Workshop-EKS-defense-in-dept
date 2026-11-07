# A Layered Approach to Amazon EKS Security

[Đọc workshop trên GitHub Pages](https://toannd021104.github.io/eks-defense-in-depth-workshop/).

Workshop tiếng Việt, tập trung từ Internet đến pod, Kubernetes workload security, IAM/RBAC và supply chain/data security. Bản mới được chắt lọc từ `../test.md`; không sửa bản gốc hoặc site `../AWS-Security-WS`.

ZIP tải từ website chỉ gồm mã lab. Để chạy/chỉnh Hugo, clone toàn bộ repository.

## Đọc và chạy website

```bash
hugo server --source workshop --bind 0.0.0.0 --port 1314
```

Mở http://localhost:1314/. Năm module gồm 26 bài, có preparation, validation và cleanup riêng. Hướng dẫn ưu tiên Console → AWS CLI/API → Terraform. Slide, threat detection và incident response ngoài phạm vi.

## Triển khai lab bằng Terraform

AWS CLI profile `guru`, region `us-east-1`. Kiểm tra `aws sts get-caller-identity` trước. Cần domain public Route 53 có delegation hợp lệ cho HTTPS.

```bash
export AWS_PROFILE=guru AWS_REGION=us-east-1
python3 -m pip install boto3 PyYAML
cp infrastructure/terraform/terraform.tfvars.example infrastructure/terraform/terraform.tfvars
# Sửa admin_cidr /32 và dns_zone_name. Không dùng nguyên địa chỉ minh họa.
terraform -chdir=infrastructure/terraform init
terraform -chdir=infrastructure/terraform validate
terraform -chdir=infrastructure/terraform plan -out=lab.tfplan
terraform -chdir=infrastructure/terraform apply lab.tfplan
source scripts/env.sh
python3 scripts/capture-config.py
source scripts/env.sh
bash scripts/build-push.sh
bash scripts/deploy.sh
python3 scripts/publish-dns.py
```

Đợi DNS public và targets healthy trước khi chạy test. Mọi cách Console/CLI/Terraform đều dùng cùng tên `eks-did` và naming subnet đã ghi trong trang preparation; không cần state Terraform để render khi chọn Console.

## Supply chain và validation

```bash
bash scripts/supply-chain.sh
bash scripts/admission.sh
bash scripts/prepare-unsigned.sh
python3 scripts/verify.py --supply-chain
# Gate trả exit 1 nếu scan chưa hoàn tất hoặc còn HIGH/CRITICAL:
python3 scripts/scan-gate.py
python3 scripts/check_site.py
```

`prepare-unsigned.sh` tạo digest khác chỉ dùng làm negative admission test; không deploy image đó. Signing key private nằm trong `.local/`, public key trong `k8s/cosign.pub`. ECR verification token có hạn khoảng 12 giờ; refresh qua admission script. Kyverno ClusterPolicy dùng API legacy còn được hỗ trợ ở release đã pin, cần đánh giá migration ImageValidatingPolicy khi nâng cấp.

Kết quả public nằm trong `evidence/verification.json` và trang validation. `.local` giữ log, kubeconfig và dữ liệu nhạy cảm: không publish. Console screenshots thực tế được chụp bằng phiên chỉ đọc; thông tin đăng nhập không được đưa lên website.

## Chỉnh sửa nội dung và sơ đồ

- Trang Markdown chuẩn nằm trong `workshop/content/`.
- `scripts/write_workshop.py` là nguồn sinh bản nội dung đầu tiên; nếu sửa Markdown trực tiếp, không chạy lại generator vì nó ghi đè các trang đó. Các thay đổi bản gốc nên sửa trong generator rồi sinh lại để đồng bộ.
- `scripts/diagrams.py` sinh SVG và draw.io từ icon AWS/Kubernetes ở `/home/ubuntu/devops-blog2/src/assets/icons/`. Artifacts đã có trong repo nên build Hugo không cần thư mục icon ngoài.
- `k8s/application.yaml` và `network-policies.yaml` là manifests đã render. Người dùng account khác chạy `capture-config.py`, build-push và render lại, không áp dụng endpoint/ARN của account ví dụ.
- Website chỉ mount allowlisted Terraform source, app/scripts và manifests; không mount `.local` hoặc state.

## Cleanup và chi phí

```bash
source scripts/env.sh
python3 scripts/cleanup.py
terraform -chdir=infrastructure/terraform plan -destroy -out=destroy.tfplan
terraform -chdir=infrastructure/terraform apply destroy.tfplan
```

Review đúng account và tài nguyên lab. Cleanup xóa Ingress trước để controller gỡ ALB; sau đó mới destroy VPC. RDS disposable không giữ final snapshot, ECR force-delete images; đừng dùng cho dữ liệu cần giữ. Inspector là account-level setting; chỉ tắt khi chính lab bật và không có consumer khác. CMK schedule deletion 7 ngày.

EKS, EC2, ALB, NAT/public IPv4, RDS, WAF, Inspector và KMS tiếp tục tính phí khi để lab chạy. Hai node/private subnets không làm toàn hệ thống HA: lab dùng một NAT, Single-AZ RDS và một replica controller/admission để giảm chi phí.
