from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
C=ROOT/'workshop/content'
MODULES=[('1-introduction','Introduction to Defense in Depth'),('2-network-security','Network Security – Securing the Request Path'),('3-kubernetes-security','Kubernetes Security – Securing Workloads'),('4-identity','Identity & Access Management – Securing Permissions'),('5-supply-chain-data','Supply Chain & Data Security')]
PAGES=[]
FIGURES={
 (1,3):('console-eks','EKS cluster thực tế: trạng thái Active, version 1.35 và managed control plane.'),
 (2,2):('console-subnets','Các subnet của lab có prefix eks-did; các subnet 172.31 thuộc default VPC, không được sử dụng.'),
 (2,5):('console-alb','ALB do controller tạo: Active, internet-facing và trải hai AZ.'),
 (2,6):('console-targets','① IP target type và port 8080. ② Hai targets healthy. ③ Pod IPs; target test cũ có thể đang draining.'),
 (4,3):('console-access','Observer map vào group notes-observers và không có access policy admin; bootstrap identity được quản lý riêng.'),
 (5,1):('console-ecr','Repository thật: app image pin digest, Cosign signature artifact và unsigned image chỉ dùng negative test.'),
 (5,3):('console-rds','① RDS Available. ② IAM authentication Enabled; master credentials do Secrets Manager quản lý.')
}

def write(path,title,weight,body,pre=''):
 p=C/path/'_index.md';p.parent.mkdir(parents=True,exist_ok=True)
 p.write_text('---\ntitle: '+json.dumps(title,ensure_ascii=False)+'\nweight: '+str(weight)+'\nchapter: false\npre: '+json.dumps(pre)+'\n---\n\n'+body.strip()+'\n')
def page(m,n,slug,title,body):
 if (m,n) in FIGURES:
  name,caption=FIGURES[(m,n)]
  figure='\n\n![Ảnh AWS Console thực tế](/images/'+name+'.png "'+caption+'")\n\n'
  pos=body.find('### CLI')
  body=body[:pos]+figure+body[pos:] if pos>=0 else body+figure
 path=MODULES[m-1][0]+'/'+str(n)+'-'+slug
 write(Path(path),title,n,body,f'<b>{m}.{n}.</b> ');PAGES.append((m,n,path,title))
write(Path('.'),'Defense in Depth for Amazon EKS',0,r'''
<span class="lab-tag">HANDS-ON WORKSHOP · AWS + KUBERNETES</span>

# Từ Internet đến pod: hiểu đường đi, xây từng lớp bảo vệ

Một website chạy được chưa chứng minh rằng các thành phần chỉ truy cập được đúng nơi cần thiết. Workshop này giúp bạn dựng một ứng dụng EKS, theo dõi request từ ALB đến pod, rồi giới hạn network và quyền của từng chủ thể.

Bạn đã biết AWS/Kubernetes nhưng quên một số khái niệm? Mỗi bài nhắc lại đúng kiến thức sắp dùng, giải thích lựa chọn và dẫn đến một thao tác có thể kiểm chứng. Không cần học thuộc danh sách dịch vụ trước khi bắt đầu.

![High-level architecture: ứng dụng, quản trị và workload identity](/images/high-level.svg "Ba workload: frontend, API, worker. RDS và SQS là dịch vụ managed.")

### Sau workshop, bạn làm được gì?

- Giải thích chính xác ALB target type `ip` đưa request đến pod như thế nào.
- Xây VPC hai AZ, EKS private workers, ALB HTTPS, RDS private và SQS.
- Giới hạn frontend → API → database; kiểm tra pod không liên quan bị chặn.
- Cấp quyền Kubernetes cho người vận hành và quyền AWS riêng cho API/worker.
- Áp dụng pod hardening, kiểm tra image, ký digest và đặt admission gate.
- Chứng minh bằng cả hành động được phép và hành động bị từ chối.

### Bắt đầu

Đọc [Chuẩn bị và cách dùng workshop](/preparation/) trước. [Tải mã lab ZIP](/downloads/eks-defense-in-depth-lab.zip) để chạy các bài thực hành; source Hugo được giữ cùng repository. Bạn chọn **một** cách tạo hạ tầng: Console, CLI/API hoặc Terraform. Các cách mô tả cùng thiết kế; không tạo lại cùng tài nguyên bằng cả ba.

| Module | Câu hỏi dẫn đường |
|---|---|
| [1. Introduction](/1-introduction/) | Mỗi lớp bảo vệ giải quyết khoảng trống nào? |
| [2. Network Security](/2-network-security/) | Request từ Internet đến private pod bằng đường nào? |
| [3. Kubernetes Security](/3-kubernetes-security/) | Pod được kết nối và chạy với đặc quyền gì? |
| [4. Identity & Access Management](/4-identity/) | Ai được thao tác Kubernetes và AWS? |
| [5. Supply Chain & Data Security](/5-supply-chain-data/) | Image nào được chạy, dữ liệu được bảo vệ ở đâu? |

Kết quả thực nghiệm được ghi riêng tại [Kiểm chứng và trạng thái sandbox](/validation/). Một bước có hướng dẫn không đồng nghĩa đã chạy thành công trong sandbox. Xem [Cleanup](/cleanup/) khi kết thúc; tài nguyên AWS tiếp tục tính phí khi bạn đóng trình duyệt.

Threat detection, GuardDuty, incident response và slide không thuộc phiên bản này.
''')
write(Path('preparation'),'Chuẩn bị và cách dùng workshop',1,r'''
## Bạn sẽ xây gì?

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

Sau khi hạ tầng sẵn sàng, đọc Module 1 để hiểu vì sao cần từng lớp. [Cleanup](/cleanup/) là bước bắt buộc khi ngừng sử dụng lab.
''')
page(1,1,'defense-in-depth','Defense in Depth là gì?',r'''
## Một request hợp lệ không chứng minh toàn hệ thống an toàn

Giả sử website chỉ mở HTTPS, worker nodes không có public IP. Người dùng vẫn có thể khai thác lỗi trong API. Nếu API kết nối được mọi pod và mang quyền AWS rộng, tác động vượt xa một endpoint bị lỗi.

Defense in Depth là phối hợp nhiều lớp kiểm soát để giảm khả năng xâm nhập và giới hạn phạm vi ảnh hưởng khi một lớp không đủ. Trong workshop này, chúng ta tập trung vào **phòng ngừa và giới hạn quyền**, không dựng hệ thống detection/response.

| Câu hỏi | Lớp kiểm soát |
|---|---|
| Ai đến được điểm vào? | ALB listener, HTTPS, WAF, Security Group |
| Pod nào gọi được API? | NetworkPolicy |
| Container được chạy với đặc quyền gì? | Pod Security Admission, securityContext |
| Ai sửa được workload? | EKS Access Entry, Kubernetes RBAC |
| Pod được gọi AWS API nào? | Pod Identity và IAM policy |
| Artifact và dữ liệu được bảo vệ thế nào? | Scanning, signature gate, TLS, encryption, secret access |

### Quan sát ngay trong lab

**Console:** VPC → Subnets kiểm tra workers ở private subnet; EKS → Resources xem frontend, API, worker. Đây mới là quan sát cấu hình.

**CLI/API:** kiểm tra những controls hiện có:

```bash
kubectl get pods -n notes -o wide
kubectl get networkpolicy -n notes
kubectl get serviceaccounts -n notes
```

Nếu chưa có NetworkPolicy, namespace vẫn không tự cô lập traffic. Nếu đã có policy, vẫn cần phép thử để biết engine có thực thi.

### Quyết định của lab

Mỗi lớp có một phép thử dương và âm. Sau khi mở frontend → API, chúng ta còn thử pod không liên quan → API. Sau khi cấp API quyền gửi SQS, thử nhận message bằng cùng role phải bị từ chối.

Terraform/YAML là bản mô tả ý định; kết quả kết nối và kết quả authorization mới chứng minh hành vi. Bài kế tiếp xác định những khoảng trống cụ thể trên EKS.
''')
page(1,2,'why-eks','Tại sao Amazon EKS cần Defense in Depth?',r'''
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
''')
page(1,3,'shared-responsibility','AWS Shared Responsibility Model',r'''
## Xác định việc AWS làm và việc bạn phải làm

Lab sử dụng **EKS managed node groups**, không dùng Fargate hoặc Auto Mode. Ranh giới trách nhiệm phụ thuộc lựa chọn compute.

| Thành phần | AWS quản lý | Bạn cấu hình và kiểm chứng |
|---|---|---|
| EKS control plane | Hạ tầng và vận hành control plane | Endpoint exposure, access entries, authorization |
| Managed node group | Cơ chế provisioning/update tích hợp | Chọn phiên bản AMI, rollout cập nhật, IAM, IMDS, workload placement |
| VPC | Hạ tầng mạng AWS | Subnet, route, SG/NACL, outbound |
| Workload | Kubernetes API/compute nền | Image, pod privileges, NetworkPolicy, identity |
| RDS | Hạ tầng dịch vụ DB theo cấu hình | Public access, SG, users/grants, backup, encryption |

### Thực hành đọc ranh giới

**Console:** EKS → Compute → node group, ghi phiên bản AMI release và Kubernetes version. RDS → database → Connectivity & security, xác nhận Publicly accessible = No.

```bash
aws eks describe-nodegroup --cluster-name eks-did --nodegroup-name private-workers \
  --query 'nodegroup.{status:status,version:version,release:releaseVersion}'
aws rds describe-db-instances --db-instance-identifier eks-did \
  --query 'DBInstances[0].{public:PubliclyAccessible,encrypted:StorageEncrypted,multiAZ:MultiAZ}'
```

Mong đợi: node group `ACTIVE`, DB private và encrypted. `MultiAZ=false` là giảm chi phí lab, không phải khuyến nghị HA cho production.

### Bài học

Có encryption không đồng nghĩa mọi người đều bị chặn đọc dữ liệu: IAM/SQL/RBAC vẫn quyết định quyền truy cập. Có managed nodes không đồng nghĩa node image luôn được cập nhật theo yêu cầu của bạn. Trong Terraform, cấu hình ở `aws_eks_node_group.private` và `aws_db_instance.this`; xem [mã hạ tầng](/source/terraform/main.tf).
''')
page(1,4,'architecture','Tổng quan kiến trúc và các Security Layers',r'''
## Đọc hệ thống qua ba luồng

![AWS architecture với VPC, subnet, EKS, RDS và SQS](/images/aws-architecture.svg "Khung nét đứt biểu diễn ranh giới mạng/logical. Association chứng chỉ/WAF không phải network hop.")

**Luồng ứng dụng:** client phân giải DNS rồi kết nối ALB bằng HTTPS. ALB mở kết nối đến frontend pod trên 8080. Nginx proxy `/api/` qua Service API. API dùng TLS đến RDS, ký token IAM DB auth cho user `notes_api`.

**Luồng nền:** API gửi SQS message. Worker chủ động long-poll SQS, đếm ghi chú và ghi report bằng SQL role `notes_worker`. SQS không đẩy inbound connection vào worker.

**Luồng quản trị:** `kubectl` đến EKS API endpoint qua đường riêng; IAM xác thực, EKS authorizer/RBAC phân quyền. Request này không qua ALB ứng dụng.

### Workload identity là luồng cấp credentials

Pod Identity association liên kết namespace/ServiceAccount với IAM role. SDK lấy credentials tạm thời qua agent; API/worker sau đó dùng credentials để gọi SQS hoặc ký token RDS. Đây không phải đường mà HTTP request từ người dùng phải lần lượt đi qua.

### Những lựa chọn cố định trong lab

| Lựa chọn | Lý do | Đánh đổi |
|---|---|---|
| ALB `ip` | VPC CNI cung cấp pod IP định tuyến được | Phải hiểu pod readiness và target registration |
| Private nodes, RDS isolated | Giảm điểm vào public | Cần outbound cho image/API và đường quản trị phù hợp |
| NetworkPolicy + node SG | Ít thành phần, dễ quan sát | SG không phân biệt từng pod; pod isolation do policy engine |
| Pod Identity | Temporary credentials, role theo ServiceAccount | Cần agent/EKS Auth và SDK tương thích |
| Một NAT, RDS Single-AZ | Giảm chi phí sandbox | Không đạt HA đa AZ cho toàn hệ thống |

**Console:** xem VPC Resource map và EKS Resources. **CLI:** `kubectl get pods,svc,ingress -n notes -o wide`. Đối chiếu pod IP với target group ở 2.6.

Tải [AWS draw.io](/images/aws-architecture.drawio) hoặc [high-level draw.io](/images/high-level.drawio) để chỉnh sửa. Các hình dùng icon từ bộ AWS/Kubernetes đã thống nhất.
''')
page(2,1,'request-flow','Request Flow: Internet → ALB → Pod',r'''
## Theo dõi một request thay vì đọc danh sách dịch vụ

![Request path từ client đến PostgreSQL](/images/request-path.svg "ALB gửi đến frontend pod IP; frontend gọi API qua Service nội bộ.")

Khi mở `https://notes.<domain>`, client phân giải DNS rồi mở TLS đến ALB. DNS không proxy HTTP. ALB kết thúc TLS, kiểm tra listener rule, chọn target healthy và mở kết nối HTTP riêng đến frontend pod `:8080`. Nginx nhận `/api/notes` và proxy đến `api.notes.svc.cluster.local:8080/notes`. API mở kết nối PostgreSQL TLS đến RDS `:5432`.

### Console: đối chiếu từng đoạn

1. Route 53 → Hosted zones → zone lab → record `notes`: điểm đến phải là ALB của lab.
2. EC2 → Load Balancers → `eks-did-notes` → Listeners: HTTP 80 redirect sang HTTPS 443; HTTPS forward đến target group frontend.
3. Target Groups → Targets: chọn IP target, xem port 8080 và health status.
4. EKS → Resources → Pods: so IP frontend với các target IP.

### CLI/API: gửi và theo dõi

```bash
source scripts/env.sh
curl -sS -o /dev/null -w '%{http_code}\n' "https://$APP_HOST/"
curl -fsS "https://$APP_HOST/api/healthz"
kubectl get pods -n notes -l app=frontend -o wide
kubectl logs -n notes -l app=frontend --tail=10
```

Mong đợi HTTP 200 và `workload: api` ở API health endpoint. Frontend access log có request tương ứng. Đó là hai phép kiểm tra khác nhau: trang chủ thành công chưa chứng minh API hay DB hoạt động.

```bash
curl -fsS "https://$APP_HOST/api/notes" \
  -H 'Content-Type: application/json' -d '{"body":"Hello from the request path"}'
curl -fsS "https://$APP_HOST/api/notes"
```

POST phải trả ID, GET phải có ghi chú. Không ghi chú thật hoặc dữ liệu nhạy cảm vì app chưa có user authentication.

### Giới hạn và bước tiếp theo

`X-Forwarded-For` mang IP client trong HTTP header; đây không nhất thiết là source IP mà NetworkPolicy thấy trên kết nối ALB → pod. Không dùng header để viết rule L3/L4. Các bài 2.2–2.6 sẽ giải thích mạng và target registration đằng sau đường đi này. Cấu hình có trong [render.py](/source/scripts/render.py).
''')
page(2,2,'vpc','VPC Architecture: Public & Private Subnets, Routing, NAT Gateway',r'''
## Public hay private được quyết định bởi route

Một subnet có route đến Internet Gateway không làm mọi EC2 trong đó tự public: tài nguyên vẫn cần địa chỉ public phù hợp và rule cho phép. Ngược lại, private subnet không tự ngăn kết nối nội bộ VPC.

| Nhóm | AZ A | AZ B | Default route |
|---|---|---|---|
| Public | 10.20.0.0/20 | 10.20.16.0/20 | Internet Gateway |
| Application | 10.20.32.0/20 | 10.20.48.0/20 | Một NAT Gateway ở AZ A |
| Database | 10.20.64.0/24 | 10.20.65.0/24 | Không có; chỉ local VPC |

### Console: tạo nền mạng

1. VPC → Your VPCs → Create VPC → **VPC only**, Name `eks-did`, IPv4 `10.20.0.0/16`. Bật DNS resolution và DNS hostnames trong VPC settings.
2. Subnets → Create subnet: tạo sáu subnet theo bảng, dùng hai AZ khả dụng. Đặt tên `eks-did-public-a/b`, `eks-did-private-a/b`, `eks-did-database-a/b`. Private/database không auto-assign public IP.
3. Internet Gateways → tạo `eks-did-igw`, attach vào VPC.
4. Route tables → tạo `eks-did-public`, thêm `0.0.0.0/0 → IGW`, associate đúng hai public subnets. Route local đã có sẵn.
5. NAT Gateways → tạo **public NAT**, public subnet AZ A, allocate Elastic IP. Đợi `Available`.
6. Tạo route table `eks-did-private`, thêm `0.0.0.0/0 → NAT`, associate hai application subnets.
7. Tạo route table `eks-did-database-isolated`, chỉ giữ route local, associate hai DB subnets.
8. Tag public subnets `kubernetes.io/role/elb=1`, application subnets `kubernetes.io/role/internal-elb=1`.

![Vị trí subnet và NAT trong AWS architecture](/images/aws-architecture.svg)

### CLI/API: xác minh association thay vì chỉ nhìn tên

```bash
VPC_ID=$(aws ec2 describe-vpcs --filters Name=tag:Name,Values=eks-did --query 'Vpcs[0].VpcId' --output text)
aws ec2 describe-subnets --filters "Name=vpc-id,Values=$VPC_ID" \
  --query 'Subnets[].{id:SubnetId,cidr:CidrBlock,az:AvailabilityZone,publicIP:MapPublicIpOnLaunch}'
aws ec2 describe-route-tables --filters "Name=vpc-id,Values=$VPC_ID" \
  --query 'RouteTables[].{id:RouteTableId,subnets:Associations[].SubnetId,routes:Routes}'
```

Khi tạo thủ công, AWS API tương ứng là `CreateVpc`, `CreateSubnet`, `CreateRouteTable`, `CreateRoute` và `AssociateRouteTable`. Ví dụ tạo public route sau khi export hai ID thực:

```bash
aws ec2 create-route --route-table-id "$PUBLIC_ROUTE_TABLE_ID" \
  --destination-cidr-block 0.0.0.0/0 --gateway-id "$INTERNET_GATEWAY_ID"
```

Chỉ chạy khi route chưa tồn tại. Terraform tương ứng nằm trong [main.tf](/source/terraform/main.tf) và [data-services.tf](/source/terraform/data-services.tf).

### Tradeoff

Một NAT tiết kiệm chi phí nhưng tạo phụ thuộc AZ và có thể phát sinh cross-AZ traffic. Production cần đánh giá NAT theo AZ hoặc VPC Endpoints. Endpoint cho ECR API/DKR vẫn còn dependency S3, EKS Auth, DNS và dịch vụ app; thêm một endpoint không chứng minh có thể bỏ NAT.
''')
page(2,3,'edge','Edge Security: AWS WAF, ALB và HTTPS',r'''
## Ba thành phần giải quyết ba việc

ALB định tuyến HTTP, ACM cung cấp certificate cho TLS và WAF kiểm tra request HTTP. WAF gắn vào ALB, không phải một máy proxy đặt trước ALB.

### Console: cấp chứng chỉ và tạo một rule kiểm chứng được

1. Route 53 → chọn public hosted zone bạn quản lý. Dùng hostname `notes.<zone>`; không tạo hosted zone mới rồi bỏ qua delegation.
2. ACM tại **us-east-1** → Request public certificate → nhập hostname → DNS validation. Chọn Create records in Route 53; đợi **Issued**. Certificate phải cùng Region với ALB.
3. WAF → Web ACLs → Create → Regional, tên `eks-did`. Default action Allow.
4. Thêm custom rule `workshop-header-test`, match **single header** `x-workshop-test`, exactly matches `block-me`, transformation None, action Block. Bật sampled requests/metrics.
5. Ingress ở 2.5 dùng ARN certificate và ARN Web ACL. Sau khi ALB xuất hiện, kiểm tra WAF resource association.

Rule header là bài test quyết định rõ ràng; nó không đại diện cho bộ rule production chống SQLi/XSS. Managed rules/rate limiting cần tuning và đánh giá false positives riêng.

### CLI/API: xác minh HTTPS và WAF

```bash
aws acm list-certificates --certificate-statuses ISSUED
curl -sS -o /dev/null -w '%{http_code}\n' "http://$APP_HOST/"
curl -sS -o /dev/null -w '%{http_code}\n' "https://$APP_HOST/"
curl -sS -o /dev/null -w '%{http_code}\n' -H 'x-workshop-test: block-me' "https://$APP_HOST/"
```

Mong đợi HTTP redirect, HTTPS 200, request có header 403. Không dùng `curl -k`: lệnh phải xác minh certificate và hostname.

Nếu dùng CLI thay Console để yêu cầu cert:

```bash
aws acm request-certificate --domain-name "$APP_HOST" --validation-method DNS
```

Sau đó đọc `describe-certificate`, tạo record validation và đợi `ISSUED`. Không yêu cầu lại cert nếu đã dùng Terraform. [Terraform WAF/ACM](/source/terraform/data-services.tf) chứa cấu hình đầy đủ.

### TLS kết thúc ở đâu?

Client → ALB được mã hóa; lab ALB → frontend và frontend → API dùng HTTP trong VPC. API/worker → RDS dùng TLS xác minh CA/hostname. Thiết kế này **không mã hóa end-to-end toàn bộ request path**. Nếu yêu cầu đó tồn tại, phải bổ sung backend HTTPS/mTLS và chứng minh lại.
''')
page(2,4,'security-groups','Network Access Control: Security Groups & NACLs',r'''
## SG stateful, NACL stateless

SG gắn vào ENI, tổng hợp allow rules và theo dõi connection. NACL gắn subnet, có allow/deny theo thứ tự và phải cho cả chiều trả về. Chúng không thay thế NetworkPolicy chọn pod theo label.

### Console: dựng và đọc các rule

1. VPC → Security groups → Create `eks-did-database` trong VPC lab. Inbound TCP 5432, **source là cluster/node SG thực tế**, không phải `0.0.0.0/0`. Gắn SG này vào RDS.
2. EKS → Networking → cluster security group. EC2 → node → Network interface kiểm tra SG thực sự gắn vào node/ENI. Lab launch template không đặt SG thay thế, nên managed nodes dùng cluster SG.
3. Sau khi tạo Ingress, xem SG do controller tạo cho ALB và rule cho backend. Listener chỉ mở 80/443; backend cần 8080 từ SG của load-balancing path, không public 8080.
4. VPC → Network ACLs → xem association và rule numbers. Lab giữ default NACL để tập trung SG/NetworkPolicy; không tự siết ephemeral ports khi chưa có traffic matrix.

### CLI/API: xem bằng chứng

```bash
aws ec2 describe-security-group-rules \
  --filters "Name=group-id,Values=$NODE_SG" \
  --query 'SecurityGroupRules[].{egress:IsEgress,port:FromPort,to:ToPort,source:ReferencedGroupInfo.GroupId,cidr:CidrIpv4}'
aws ec2 describe-network-acls --filters "Name=vpc-id,Values=$VPC_ID" \
  --query 'NetworkAcls[].{id:NetworkAclId,associations:Associations[].SubnetId,rules:Entries}'
```

Nếu tạo database SG bằng API, `AuthorizeSecurityGroupIngress` dùng referenced group:

```bash
aws ec2 authorize-security-group-ingress --group-id "$DB_SG_ID" \
  --ip-permissions "IpProtocol=tcp,FromPort=5432,ToPort=5432,UserIdGroupPairs=[{GroupId=$NODE_SG}]"
```

Không thêm lại rule đã tồn tại. Terraform dùng `aws_vpc_security_group_ingress_rule.database`.

### Giới hạn phải hiểu

Tất cả pod dùng node SG có thể đi qua lớp SG đến RDS nếu không có kiểm soát bổ sung. **SG này không chỉ cho phép API/worker.** Module 3 dùng NetworkPolicy chặn frontend → RDS, còn PostgreSQL grants và IAM DB auth giới hạn quyền sử dụng DB. Security Groups for Pods là lựa chọn nâng cao khi cần SG theo workload, không được bật trong lab này.
''')
page(2,5,'controller-ingress','AWS Load Balancer Controller và Kubernetes Ingress',r'''
## Ingress là cấu hình, controller là bộ điều khiển

Ingress mô tả host/path/backend. AWS Load Balancer Controller theo dõi Ingress, Service và EndpointSlice rồi gọi ELB/EC2 APIs tạo ALB, listener, target group và rule SG. Controller không proxy từng HTTP request của ứng dụng.

### Console trước: kiểm tra quyền controller

IAM → Roles → `eks-did-controller`: trust principal `pods.eks.amazonaws.com`, actions `sts:AssumeRole` và `sts:TagSession`. EKS → Access → Pod Identity associations: namespace `kube-system`, ServiceAccount `aws-load-balancer-controller`, role trên. Policy lấy từ release controller, không dùng `AdministratorAccess`.

AWS Console không cung cấp trình soạn đầy đủ mọi Kubernetes resource. Vì vậy cài Helm chart và tạo Ingress bằng CLI là bước cần thiết.

### CLI: cài controller và triển khai Ingress

Script [deploy.sh](/source/scripts/deploy.sh) pin chart `3.6.2`, truyền region và VPC ID để controller không cần lấy thông tin qua IMDS:

```bash
source scripts/env.sh
bash scripts/deploy.sh
kubectl -n kube-system rollout status deployment/aws-load-balancer-controller
kubectl -n notes get ingress notes -o yaml
```

Các annotation chính trong [render.py](/source/scripts/render.py):

```yaml
alb.ingress.kubernetes.io/scheme: internet-facing
alb.ingress.kubernetes.io/target-type: ip
alb.ingress.kubernetes.io/healthcheck-path: /healthz
alb.ingress.kubernetes.io/listen-ports: '[{"HTTP":80},{"HTTPS":443}]'
alb.ingress.kubernetes.io/ssl-redirect: '443'
```

Certificate ARN, public subnet IDs và WAF ARN được render từ cấu hình account, không hardcode ví dụ của người khác.

```bash
kubectl get ingress -n notes --watch
# Khi ADDRESS có hostname ALB, dừng watch bằng Ctrl-C.
python3 scripts/publish-dns.py
```

### Kiểm chứng và gotchas

EC2 Console phải thấy ALB và target group do controller quản lý; `curl https://$APP_HOST/` phải thành công sau khi DNS cập nhật. Nếu chưa có ALB, xem controller logs và events trước khi kiểm tra app. Không sửa ALB thủ công để “fix” cấu hình mà controller sẽ reconcile lại.

Quyền sửa Ingress cũng có thể thay đổi tài nguyên AWS. Lab không dùng shared IngressGroup; chỉ admin lab được tạo/sửa Ingress. IAM policy phiên bản được lưu tại [controller-policy.json](/source/terraform/controller-policy.json).
''')
page(2,6,'target-types','ALB Target Types: Instance vs IP',r'''
## Hai cách đều hợp lệ, nhưng data path khác nhau

| | Instance target | IP target — đường chính của lab |
|---|---|---|
| Target đăng ký | EC2 instance ID | Pod IP |
| Cổng nhận | NodePort | Container/target port 8080 |
| Data path | ALB → node → Service routing → pod | ALB → pod IP |
| Khi phù hợp | Thiết kế node targets/NodePort; pod network không trực tiếp routable từ ALB | VPC CNI và pod IP được ALB định tuyến tới; Fargate cũng yêu cầu IP targets |
| Cần quan sát | NodePort, kube-proxy/routing, node SG | EndpointSlice, pod readiness, target health, pod IP |

Lab chọn `ip` vì private pod IP của VPC CNI đã routable trong VPC, tránh bước NodePort không cần thiết. Đây là lựa chọn phù hợp kiến trúc hiện tại, không phải khẳng định instance mode luôn sai.

### Console: đối chiếu target với pod

EC2 → Target Groups → chọn target group của `eks-did-notes`. Target type phải `IP`, port 8080. EKS → Pods → frontend phải có các IP trùng với targets. Trong rollout có thể thấy IP cũ đang draining và IP mới đang đăng ký.

### CLI/API: kiểm tra cơ chế

```bash
kubectl get pods -n notes -l app=frontend -o wide
kubectl get endpointslices -n notes -l kubernetes.io/service-name=frontend -o yaml
aws elbv2 describe-target-groups \
  --query 'TargetGroups[?starts_with(TargetGroupName, `k8s-notes`)].{arn:TargetGroupArn,type:TargetType,port:Port}'
# Export TARGET_GROUP_ARN từ kết quả trên.
aws elbv2 describe-target-health --target-group-arn "$TARGET_GROUP_ARN"
```

Mong đợi registered IPs là frontend pod IPs và health `healthy`. Service vẫn để controller tìm backend, nhưng ALB không phải gửi request qua Service ClusterIP. Ngược lại, Nginx → API **có dùng** Service DNS/ClusterIP.

### Thử rollout có kiểm soát

```bash
kubectl rollout restart deployment/frontend -n notes
kubectl rollout status deployment/frontend -n notes
curl -fsS "https://$APP_HOST/" -o /dev/null
```

Controller phải cập nhật targets theo pods mới. Không dùng một lần curl thành công làm bằng chứng “zero downtime”: kiểm chứng availability khi rollout cần liên tục đo traffic, readiness và target registration. Module kế tiếp đi vào các kết nối bên trong cluster.
''')
page(3,1,'networking','Kubernetes Networking: Pod, Service và Namespace',r'''
## Pod IP thay đổi; tên Service giúp client tìm đúng backend

Pod là đơn vị chạy container, thường có IP riêng. Deployment có thể thay pod khi rollout, nên không hardcode pod IP trong Nginx. Service chọn pods bằng label; EndpointSlice thể hiện danh sách endpoints. Namespace nhóm resources và là phạm vi của nhiều policy, nhưng không tự tạo network isolation.

### Console: đọc ứng dụng

EKS → cluster → Resources → Workloads → Deployments: frontend và API có hai replicas, worker có một. Trong Service and networking, hai Service `frontend`/`api` đều là ClusterIP. Worker không cần Service vì chỉ chủ động long-poll SQS.

### CLI: xem mối liên hệ giữa objects

```bash
kubectl get pods -n notes -o wide --show-labels
kubectl get services -n notes
kubectl get endpointslices -n notes -l kubernetes.io/service-name=api
kubectl get deployment frontend -n notes -o yaml
```

Kiểm tra selector Service `app: api` trùng pod labels. Service port/targetPort lab đều 8080, tránh thêm một lần đổi port khi học traffic flow. Với VPC CNI policy engine cần đối chiếu các giới hạn port/protocol trong tài liệu phiên bản sử dụng.

```bash
kubectl exec -n notes deployment/frontend -- \
  wget -qO- http://api.notes.svc.cluster.local:8080/healthz
```

Mong đợi JSON health API. DNS name chọn Service, Service routing chọn endpoint healthy. Đối với ALB IP targets, Service vẫn là backend reference cho controller nhưng không phải hop trên traffic ALB → frontend.

![Giao diện ứng dụng chạy thật trên ALB HTTPS](/images/application-live.png "Ghi chú được lưu qua API vào RDS; báo cáo do worker xử lý qua SQS.")

### Điều gì namespace chưa làm?

Trước khi áp dụng policy, pod ở namespace khác vẫn có thể kết nối API nếu routing/security rules cho phép. Module 3.2 sẽ kiểm chứng điều đó rồi thu hẹp. Người có quyền tạo pod tùy ý có thể gắn label giống workload tin cậy, nên NetworkPolicy phải đi cùng RBAC; label không phải danh tính bất khả giả mạo.

Manifest đầy đủ được tạo bởi [render.py](/source/scripts/render.py); cấu hình Nginx và ứng dụng có trong nguồn tải về.
''')
page(3,2,'networkpolicy','Network Segmentation với Kubernetes NetworkPolicy',r'''
## Bắt đầu từ traffic matrix

![Các kết nối được phép và bị chặn](/images/network-policy.svg)

| Source | Destination | Port | Quyết định |
|---|---|---|---|
| ALB subnets | Frontend | TCP 8080 | Allow, phối hợp SG |
| Frontend | API cùng namespace | TCP 8080 | Allow |
| API/worker | Database subnets | TCP 5432 | Allow, vẫn cần SG/IAM DB/SQL grants |
| Workloads | CoreDNS | TCP/UDP 53 | Allow |
| API/worker/db-init | Pod Identity Agent | TCP 80 | Allow 169.254.170.23/32 |
| API/worker/db-init | Public AWS endpoints | TCP 443 | Allow outbound; IAM giới hạn API/resource |
| Frontend | Database/Internet | — | Deny |
| Pod không liên quan | API | — | Deny |

### Console trước

EKS Console giúp xem pod labels, IP và NetworkPolicy nếu resource browser hỗ trợ phiên bản đó. Policy creation/enforcement cần YAML và `kubectl`; không có nút AWS Security Group nào thay được pod selectors.

### CLI: xác nhận engine rồi áp dụng

Làm 3.3 trước khi bật default deny. Khi baseline ứng dụng đã hoạt động:

```bash
kubectl get networkpolicy -n notes
kubectl apply -f k8s/network-policies.yaml
kubectl describe networkpolicy frontend -n notes
kubectl describe networkpolicy api -n notes
```

Default deny chọn mọi pod, cô lập ingress và egress. Các allow policies **cộng dồn**; một default-deny object không ghi đè policy allow quá rộng khác. Policy đích cho API cần frontend `podSelector`; nếu tách namespace phải kết hợp `namespaceSelector` trong cùng peer để có điều kiện AND.

```yaml
from:
  - podSelector:
      matchLabels:
        app: frontend
ports:
  - protocol: TCP
    port: 8080
```

Đây là một phần rule, không phải manifest hoàn chỉnh. [render.py](/source/scripts/render.py) sinh toàn bộ policy từ CIDR thực, không pin IP RDS có thể thay khi failover.

### Kiểm chứng

```bash
python3 scripts/verify.py
```

Bộ kiểm tra dùng IP Service cho negative connectivity để phân biệt lỗi DNS với kết nối bị chặn. Frontend phải gọi API được; untrusted pod gọi API và frontend gọi RDS phải timeout. Positive API → RDS phải thành công để chứng minh DB đang sẵn sàng.

### Giới hạn

Egress HTTPS public hiện cho phép nhiều endpoint hơn SQS. Standard NetworkPolicy không có native FQDN/HTTP authorization; dùng IAM giới hạn một queue, thêm VPC Endpoint policies hoặc giải pháp egress phù hợp nếu cần siết theo dịch vụ. Không tuyên bố policy đã chặn mọi data exfiltration.
''')
page(3,3,'vpc-cni','NetworkPolicy Enforcement với Amazon VPC CNI',r'''
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
''')
page(3,4,'pod-security','Pod Security Standards & Pod Security Admission',r'''
## Chặn cấu hình đặc quyền trước khi pod chạy

Pod Security Standards có ba mức Privileged, Baseline và Restricted. Pod Security Admission (PSA) thực thi theo namespace labels. Nó không scan lỗ hổng trong image hoặc kiểm tra HTTP request.

### Console trước

EKS → Resources → Namespaces → `notes`: quan sát labels. AWS Console có thể không hỗ trợ chỉnh tất cả labels; dùng Kubernetes API cho thay đổi sau.

### CLI: pin version policy theo cluster

```bash
kubectl label namespace notes \
  pod-security.kubernetes.io/enforce=restricted \
  pod-security.kubernetes.io/enforce-version=v1.35 \
  pod-security.kubernetes.io/audit=restricted \
  pod-security.kubernetes.io/warn=restricted --overwrite
```

Pin version giúp việc upgrade chuẩn Restricted được review thay vì đổi ngầm. Không áp dụng Restricted lên `kube-system` tùy tiện: CNI và một số add-on cần quyền hệ thống.

### Negative test an toàn, không tạo privileged pod thật

```bash
kubectl run psa-negative -n notes --image=nginx:1.28-alpine \
  --dry-run=server -o yaml
```

Pod mặc định thiếu cấu hình Restricted nên admission phải từ chối, giải thích `runAsNonRoot`, seccomp/capabilities. `--dry-run=server` chạy admission nhưng không lưu pod. Test không bypass admission hoặc chạy host mount.

### Positive test

```bash
kubectl get pods -n notes
kubectl get deployment api -n notes -o jsonpath='{.spec.template.spec.securityContext}'
```

Workloads hợp lệ vẫn Running/Ready sau rollout. Label PSA không đuổi mọi pod đang chạy; cần review/redeploy workload để chứng minh pod template đáp ứng chuẩn.

Trong manifest lab, `securityContext` do `render.py` tạo, tách pod-level và container-level settings. Bài tiếp theo giải thích ý nghĩa của từng trường thay vì chỉ copy YAML.
''')
page(3,5,'securitycontext','Container Hardening với SecurityContext',r'''
## Giảm đặc quyền mà vẫn giữ app hoạt động

Nếu ứng dụng bị thực thi code ngoài ý muốn, container không nên tự có quyền root hoặc ghi tùy ý vào root filesystem. Lab dùng cấu hình:

```yaml
securityContext:
  runAsNonRoot: true
  runAsUser: 10001
  runAsGroup: 10001
  seccompProfile:
    type: RuntimeDefault
containers:
  - name: api
    # image và các trường còn lại xem manifest đầy đủ
    securityContext:
      allowPrivilegeEscalation: false
      readOnlyRootFilesystem: true
      capabilities:
        drop: ["ALL"]
```

`runAsNonRoot` yêu cầu UID không phải root. `allowPrivilegeEscalation: false` hạn chế tăng quyền qua cơ chế như setuid; không phải sandbox tuyệt đối. `RuntimeDefault` áp dụng seccomp runtime. Bỏ capabilities giảm quyền Linux không cần thiết.

### Console và CLI: kiểm tra runtime thực tế

EKS Console → Pod API → xem cấu hình. Sau đó:

```bash
kubectl exec -n notes deployment/api -- id
kubectl exec -n notes deployment/api -- python -c \
  'from pathlib import Path; Path("/app/should-not-write").write_text("test")'
```

Mong đợi UID 10001 và lần ghi bị từ chối (`Read-only file system` hoặc permission error). Sau đó API health vẫn 200:

```bash
curl -fsS "https://$APP_HOST/api/healthz"
```

### Ứng dụng cần ghi file ở đâu?

Nginx cần PID/temp directories. Lab dùng image unprivileged, listen 8080 và mount `emptyDir` có giới hạn tại `/tmp`; cấu hình đưa PID/cache paths đến đó. Không mở writable toàn root filesystem chỉ để hết lỗi.

Python tắt bytecode writes và đọc CA bundle đã có trong image. Resource requests/limits giới hạn ngân sách CPU/RAM, nhưng không phải cơ chế chống mọi kiểu DoS.

Nguồn: [Dockerfile](/source/app/Dockerfile), [render.py](/source/scripts/render.py). Non-root/Restricted không thay thế cập nhật dependencies hoặc application authorization.
''')
page(3,6,'node-imds','Worker Node Security và IMDSv2',r'''
## Không để pod vô tình mang quyền của node

Node role cần pull image và thực hiện chức năng EKS. Quyền SQS/RDS của ứng dụng không nên gắn lên role này. Nếu pod lấy được node credentials qua EC2 IMDS, việc cấp role riêng theo workload có thể bị suy yếu.

### Console: cấu hình trước khi tạo node

1. EC2 → Launch templates → template node lab → Advanced details → Metadata options.
2. Metadata accessible: enabled; **IMDSv2 required**, response hop limit **1**.
3. Không mở SSH từ Internet, EBS encrypted. CNI role riêng cho `aws-node`, không bắt CNI pod phụ thuộc metadata hop 1.
4. EKS node group dùng đúng template version. Sửa launch template không tự cập nhật mọi node cũ; rollout node group có kiểm soát.

### CLI/API: kiểm tra instance thay vì chỉ nhìn template

```bash
aws ec2 describe-instances \
  --filters Name=tag:eks:cluster-name,Values=eks-did Name=instance-state-name,Values=running \
  --query 'Reservations[].Instances[].{id:InstanceId,publicIP:PublicIpAddress,metadata:MetadataOptions,profile:IamInstanceProfile.Arn}'
```

Mong đợi nodes không có public IP, `HttpTokens=required`, `HttpPutResponseHopLimit=1`. Terraform dùng `aws_launch_template.nodes`.

### Negative test từ pod thường

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
''')
page(4,1,'authentication-authorization','Authentication vs Authorization',r'''
## Đăng nhập thành công chưa có nghĩa được làm mọi việc

Authentication xác định chủ thể; authorization quyết định chủ thể được phép làm hành động nào với resource nào. Hai câu hỏi xuất hiện ở cả Kubernetes, AWS API và database, nhưng do các hệ thống khác nhau trả lời.

| Hành động | Xác thực | Phân quyền |
|---|---|---|
| Người vận hành chạy `kubectl get pods` | EKS IAM authentication | EKS access policy / Kubernetes RBAC |
| API gửi SQS message | AWS temporary credentials | IAM và queue resource policy |
| API ghi vào RDS | IAM DB token | `rds-db:connect` và PostgreSQL grants |
| Người dùng đọc ghi chú | Chưa có trong app demo | Chưa có; không dùng app cho dữ liệu nhạy cảm |

### Console và CLI: quan sát hai identity

Console → IAM → role API; EKS → Access → observer access entry. Đây là hai quyền riêng.

```bash
aws sts get-caller-identity
kubectl auth can-i list pods -n notes
kubectl auth can-i get secrets -n notes
```

Với admin hiện tại, câu trả lời có thể đều `yes`; điều đó không chứng minh observer được hạn chế. Bài 4.4 sẽ dùng credentials của observer thật để thử lại.

### Khi nào bị từ chối ở đâu?

Network timeout không phải `AccessDenied`. Kubernetes trả `Forbidden` khi đã nhận request nhưng principal không có permission cần thiết. AWS trả authorization error khi request được xử lý nhưng thiếu quyền hoặc có explicit deny. PostgreSQL có thể chấp nhận kết nối nhưng từ chối một câu SQL.

Terraform tạo role và access entry; YAML Role/RoleBinding quy định Kubernetes verbs. Không dùng NetworkPolicy để giải quyết lỗi `sqs:SendMessage AccessDenied`, cũng không thêm IAM policy để chữa một connection timeout. Việc phân biệt này giúp người đọc biết bước tiếp theo phải kiểm tra lớp nào.
''')
page(4,2,'endpoint','EKS API Endpoint Security',r'''
## Đường quản trị không qua ALB

![Đường quản trị EKS](/images/human-access.svg)

ALB public phục vụ website. EKS API endpoint phục vụ Kubernetes API. Một người có thể mở website nhưng không kết nối được endpoint quản trị; một người đến được endpoint vẫn phải qua authentication/authorization.

### Console: giới hạn nguồn quản trị

EKS → cluster → Networking → Manage endpoint access. Lab chọn Public and private, public CIDRs = IP workstation `/32`. Nodes/controller dùng private endpoint trong VPC. Không mở `0.0.0.0/0` để xử lý lỗi từ workstation.

Thiết kế production có VPN/private connectivity có thể dùng private-only. Đánh đổi: người học từ Internet cần một đường quản trị vào VPC, không thể chỉ chạy kubectl từ bất kỳ đâu.

### CLI/API: kiểm tra rồi mới thay

```bash
aws eks describe-cluster --name eks-did \
  --query 'cluster.resourcesVpcConfig.{public:endpointPublicAccess,private:endpointPrivateAccess,cidrs:publicAccessCidrs}'
curl -fsS https://checkip.amazonaws.com
```

Nếu IP workstation đổi, cập nhật **đúng IP mới**:

```bash
ADMIN_IP=$(curl -fsS https://checkip.amazonaws.com)
aws eks update-cluster-config --name eks-did \
  --resources-vpc-config "endpointPublicAccess=true,endpointPrivateAccess=true,publicAccessCidrs=$ADMIN_IP/32"
```

Chỉ dùng API nếu đó là đường quản lý bạn chọn. Với Terraform, sửa `admin_cidr`, plan rồi apply để tránh drift. Giữ kết nối quản trị đang hoạt động và đợi update hoàn tất trước khi thử context mới.

### Kiểm chứng

`kubectl get nodes` từ workstation được cho phép phải thành công. Đọc public CIDR từ API để xác nhận không có mạng rộng ngoài dự kiến. Workshop không dùng một timeout từ mạng chưa biết để tuyên bố đã kiểm chứng private-only; giới hạn test được ghi trong validation.
''')
page(4,3,'human-access','Human Access: AWS IAM & EKS Access Entries',r'''
## Từ IAM role đến Kubernetes group

Lab dùng role `eks-did-observer`, access entry map vào group `notes-observers`. Group được bind vào Role chỉ đọc của namespace `notes`. Không associate thêm policy admin cho role này.

### Console: tạo đúng đường cấp quyền

1. IAM → Roles → Create role → Custom trust policy. Cho phép **IAM principal quản trị lab của bạn** `sts:AssumeRole`; không dùng wildcard principal hoặc hardcode principal của account ví dụ.
2. Đặt `eks-did-observer`. Identity policy chỉ cần `eks:DescribeCluster` cho ARN cluster `eks-did` để lấy endpoint/config. Kubernetes verbs không nằm trong policy này.
3. EKS → cluster → Access → Create access entry: chọn role ARN, type Standard, Kubernetes group `notes-observers`.
4. Không associate `AmazonEKSClusterAdminPolicy`. Bài tiếp theo tạo RoleBinding.

### CLI/API tương đương

```bash
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
OBSERVER_ARN="arn:aws:iam::$ACCOUNT_ID:role/eks-did-observer"
aws eks list-access-entries --cluster-name eks-did
aws eks describe-access-entry --cluster-name eks-did --principal-arn "$OBSERVER_ARN"
aws eks list-associated-access-policies --cluster-name eks-did --principal-arn "$OBSERVER_ARN"
```

Nếu tạo bằng API thay Console, sau khi role tồn tại:

```bash
aws eks create-access-entry --cluster-name eks-did \
  --principal-arn "$OBSERVER_ARN" --type STANDARD --kubernetes-groups notes-observers
```

Không tạo trùng entry đã có. Terraform chứa `aws_iam_role.observer`, `aws_eks_access_entry.observer` tại [data-services.tf](/source/terraform/data-services.tf).

### Gotcha: permissions có thể cộng thêm

EKS access policies và RBAC có thể cùng cấp quyền. RoleBinding read-only không thu hồi quyền admin từ một access policy khác. Kiểm tra cả hai trước khi kết luận observer bị hạn chế. Không xóa bootstrap/admin hiện tại trước khi identity thay thế đã đăng nhập và thực hiện đủ quyền quản trị cần thiết.
''')
page(4,4,'rbac','Kubernetes RBAC: Role, ClusterRole và Bindings',r'''
## Role định nghĩa quyền; Binding gắn quyền với chủ thể

Role có phạm vi namespace. ClusterRole có thể dùng cho cluster-scoped resources hoặc tái sử dụng qua RoleBinding. RoleBinding cấp quyền trong namespace; ClusterRoleBinding có phạm vi toàn cluster. Các quyền được cộng dồn, không có deny Role để hủy allow khác.

### Console trước

EKS → Access xác nhận observer group và không có admin policy. Kubernetes Resources có thể hiển thị roles/bindings tùy quyền của người xem. Tạo Role bằng manifest:

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: observer
  namespace: notes
rules:
  - apiGroups: [""]
    resources: ["pods", "services"]
    verbs: ["get", "list", "watch"]
  - apiGroups: ["apps"]
    resources: ["deployments"]
    verbs: ["get", "list", "watch"]
```

RoleBinding của lab gắn Role này với group `notes-observers`, xem manifest tạo bởi [render.py](/source/scripts/render.py).

### CLI: thử bằng credentials thật

```bash
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
aws eks update-kubeconfig --name eks-did \
  --role-arn "arn:aws:iam::$ACCOUNT_ID:role/eks-did-observer" \
  --kubeconfig .local/observer-kubeconfig --alias observer
kubectl --kubeconfig .local/observer-kubeconfig get pods -n notes
kubectl --kubeconfig .local/observer-kubeconfig auth can-i patch deployments -n notes
kubectl --kubeconfig .local/observer-kubeconfig get secrets -n notes
```

Mong đợi: list pods thành công, patch `no`, đọc Secret `Forbidden`. Dùng server-side dry run để thử sửa Deployment mà không thay đổi workload thật:

```bash
kubectl --kubeconfig .local/observer-kubeconfig patch deployment api -n notes \
  --type merge -p '{"spec":{"replicas":1}}' --dry-run=server
```

Phải bị từ chối. `--as` là impersonation test, không thay thế việc chứng minh IAM role đăng nhập được; bộ kiểm tra dùng observer credentials thật.

### Quyền “chỉ deploy app” vẫn cần review

`pods/exec`, đọc Secret, tạo pod với ServiceAccount khác, sửa Ingress hoặc RoleBinding có thể mang lại quyền gián tiếp đáng kể. Lab observer không có các quyền đó. Không cấp wildcard verbs/resources vì tiện demo.
''')
page(4,5,'workload-identity','Workload Identity: IRSA vs EKS Pod Identity',r'''
## Mỗi chức năng một role, không nhúng access key

![Cấp temporary credentials theo workload](/images/workload-identity.svg)

| | IRSA | EKS Pod Identity — app của lab |
|---|---|---|
| Liên kết | OIDC trust + ServiceAccount annotation | EKS association namespace/ServiceAccount/role |
| Cấp credentials | STS AssumeRoleWithWebIdentity | Agent + EKS Auth + SDK credential provider |
| Khi chọn | Cấu hình hiện có, môi trường/compute cần IRSA | EKS compute được hỗ trợ, muốn quản lý association qua EKS |
| Dependency | OIDC provider, STS, SDK | Agent, EKS Auth, SDK tương thích |

Lab dùng Pod Identity cho API, worker, db-init và controller. VPC CNI dùng IRSA riêng để bootstrap mạng không phụ thuộc node IMDS. Không gán đồng thời hai cơ chế cho cùng một workload rồi đoán SDK dùng cái nào.

### Console: tạo trust và association

1. EKS → Add-ons: Pod Identity Agent `ACTIVE` trên managed nodes.
2. IAM → tạo các role `eks-did-api`, `eks-did-worker`, `eks-did-db-init`, `eks-did-controller`.
3. Trust service principal `pods.eks.amazonaws.com`, actions `sts:AssumeRole`, `sts:TagSession`. Dùng điều kiện session tags giới hạn namespace/ServiceAccount như [data-services.tf](/source/terraform/data-services.tf).
4. EKS → Access → Pod Identity associations: namespace `notes`, ServiceAccount tương ứng `api`, `worker`, `db-init`; controller là `kube-system/aws-load-balancer-controller`.
5. Gắn identity policies theo 4.6. Association có thể tạo trước ServiceAccount nhưng workload chỉ chạy đúng khi cả hai có mặt.

### CLI/API: tạo và đọc association

```bash
aws eks list-pod-identity-associations --cluster-name eks-did
kubectl get daemonset eks-pod-identity-agent -n kube-system
```

Ví dụ API tạo association **nếu chưa tồn tại**:

```bash
aws eks create-pod-identity-association --cluster-name eks-did \
  --namespace notes --service-account api --role-arn "$API_ROLE_ARN"
```

Terraform tự quản lý `aws_eks_pod_identity_association.workload`. Sau khi đổi association, rollout pod để credentials injection/caches phản ánh đúng cấu hình.

### Kiểm chứng identity trong pod

```bash
kubectl exec -n notes deployment/api -- python -c \
  'import boto3; print(boto3.client("sts").get_caller_identity()["Arn"])'
```

ARN phải là assumed role `eks-did-api`, không phải node role. Egress phải cho agent `169.254.170.23:80` và AWS APIs cần thiết. `automountServiceAccountToken: false` tắt token Kubernetes API mặc định; Pod Identity vẫn có projected token riêng do EKS cấp, không mâu thuẫn với cấu hình đó.
''')
page(4,6,'least-privilege','Least Privilege và IAM Policies',r'''
## Giới hạn theo action, resource và chủ thể

| Identity | Quyền AWS | Quyền SQL |
|---|---|---|
| Frontend | Không có role ứng dụng | Không có user DB |
| API | `sqs:SendMessage` trên queue lab; `rds-db:connect` cho `notes_api` | Insert/select notes, select reports |
| Worker | Receive/Delete/GetQueueAttributes trên queue lab; connect `notes_worker` | Select notes, insert/select reports |
| db-init | GetSecretValue đúng RDS master secret | Bootstrap schema/users; job kết thúc sau khởi tạo |
| Controller | Policy ELB controller release đã pin | Không có |

### Console: tạo policies có phạm vi

IAM → role API → Add permissions → Inline policy → JSON. Ví dụ queue policy cho role API:

```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Action": "sqs:SendMessage",
    "Resource": "arn:aws:sqs:us-east-1:YOUR_ACCOUNT_ID:eks-did-reports"
  }]
}
```

Thay account thật; thêm statement `rds-db:connect` với ARN dạng `arn:aws:rds-db:REGION:ACCOUNT:dbuser:DB_RESOURCE_ID/notes_api`. Đây là **DB resource ID**, không phải DB identifier hoặc ARN instance thông thường. Worker dùng username riêng. Toàn bộ statements có trong [Terraform](/source/terraform/data-services.tf).

```bash
aws rds describe-db-instances --db-instance-identifier eks-did \
  --query 'DBInstances[0].{resourceID:DbiResourceId,secret:MasterUserSecret.SecretArn}'
```

### CLI: positive và negative tests

```bash
curl -fsS "https://$APP_HOST/api/reports" -X POST
kubectl logs -n notes deployment/worker --tail=10
curl -fsS "https://$APP_HOST/api/reports"
```

API trả task ID; worker ghi report; GET trả cùng ID. Đây là bài test xuyên SQS/IAM/DB.

```bash
kubectl exec -n notes deployment/api -- python -c '
import boto3,os
from botocore.exceptions import ClientError
try:
    boto3.client("sqs").receive_message(QueueUrl=os.environ["QUEUE_URL"],WaitTimeSeconds=0)
    raise SystemExit("UNEXPECTED: API can receive messages")
except ClientError as e:
    print(e.response["Error"]["Code"])
    assert "AccessDenied" in e.response["Error"]["Code"]'
```

Phải bị AccessDenied. Kiểm tra SQL riêng: API không được insert `notes.reports`; IAM connect không tự cấp quyền SQL. Db-init dùng master secret chỉ cho bootstrap; sau khi hoàn tất, pod job có thể xóa, và không cấp quyền đọc secret cho API/worker.
''')
page(5,1,'scanning','Container Image Scanning với ECR & Inspector',r'''
## Tìm lỗ hổng trước khi quyết định release

Image scanning tìm các package/dependency có vulnerability đã biết. Kết quả cần được đánh giá theo mức độ, khả năng khai thác, bản sửa và exception có thời hạn. Scan không tự ngăn Kubernetes chạy image.

### Console: basic và enhanced scanning

1. ECR → Private registry → Features & Settings → Scanning: xem loại scanning đang dùng. Basic scan tập trung OS packages; enhanced scanning tích hợp Inspector, có thể theo dõi cả language packages theo khả năng hỗ trợ.
2. Inspector → Activate → ECR scanning, nếu sandbox cho phép. Đây là cấu hình account/Region; review phạm vi trước khi đổi trong account dùng chung.
3. Chọn repository `eks-did/notes`, xem digest đã push và scan findings. Chờ scan hoàn tất; “không thấy findings” trong lúc pending không phải kết quả sạch.
4. Mở một finding, xem affected package, installed/fixed version và severity. Không đưa finding vào bài như bằng chứng exploit đã xảy ra.

### CLI/API: build rồi đọc findings

```bash
bash scripts/build-push.sh
IMAGE=$(cat .local/image.txt)
aws ecr describe-images --repository-name eks-did/notes \
  --query 'imageDetails[].{digest:imageDigest,tags:imageTags,scan:imageScanStatus.status}'
```

Enhanced scanning dùng Inspector APIs:

```bash
aws inspector2 batch-get-account-status \
  --account-ids "$(aws sts get-caller-identity --query Account --output text)"
aws inspector2 list-findings --filter-criteria \
  '{"ecrImageRepositoryName":[{"comparison":"EQUALS","value":"eks-did/notes"}],"findingStatus":[{"comparison":"EQUALS","value":"ACTIVE"}]}' \
  --query 'findings[].{severity:severity,title:title}'
```

Basic scan APIs và Inspector có lifecycle/status khác nhau; không gọi `start-image-scan` như thể nó điều khiển enhanced scanning.

### Release gate có hành vi thật

```bash
python3 scripts/scan-gate.py
```

Script yêu cầu coverage đã scan, đọc findings của **đúng deployed digest**, trả exit 1 nếu có HIGH/CRITICAL hoặc chưa có coverage hoàn tất. [Kết quả scan thực tế](/evidence/image-scan.json) trong lượt lab ghi 4 HIGH, 8 MEDIUM, 2 LOW, 2 UNTRIAGED; 4 HIGH chưa có bản sửa theo Inspector. Gate trả `BLOCK`, không tự miễn trừ vì chưa có fix. App vẫn được dùng trong sandbox để kiểm tra network/identity; kết quả đó không phải phê duyệt release production.

Khi có bản vá, cập nhật base/dependency, build digest mới, scan lại rồi mới review gate. Đừng trộn kết quả scan image unsigned với image đang chạy.

### Terraform và gate

`aws_ecr_repository.app` bật immutable tags/basic scan; optional `aws_inspector2_enabler.ecr` bật ECR Inspector. Account có registry filters cần review để chắc repository lab nằm trong coverage. Tạo image mới với tag mới thay vì overwrite tag immutable.

Workshop ghi kết quả scan thực tế; không hứa “zero CVE”. Nếu muốn gate theo severity, thêm bước CI đọc findings rồi cho phép/từ chối release theo policy. Không gọi scan thành công là deploy bị chặn tự động.
''')
page(5,2,'sbom-signing','SBOM, Image Signing & Admission Policies',r'''
## Ba bằng chứng khác nhau

![Chuỗi source, build, ký và admission](/images/supply-chain.svg)

SBOM liệt kê thành phần. Signature chứng minh artifact digest đã được signer tin cậy ký. Admission policy quyết định workload có được tạo. Signature không bảo đảm image không có lỗ hổng; SBOM không thay vulnerability scan.

### Console trước

ECR → repository → Images: ghi lại image digest thay vì chỉ tag. IAM/ECR permissions xác định ai có quyền push. Cấu hình signature verification là Kubernetes admission, nên phần tiếp theo cần CLI.

### CLI: sinh SBOM, ký và xác minh

```bash
source scripts/env.sh
bash scripts/supply-chain.sh
```

Script dùng image digest trong `.local/image.txt`, sinh `.local/sbom.cdx.json` bằng Trivy và ký bằng Cosign. Public key được lưu `k8s/cosign.pub`; private key chỉ ở `.local/` bị gitignore. Lab dùng key tạm với password rỗng để demo; production dùng signer được bảo vệ và policy quản lý key/rotation riêng.

Lab không upload signature vào public transparency log; `--tlog-upload=false` khi ký và `--insecure-ignore-tlog` khi xác minh chỉ bỏ yêu cầu transparency log, **không bỏ kiểm tra signature bằng public key**.

```bash
IMAGE=$(cat .local/image.txt)
cosign verify --insecure-ignore-tlog --key k8s/cosign.pub "$IMAGE"
```

### Enforce bằng Kyverno

```bash
bash scripts/admission.sh
bash scripts/prepare-unsigned.sh
kubectl get clusterpolicy verify-notes-image
```

Policy giới hạn namespace `notes` và repository app lab, yêu cầu signature từ public key của workshop. Kyverno fetch manifest/signature từ private ECR bằng registry secret; secret được tạo qua stdin, không đưa vào Hugo hoặc command arguments. ECR token hết hạn sau khoảng 12 giờ: refresh bằng script trước lượt thử tiếp theo. Production nên dùng credential provider/identity được quản lý phù hợp.

**Positive test:** server-side dry-run pod Restricted dùng digest đã ký phải được chấp nhận. **Negative test:** cùng repo nhưng digest mới chưa ký phải bị webhook từ chối. `verify.py --supply-chain` thực hiện hai test sau bước `prepare-unsigned.sh`. Script build cùng source với một image label khác để có digest mới, push nhưng không ký hoặc deploy nó.

### Phạm vi và tradeoff

Ở chart 3.9.2 đã kiểm chứng, `ClusterPolicy` là API legacy vẫn được hỗ trợ; đánh giá migration sang `ImageValidatingPolicy` khi nâng cấp. Policy này kiểm tra image API/worker của lab, chưa bao phủ mọi repository hoặc image Nginx upstream. Không khẳng định toàn cluster chỉ chạy signed images. Webhook fail-closed tăng bảo vệ nhưng phụ thuộc availability của verifier/registry; một replica Kyverno chỉ phù hợp sandbox. Native CEL admission có thể kiểm tra digest/registry pattern, nhưng không tự xác minh Cosign signature, nên lab dùng verifier thực.
''')
page(5,3,'secrets','Kubernetes Secrets & AWS Secrets Manager',r'''
## Credentials phải được bảo vệ cả lúc lưu và lúc sử dụng

Kubernetes Secret thường biểu diễn dữ liệu bằng Base64 khi xuất YAML. Base64 không phải encryption. Ai có quyền đọc Secret hoặc exec vào workload có secret có thể tiếp cận dữ liệu đó.

### Console: quan sát secret do RDS quản lý

RDS → database → Configuration → Master credentials ARN → mở Secrets Manager. Kiểm tra encryption key và access policy. Không bấm hiển thị password để chụp ảnh đưa lên workshop.

Lab chỉ cấp `GetSecretValue` trên ARN này cho role `eks-did-db-init`. Job khởi tạo schema và hai user `notes_api`, `notes_worker`, cấp `rds_iam` và SQL grants tối thiểu. API/worker không đọc master password; SDK ký IAM DB auth token ngắn hạn khi mở connection, kết hợp TLS verify-full.

### CLI/API: xem metadata, không in secret

```bash
aws secretsmanager describe-secret --secret-id "$DB_SECRET_ARN" \
  --query '{arn:ARN,rotation:RotationEnabled,key:KmsKeyId}'
kubectl get job db-init -n notes
kubectl logs job/db-init -n notes
```

Mong đợi init job hoàn tất và log không chứa password. RDS master credential rotation do dịch vụ quản lý cần được kiểm tra theo cấu hình; không suy ra chỉ từ việc secret tồn tại.

### Negative tests

1. Observer đọc Kubernetes Secrets phải `Forbidden` (bài 4.4).
2. API gọi `GetSecretValue` trên master ARN phải `AccessDenied`.
3. API vẫn đọc/ghi đúng bảng bằng IAM DB auth. Điều đó chứng minh việc bỏ master secret không làm app mất quyền nghiệp vụ cần thiết.

```bash
kubectl exec -n notes deployment/api -- python -c '
import boto3,os
from botocore.exceptions import ClientError
try:
    boto3.client("secretsmanager").get_secret_value(SecretId=os.environ["DB_SECRET_ARN"])
    raise SystemExit("UNEXPECTED: API can read master secret")
except ClientError as e:
    print(e.response["Error"]["Code"])
    assert "AccessDenied" in e.response["Error"]["Code"]'
```

Job không print secret; mã bootstrap nằm trong [main.py](/source/app/main.py). Sau khi hoàn tất, xóa pod job nếu không cần giữ để quan sát. Thu hồi association/bootstrap role khi đã chốt schema là bước hardening tiếp theo; role này không dành cho app chạy thường xuyên.
''')
page(5,4,'encryption','Data Encryption với AWS KMS',r'''
## Mã hóa ở đâu, bằng key nào?

![Các ranh giới mã hóa](/images/encryption.svg)

| Đoạn / nơi lưu | Cơ chế trong lab |
|---|---|
| Client → ALB | TLS certificate ACM |
| ALB → Nginx → API | HTTP private; chưa mã hóa end-to-end |
| API/worker → RDS | TLS `verify-full` với RDS CA bundle |
| RDS storage | Encryption dùng key mặc định của RDS trong account |
| EBS node disks | Encrypted EBS |
| SQS | SSE-SQS; không phải demo CMK bên dưới |
| ECR | AES-256 repository encryption |
| KMS lab key | CMK riêng cho bài Encrypt/Decrypt, không tự bảo vệ toàn bộ tài nguyên |

### Console: tạo và kiểm tra key

KMS → Customer managed keys → Create symmetric Encrypt/Decrypt key → alias `eks-did`. Giới hạn key administrators/users vào identity lab cần thiết, bật rotation. Terraform tạo `aws_kms_key.lab` và alias, tùy chọn tắt nếu SCP không cho.

RDS → Configuration kiểm tra storage encrypted và KMS key ID. ECR/SQS có cấu hình riêng; đừng nhìn thấy một CMK rồi kết luận mọi dịch vụ đang sử dụng nó.

### CLI/API: round-trip có thể tái lập

```bash
mkdir -p .local
printf 'eks-defense-in-depth-demo' > .local/plaintext.txt
aws kms encrypt --key-id alias/eks-did \
  --plaintext fileb://.local/plaintext.txt \
  --encryption-context Workshop=eks-did \
  --query CiphertextBlob --output text | base64 --decode > .local/ciphertext.bin
aws kms decrypt --ciphertext-blob fileb://.local/ciphertext.bin \
  --encryption-context Workshop=eks-did \
  --query Plaintext --output text | base64 --decode > .local/decrypted.txt
cmp .local/plaintext.txt .local/decrypted.txt
```

Mong đợi `cmp` exit 0. Negative test: decrypt cùng ciphertext nhưng context `Workshop=other` phải trả `InvalidCiphertextException`. Encryption context là AAD, không phải secret; không đặt dữ liệu nhạy cảm trong đó.

### Giới hạn và cleanup

At-rest encryption không chặn principal được cấp quyền hợp lệ đọc plaintext qua API. KMS policy, IAM và resource permissions vẫn quan trọng. Khi teardown, CMK được schedule deletion sau 7 ngày, không biến mất ngay; xem trạng thái PendingDeletion. Không xóa key bảo vệ dữ liệu còn cần khôi phục.
''')
write(Path('cleanup'),'Cleanup: gỡ lab đúng thứ tự',90,r'''
## Đóng website không dừng tính phí

Chạy cleanup trong đúng account/profile. Lab dùng prefix `eks-did` và kubeconfig riêng; không xóa VPC/default resources hoặc dịch vụ của người khác.

### Console: những tài nguyên cần gỡ

1. EKS/Kubernetes: xóa Ingress trước, đợi controller xóa ALB, target groups và SG do nó quản lý. Sau đó gỡ namespace app, Kyverno và controller.
2. Route 53: xóa **record ứng dụng `notes`**, không xóa public hosted zone sandbox.
3. Gỡ node group/add-ons/cluster; RDS, queue, ECR lab; NAT trước khi release EIP; subnet/route/IGW/VPC sau khi ENI không còn.
4. Xóa ACM certificate và record validation thuộc cert lab. Schedule deletion CMK; xóa alias lab.
5. Inspector là account-level setting: chỉ disable nếu chính lab đã bật và không có consumer khác. Không tắt scanning toàn account dùng chung mà không review.

### CLI: gỡ tài nguyên do controller quản lý

```bash
source scripts/env.sh
python3 scripts/cleanup.py
```

Script xác nhận cluster tên `eks-did`, xóa signature policy trước, gỡ Ingress và đợi ALB biến mất, rồi xóa namespace và Helm releases. Nó không destroy VPC/RDS.

### Terraform: chỉ cho tài nguyên được quản lý bằng state này

```bash
terraform -chdir=infrastructure/terraform plan -destroy -out=destroy.tfplan
# Kiểm tra plan chỉ chứa tài nguyên lab của state này.
terraform -chdir=infrastructure/terraform apply destroy.tfplan
```

Lab cấu hình RDS `skip_final_snapshot=true` và ECR `force_delete=true` để teardown disposable data. Không dùng lựa chọn đó cho dữ liệu cần giữ. Nếu tạo bằng Console, xóa bằng Console/API hoặc import state có review, không chạy destroy trong state rỗng rồi cho rằng đã dọn xong.

### Xác minh sau cleanup

```bash
aws eks list-clusters
aws rds describe-db-instances --query 'DBInstances[].DBInstanceIdentifier'
aws elbv2 describe-load-balancers --query 'LoadBalancers[].LoadBalancerName'
aws ec2 describe-nat-gateways --filter Name=state,Values=available,pending \
  --query 'NatGateways[].{id:NatGatewayId,vpc:VpcId}'
```

Kiểm tra EIP, CloudWatch log groups và KMS PendingDeletion. Giữ lại source, public key và báo cáo đã loại credentials; không upload state, registry auth secret hoặc private signing key.
''')
write(Path('validation'),'Kiểm chứng và trạng thái sandbox',80,r'''
## Ý định và kết quả là hai thứ khác nhau

Hướng dẫn trong từng bài mô tả kết quả mong đợi. Báo cáo tại đây ghi những gì bộ kiểm tra thực sự quan sát. `PASS` chỉ áp dụng cho phép thử được nêu, không phải chứng nhận production-ready.

```bash
source scripts/env.sh
python3 scripts/verify.py
# Sau khi hoàn thành signing/admission và tạo unsigned image:
python3 scripts/verify.py --supply-chain
```

Bộ kiểm tra chạy app flow, WAF, network allow/deny, observer credentials, IAM deny, PostgreSQL grants, PSA, IMDS và KMS round-trip. Các bài kiểm tra không khai thác lỗ hổng hoặc chạy workload privileged.

Image scanning và release gate có [báo cáo riêng](/evidence/image-scan.json): gate có thể chặn release dù các test chức năng/phân quyền PASS. Tải [SBOM CycloneDX thực tế](/evidence/sbom.cdx.json) để xem thành phần image.

Xem [báo cáo thực nghiệm](/validation/results/) để biết test đã chạy và giới hạn. Script lưu log chi tiết trong `.local/` được gitignore; bản public chỉ lưu kết quả đã lọc.
''')
for i,(slug,title) in enumerate(MODULES,1):
 rows=[f'| {m}.{n} | [{t}]({"/"+p+"/"}) |' for m,n,p,t in PAGES if m==i]
 write(Path(slug),title,i+1,'\n\n'.join([f'Module {i} liên kết kiến thức với thao tác trên cùng một hệ thống lab. Đọc [Chuẩn bị](/preparation/) trước khi tạo tài nguyên.','| Bài | Nội dung |\n|---|---|\n'+'\n'.join(rows),'Đọc sơ đồ ở đầu bài, thực hiện theo Console → CLI/API → Terraform và kiểm chứng trước khi sang bài tiếp.']), f'<b>{i}.</b> ')
# Emit a navigation map for validation and future edits.
(ROOT/'evidence/content-map.json').write_text(json.dumps(PAGES,ensure_ascii=False,indent=2))
print('Generated',len(PAGES),'lessons across',len(MODULES),'modules.')
