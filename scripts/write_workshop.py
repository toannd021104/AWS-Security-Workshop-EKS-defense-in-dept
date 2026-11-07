from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
C=ROOT/'workshop/content'
MODULES=[('1-introduction','Introduction to Defense in Depth'),('2-network-security','Network Security – Securing the Request Path'),('3-kubernetes-security','Kubernetes Security – Securing Workloads'),('4-identity','Identity & Access Management – Securing Permissions'),('5-supply-chain-data','Supply Chain & Data Security')]
PAGES=[]

def write(path,title,weight,body,pre='',**params):
 p=C/path/'_index.md';p.parent.mkdir(parents=True,exist_ok=True)
 p.write_text('---\ntitle: '+json.dumps(title,ensure_ascii=False)+'\nweight: '+str(weight)+'\nchapter: false\npre: '+json.dumps(pre)+'\n'+''.join(k+': '+json.dumps(v,ensure_ascii=False)+'\n' for k,v in params.items())+'---\n\n'+body.strip()+'\n')
def page(m,n,slug,title,body):
 path=MODULES[m-1][0]+'/'+str(n)+'-'+slug
 write(Path(path),title,n,body,f'<b>{m}.{n}.</b> ');PAGES.append((m,n,path,title))
write(Path('.'),'A Layered Approach to Amazon EKS Security',0,r'''
## Bảo vệ một ứng dụng, từng lớp một

Một ứng dụng chạy được trên Amazon EKS chưa trả lời hết các câu hỏi về bảo mật. Request từ Internet đi vào pod nào? Frontend có thể kết nối thẳng đến database không? API có cần quyền nhận message mà worker đang xử lý không?

Workshop này sử dụng **Notes**, một ứng dụng lưu ghi chú và tạo báo cáo, để trả lời từng câu hỏi bằng cấu hình và phép thử thực tế. Bắt đầu với ứng dụng hoạt động qua HTTPS, các bài tiếp theo lần lượt kiểm tra đường mạng, giới hạn kết nối giữa workload, thu hẹp quyền truy cập và kiểm chứng cách bảo vệ image, secrets, dữ liệu.

Sau mỗi thay đổi, chạy lại luồng lưu ghi chú và tạo báo cáo. Kết quả cần đạt gồm hai phần: thao tác hợp lệ vẫn hoạt động, còn kết nối hoặc quyền không cần thiết bị từ chối.

## Bạn sẽ thực hiện những gì?

- Lần theo request từ Internet qua ALB đến frontend và API trên EKS; đối chiếu listener, target group và pod IP.
- Giới hạn đường kết nối bằng Security Groups và NetworkPolicy, rồi so sánh trước và sau khi áp dụng policy.
- Kiểm tra pod hardening, quyền quản trị qua IAM/RBAC và AWS role riêng cho API, worker.
- Scan và ký image, thử admission policy, kiểm tra quyền truy cập secrets và mã hóa dữ liệu.

## Ứng dụng xuyên suốt workshop

Frontend phục vụ giao diện và chuyển lời gọi đến API. API lưu ghi chú trong RDS PostgreSQL; khi có yêu cầu tạo báo cáo, API gửi message đến SQS. Worker nhận message, xử lý và lưu kết quả vào database. Ba workload chạy trên EKS; database nằm ngoài cluster, sử dụng RDS.

![Kiến trúc tổng quan của Notes](/images/high-level.svg "Frontend, API và worker có nhiệm vụ riêng. Các bài thực hành lần lượt giới hạn kết nối và quyền theo những nhiệm vụ đó.")

Không cần xây một ứng dụng mới ở mỗi chương. Cùng một request và cùng một luồng nghiệp vụ được dùng để kiểm tra tác động của các lớp bảo vệ.

## Workshop dành cho ai?

Người đã làm quen với AWS và Kubernetes, muốn thực hành bảo mật một ứng dụng EKS theo đường truy cập thực tế. Nên biết cách dùng terminal và đọc YAML cơ bản; khái niệm Pod, Service, IAM, Security Groups được nhắc lại tại bước cần sử dụng.

Cần một **tài khoản AWS**, quyền tạo các tài nguyên của lab và domain public có thể cấu hình DNS. Phần chuẩn bị hướng dẫn từ công cụ, VPC và cluster đến triển khai ứng dụng; không giả định bạn đã có lab chạy sẵn.

## Lộ trình thực hành

| Phần | Công việc chính | Thời gian dự kiến |
|---|---|---|
| [1. Introduction](/1-introduction/) | Hiểu bối cảnh, kiến trúc và các ranh giới bảo vệ | 20–30 phút |
| [Chuẩn bị lab](/preparation/) | Tạo hạ tầng, triển khai Notes và kiểm tra baseline | 90–150 phút |
| [2. Network Security](/2-network-security/) | Theo request và kiểm tra lớp mạng AWS | 60–90 phút |
| [3. Kubernetes Security](/3-kubernetes-security/) | Giới hạn kết nối và quyền thực thi workload | 75–105 phút |
| [4. Identity & Access Management](/4-identity/) | Kiểm chứng quyền của người dùng và ứng dụng | 60–90 phút |
| [5. Supply Chain & Data Security](/5-supply-chain-data/) | Kiểm tra image, admission, secrets và encryption | 60–90 phút |
| [Tổng kết](/summary/) và [Cleanup](/cleanup/) | Đối chiếu bằng chứng và gỡ tài nguyên | 15–30 phút |

Dự trù khoảng **6–10 giờ**, có thể chia thành nhiều buổi. Đây là ước lượng để lên kế hoạch; thời gian tạo tài nguyên và kinh nghiệm thao tác sẽ ảnh hưởng thời lượng thực tế.

Mỗi phần sử dụng kết quả của phần trước. Bắt đầu với **Introduction**, tiếp tục **Chuẩn bị lab**, rồi thực hành chương 2–5. Dùng nút **Trước / Tiếp** ở cuối trang hoặc menu bên trái để di chuyển. Các bước AWS ưu tiên Console; CLI/API hỗ trợ thao tác Kubernetes và kiểm tra kết quả, Terraform là nhánh triển khai thay thế.

> **Chi phí:** Các tài nguyên AWS do bạn tạo được tính phí theo tài khoản đang sử dụng. Đóng trình duyệt không dừng tài nguyên; thực hiện [Cleanup](/cleanup/) khi kết thúc hoặc khi không tiếp tục lab.

Mã nguồn có trong [gói lab ZIP](/downloads/eks-defense-in-depth-lab.zip). [Báo cáo kiểm chứng](/validation/results/) ghi kết quả đã quan sát trên lab tham chiếu; [image scan](/evidence/image-scan.json) có gate riêng và có thể chặn release dù ứng dụng chạy được.
''')
from preparation_content import write_preparation
write_preparation(write)
page(1,1,'defense-in-depth','Defense in Depth là gì?',r'''
Defense in Depth là cách phối hợp nhiều lớp bảo vệ để hạn chế khả năng truy cập trái phép và giảm phạm vi ảnh hưởng khi một lớp bị vượt qua. Mỗi lớp kiểm soát một ranh giới khác nhau: kết nối mạng, quyền thực thi, quyền truy cập hoặc dữ liệu.

Trong ứng dụng của workshop, người dùng gửi request qua ALB đến frontend. Frontend gọi API; API lưu ghi chú trên RDS và gửi yêu cầu tạo báo cáo đến SQS. Worker nhận yêu cầu từ SQS và ghi kết quả vào database. Những thành phần này cần các kết nối và quyền khác nhau để hoàn thành công việc.

HTTPS bảo vệ kết nối từ người dùng đến ALB. Security Groups giới hạn kết nối giữa các tài nguyên AWS. NetworkPolicy tiếp tục giới hạn lưu lượng giữa workload trong cluster. Pod Security Admission và SecurityContext kiểm soát cấu hình thực thi của container, còn IAM và RBAC xác định các thao tác được phép.

![Các lớp bảo vệ trên kiến trúc ứng dụng](/images/high-level.svg "Mỗi workload có vai trò riêng; các lớp bảo vệ được áp dụng theo đường truy cập và trách nhiệm của workload.")

Ví dụ, frontend chỉ cần gọi API nên không được kết nối trực tiếp đến RDS. Nếu container frontend gặp sự cố, giới hạn này giúp thu hẹp đường truy cập sang database. API được gửi message vào SQS nhưng không cần nhận hoặc xóa message; những thao tác đó thuộc về worker.

Các lớp bảo vệ cần được kiểm tra cùng nhau. Sau khi cho phép frontend gọi API, cần thử thêm một pod không thuộc ứng dụng để xác nhận nó bị chặn. Sau khi giới hạn quyền AWS của API, chức năng lưu ghi chú và gửi yêu cầu báo cáo vẫn phải hoạt động.

Workshop tập trung vào các lớp bảo vệ này trên Amazon EKS. Phần tiếp theo xác định những ranh giới cần kiểm soát trong một hệ thống kết hợp AWS và Kubernetes.
''')
page(1,2,'why-eks','Tại sao Amazon EKS cần Defense in Depth?',r'''
Amazon EKS cung cấp Kubernetes control plane được AWS quản lý. Ứng dụng chạy trên cluster vẫn phụ thuộc vào cách cấu hình mạng, worker nodes, container images và quyền truy cập. Vì vậy, việc sử dụng managed Kubernetes cần đi cùng các kiểm soát dành cho workload.

Một request đến ứng dụng đi qua nhiều ranh giới. Ở phía AWS, ALB nhận kết nối, Security Groups giới hạn lưu lượng và VPC cung cấp đường định tuyến. Khi request vào cluster, Kubernetes Service, pod labels và NetworkPolicy quyết định cách các workload kết nối. Các lời gọi đến SQS hoặc RDS tiếp tục chịu kiểm soát của IAM và quyền database.

Private subnet giúp worker nodes không cần public IP để phục vụ ứng dụng qua ALB. Tuy nhiên, các pod trong VPC vẫn có thể kết nối với nhau nếu chưa có cơ chế hạn chế. Tương tự, việc cấp IAM role riêng cho API chỉ phát huy tác dụng khi pod không lấy được quyền rộng hơn từ worker node.

Trong lab, ba workload được tách theo chức năng. Frontend phục vụ giao diện và chuyển request đến API. API thực hiện nghiệp vụ đồng bộ. Worker xử lý báo cáo ở phía sau, không mở endpoint cho người dùng. RDS được triển khai bên ngoài cluster bằng dịch vụ managed.

Cách phân chia này cho phép áp dụng các giới hạn cụ thể: frontend không có AWS role ứng dụng; API chỉ gửi vào queue của lab; worker nhận và xóa message từ queue đó. Quyền PostgreSQL cũng được tách theo công việc của API và worker.

Các chương tiếp theo lần lượt triển khai và kiểm chứng những giới hạn này. Ứng dụng mẫu phục vụ việc học network và phân quyền, chưa có cơ chế đăng nhập người dùng; chỉ sử dụng dữ liệu thử nghiệm trong lab.
''')
page(1,3,'shared-responsibility','AWS Shared Responsibility Model',r'''
AWS Shared Responsibility Model phân chia trách nhiệm bảo mật giữa AWS và người sử dụng dịch vụ. Với Amazon EKS, AWS vận hành hạ tầng của Kubernetes control plane. Người dùng quản lý cách truy cập cluster và cấu hình các workload chạy trên đó.

Workshop sử dụng EKS managed node groups. AWS cung cấp cơ chế tạo và cập nhật node group; người vận hành vẫn lựa chọn phiên bản, lên lịch cập nhật, cấu hình IAM role và kiểm soát truy cập EC2 Instance Metadata Service. Ranh giới này khác với các lựa chọn compute như Fargate hoặc EKS Auto Mode.

![Thông tin cluster EKS thực tế](/images/console-eks.png "Cluster của lab sử dụng EKS 1.35. AWS quản lý control plane; cấu hình truy cập và workload thuộc trách nhiệm của người triển khai.")

| Thành phần | AWS quản lý | Người dùng cấu hình |
|---|---|---|
| EKS control plane | Hạ tầng và vận hành control plane | Endpoint access, Access Entries và authorization |
| Managed node group | Cơ chế provisioning và update | AMI release, rollout cập nhật, IAM role, IMDS và workload placement |
| VPC | Hạ tầng mạng AWS | Subnets, route tables, Security Groups và NACLs |
| Kubernetes workload | Nền tảng dịch vụ bên dưới | Image, SecurityContext, NetworkPolicy và workload identity |
| RDS | Hạ tầng database managed | Network access, users, SQL grants, backup và encryption settings |

Ví dụ, RDS hỗ trợ mã hóa storage và quản lý master credentials, nhưng người triển khai phải lựa chọn cấu hình phù hợp và giới hạn quyền truy cập. EKS hỗ trợ NetworkPolicy qua VPC CNI, nhưng policy chỉ có hiệu lực khi tính năng thực thi được bật và các rule được khai báo đúng.

Khi đọc kiến trúc ở bài tiếp theo, mỗi ranh giới bảo mật sẽ gắn với một thành phần và một trách nhiệm cụ thể. Đây là cơ sở để xác định cấu hình cần thực hiện trong các bài thực hành.
''')
page(1,4,'architecture','Tổng quan kiến trúc và các Security Layers',r'''
Ứng dụng của workshop là một website ghi chú chạy trên Amazon EKS. Kiến trúc được chia thành ba workload: Nginx frontend, Python API và Python worker. RDS PostgreSQL lưu dữ liệu; SQS tách việc tạo báo cáo khỏi request trực tiếp của người dùng.

![Kiến trúc AWS của workshop](/images/aws-architecture.svg "ALB nằm trong public subnets; worker nodes nằm trong private application subnets; RDS sử dụng database subnets riêng. Khung nét đứt biểu diễn các ranh giới mạng và logical.")

### Luồng truy cập ứng dụng

Trình duyệt phân giải domain và kết nối ALB bằng HTTPS. ALB kết thúc TLS rồi chuyển request bằng HTTP đến frontend pod port 8080. Nginx phục vụ giao diện và chuyển các request `/api/` đến Kubernetes Service của API. API kết nối RDS bằng TLS và sử dụng IAM database authentication với user `notes_api`.

> **Phạm vi mã hóa và bảo vệ kết nối:** Lab sử dụng HTTPS để mã hóa lưu lượng từ Internet đến ALB. Từ ALB đến frontend pod và từ frontend đến API, ứng dụng sử dụng HTTP qua địa chỉ IP nội bộ trong VPC. Security Groups giới hạn kết nối ở lớp hạ tầng; Kubernetes NetworkPolicy được bổ sung trong chương 3 để giới hạn kết nối theo workload. Đây là lựa chọn của lab để tập trung thực hành bảo mật mạng và workload trên EKS.

### Luồng xử lý báo cáo

API gửi message vào SQS khi nhận yêu cầu tạo báo cáo. Worker chủ động đọc queue, lấy dữ liệu cần thiết và ghi báo cáo vào RDS bằng user `notes_worker`. SQS không mở kết nối inbound vào worker; worker không cần public endpoint hoặc Kubernetes Service riêng.

### Luồng quản trị và cấp quyền

Người vận hành dùng `kubectl` kết nối đến EKS API endpoint. Đường quản trị này đi riêng với ALB phục vụ website. IAM xác thực danh tính; EKS Access Entries và Kubernetes RBAC cấp quyền thao tác tài nguyên.

API và worker sử dụng EKS Pod Identity để nhận temporary AWS credentials theo ServiceAccount. Sau đó ứng dụng dùng credentials này để gọi SQS hoặc ký token kết nối RDS. Frontend không cần IAM role ứng dụng.

### Các lựa chọn trong lab

ALB sử dụng IP targets để chuyển request đến pod IP do VPC CNI cấp. NetworkPolicy kiểm soát kết nối theo workload; node Security Groups tiếp tục bảo vệ ở lớp tài nguyên AWS. Các lựa chọn và trường hợp thay thế được giải thích trong chương tương ứng.

Lab sử dụng một NAT Gateway và RDS Single-AZ để giảm chi phí. Đây là các đánh đổi của môi trường thực hành; kiến trúc production cần đánh giá thêm yêu cầu availability và đường kết nối private.

Có thể tải [sơ đồ AWS dạng draw.io](/images/aws-architecture.drawio) và [sơ đồ high-level dạng draw.io](/images/high-level.drawio) để xem hoặc chỉnh sửa. Chương 2 bắt đầu bằng việc theo dõi một request qua kiến trúc này.
''')
page(2,1,'request-flow','Request Flow: Internet → ALB → Pod',r'''
Ứng dụng được truy cập qua một domain public, trong khi các pod nằm trong private subnets. Trước khi cấu hình các lớp bảo vệ, cần xác định request đi qua những thành phần nào và cách kiểm tra từng chặng. Bài này đối chiếu đường đi của request với cấu hình ALB, pod IP và kết quả đọc/ghi dữ liệu.

## Request đi qua những đâu?

![Request path từ client đến PostgreSQL](/images/request-path.svg "ALB gửi đến frontend pod IP; frontend gọi API qua Service nội bộ.")

Lấy ví dụ người dùng mở `https://notes.<domain>` để xem danh sách ghi chú. Trình duyệt cần tải giao diện trước, sau đó gọi API để lấy dữ liệu. Hai việc này đi qua các thành phần sau:

1. **DNS giúp trình duyệt tìm địa chỉ ALB.** Trình duyệt tra tên miền `notes.<domain>` để biết địa chỉ cần kết nối. DNS chỉ giúp tìm địa chỉ; request của ứng dụng được gửi đến ALB.

2. **ALB nhận kết nối HTTPS từ trình duyệt.** Người dùng truy cập bằng HTTPS trên cổng `443`. ALB xử lý phần mã hóa của kết nối này, sau đó chọn một frontend pod đang sẵn sàng và chuyển request đến pod đó bằng HTTP trên cổng `8080`.

3. **Frontend trả giao diện, rồi chuyển tiếp các lời gọi API.** Nginx trong frontend pod trả HTML và JavaScript cho trình duyệt. JavaScript tiếp tục gửi `GET /api/notes` để lấy danh sách ghi chú. Request này cũng đi qua ALB đến frontend, nhưng Nginx chuyển nó đến API thay vì trả một file giao diện.

4. **Kubernetes Service giúp frontend tìm API pod.** Nginx gọi Service `api` trong namespace `notes`, qua địa chỉ nội bộ `api.notes.svc.cluster.local:8080`. Khi chuyển tiếp, Nginx bỏ phần `/api/` ở đầu đường dẫn: `/api/notes` trở thành `/notes`, là endpoint mà API xử lý.

5. **API đọc dữ liệu từ RDS và trả kết quả.** API kết nối đến RDS PostgreSQL trên cổng `5432`, sử dụng TLS để mã hóa kết nối database. Sau khi đọc các ghi chú, API trả dữ liệu JSON về qua frontend và ALB. Trình duyệt nhận JSON rồi hiển thị danh sách trên giao diện.

Với thao tác lấy danh sách ghi chú, đường đi là **trình duyệt → ALB → frontend → API → RDS**. Frontend chuyển tiếp lời gọi đến API; API là thành phần truy vấn database.

> **Phạm vi mã hóa và bảo vệ kết nối:** Lab sử dụng HTTPS để mã hóa lưu lượng từ Internet đến ALB. Từ ALB đến frontend pod và từ frontend đến API, ứng dụng sử dụng HTTP qua địa chỉ IP nội bộ trong VPC. Security Groups giới hạn kết nối ở lớp hạ tầng; Kubernetes NetworkPolicy được bổ sung trong chương 3 để giới hạn kết nối theo workload. Đây là lựa chọn của lab để tập trung thực hành bảo mật mạng và workload trên EKS.

Bài này quan sát lab đã chạy, sử dụng tài nguyên được tạo ở phần chuẩn bị. Hoàn thành [bước 0.8 — Kiểm tra baseline](/preparation/8-baseline/) trước khi chạy các lệnh bên dưới.

## Bước 1: đối chiếu đường đi trên AWS Console

Các bước sau chỉ đọc cấu hình, không tự tạo hoặc đăng ký thêm target. Mục đích là nối domain, listener, target group và pod thành một đường truy cập có thể kiểm tra.

1. Mở **Route 53 → Hosted zones → public zone của lab**, chọn record `notes`. Đọc phần value/alias target và đối chiếu với DNS name của ALB `eks-did-notes`.
2. Mở **EC2 → Load Balancers → eks-did-notes → Listeners and rules**. Listener HTTP:80 cần redirect đến HTTPS:443; listener HTTPS:443 cần forward đến target group frontend. Ghi lại target group đang được dùng.
3. Mở target group đó → tab **Targets**. Xem Target type **IP**, protocol/port **HTTP:8080** và các targets **Healthy**. Đây là danh sách do controller đăng ký, không yêu cầu bạn thêm IP bằng tay.
4. Mở **EKS → cluster → Resources → Workloads → Pods**, lọc namespace `notes`, chọn frontend pod và đọc **Pod IP**. So IP này với các targets Healthy. Resource browser yêu cầu danh tính có quyền đọc Kubernetes; có thể dùng `kubectl get pods` ở phần dưới để lấy cùng thông tin.

Ví dụ, pod IP `10.20.44.78` xuất hiện trong target group với port `8080` giúp xác nhận ALB sử dụng frontend pod đó làm backend. IP thật thay đổi theo lượt triển khai.

![Đối chiếu ALB IP targets với frontend pods](/images/console-targets.png "① Target type IP. ② Backend HTTP:8080. ③ Hai targets healthy. ④ Địa chỉ IP và port của pods.")

Ảnh được chụp trong một lượt rollout nên có một target cũ ở trạng thái Draining. Khi đối chiếu với pod hiện tại, tập trung vào các targets Healthy.

## Kiểm tra request thực sự đến ứng dụng

### Gửi request và đọc kết quả

Nạp hostname và kubeconfig của lab:

```bash
source scripts/env.sh
printf 'Hostname: %s\n' "$APP_HOST"
```

`source` thường không in gì. Dòng `printf` phải in hostname đã được tạo ở bước chuẩn bị; nếu trống, hoàn thành [thu thập cấu hình ở bước 0.7](/preparation/7-deploy-application/) trước khi gửi request.

Kiểm tra frontend:

```bash
curl -sS -o /dev/null -w '%{http_code}\n' "https://$APP_HOST/"
```

Kết quả cần thấy:

```text
200
```

`-o /dev/null` bỏ HTML, `-w` chỉ in HTTP status. Trang chủ trả 200 xác nhận frontend phản hồi qua domain HTTPS.

Tiếp tục gọi API thông qua frontend:

```bash
curl -fsS "https://$APP_HOST/api/healthz"
printf '\n'
```

Kết quả:

```json
{"status": "ok", "workload": "api"}
```

Phản hồi này đến từ API sau khi request qua ALB và Nginx frontend. Health endpoint chưa chứng minh thao tác database hoạt động.

Đọc pod IPs để so với AWS target group:

```bash
kubectl get pods -n notes -l app=frontend -o wide
```

Ví dụ, tên và IP trong môi trường của bạn sẽ khác:

```text
NAME                        READY   STATUS    RESTARTS   AGE   IP
frontend-7c8d9f6b5d-abc12    1/1     Running   0          10m   10.20.44.78
frontend-7c8d9f6b5d-def34    1/1     Running   0          10m   10.20.54.165
```

Cột IP là địa chỉ dùng để đối chiếu targets; READY 1/1 cho biết container trong pod đã sẵn sàng. Đọc access log:

```bash
kubectl logs -n notes -l app=frontend --tail=10 --prefix=true
```

Log có thể chứa dòng tương tự:

```text
[pod/frontend-…/frontend] … "GET /api/healthz HTTP/1.1" 200 …
```

Tên pod/container trong prefix cho biết backend nhận request. ALB health checks cũng xuất hiện trong log, và mười dòng cuối có thể không còn chứa request vừa gửi.

### Kiểm tra đường API đến database

```bash
curl -fsS "https://$APP_HOST/api/notes" \
  -H 'Content-Type: application/json' -d '{"body":"Hello from the request path"}'
curl -fsS "https://$APP_HOST/api/notes"
```

POST phải trả ID, GET phải có ghi chú. Không ghi chú thật hoặc dữ liệu nhạy cảm vì app chưa có user authentication.

### Đọc đúng địa chỉ nguồn của request

`X-Forwarded-For` mang IP client trong HTTP header; đây không nhất thiết là source IP mà NetworkPolicy thấy trên kết nối ALB → pod. Không dùng header để viết rule L3/L4. Các bài 2.2–2.6 sẽ giải thích mạng và target registration đằng sau đường đi này. Cấu hình có trong [render.py](/source/scripts/render.py).

Kết quả cần đối chiếu gồm target IP trùng frontend pod IP, HTTP status 200 ở trang chủ/API health và ghi chú vừa POST xuất hiện trong GET. Ba bằng chứng này lần lượt xác nhận backend registration, đường HTTP và thao tác database.
''')
page(2,2,'vpc','VPC Architecture: Public & Private Subnets, Routing, NAT Gateway',r'''
ALB cần tiếp nhận request từ Internet; worker nodes cần truy cập các dịch vụ AWS mà không có public IP; database chỉ cần phục vụ kết nối nội bộ. Bài này bố trí ba nhóm subnet và cấu hình route table phù hợp với từng nhu cầu.

## Vì sao tách ba nhóm subnet?

Route table được liên kết với subnet để xác định đường đi theo địa chỉ đích. Route `local` phục vụ kết nối trong VPC. Public subnet có route đến Internet Gateway; application subnet dùng NAT Gateway cho kết nối outbound. NAT Gateway không cung cấp đường cho Internet chủ động kết nối vào private workload.

Một subnet có route đến Internet Gateway không làm mọi EC2 trong đó tự public: tài nguyên vẫn cần địa chỉ public phù hợp và rule cho phép. Ngược lại, private subnet không tự ngăn kết nối nội bộ VPC.

| Nhóm | AZ A | AZ B | Default route |
|---|---|---|---|
| Public | 10.20.0.0/20 | 10.20.16.0/20 | Internet Gateway |
| Application | 10.20.32.0/20 | 10.20.48.0/20 | Một NAT Gateway ở AZ A |
| Database | 10.20.64.0/24 | 10.20.65.0/24 | Không có; chỉ local VPC |

Các tài nguyên này đã được dựng trong [phần chuẩn bị lab](/preparation/2-vpc/). Đối chiếu cấu hình hiện có theo các bước dưới đây; chỉ tạo mới nếu tài nguyên tương ứng chưa tồn tại.

## Bước 1: tạo VPC, subnets và route tables

1. VPC → Your VPCs → Create VPC → **VPC only**, Name `eks-did`, IPv4 `10.20.0.0/16`. Bật DNS resolution và DNS hostnames trong VPC settings.

2. Subnets → Create subnet: tạo sáu subnet theo bảng, dùng hai AZ khả dụng. Đặt tên `eks-did-public-a/b`, `eks-did-private-a/b`, `eks-did-database-a/b`. Private/database không auto-assign public IP.

![Ba nhóm subnet của VPC lab](/images/console-subnets.png "① Public subnet. ② Private application subnet. ③ Database subnet.")

Các dòng khoanh đỏ thuộc VPC `eks-did`, có CIDR bắt đầu bằng `10.20`. Những dòng `172.31` còn lại thuộc default VPC của tài khoản AWS.

3. Internet Gateways → tạo `eks-did-igw`, attach vào VPC.

4. Route tables → tạo `eks-did-public`, thêm `0.0.0.0/0 → IGW`, associate đúng hai public subnets. Route local đã có sẵn.

5. NAT Gateways → tạo **public NAT**, public subnet AZ A, allocate Elastic IP. Đợi `Available`.

6. Tạo route table `eks-did-private`, thêm `0.0.0.0/0 → NAT`, associate hai application subnets.

7. Tạo route table `eks-did-database-isolated`, chỉ giữ route local, associate hai DB subnets.

8. Tag public subnets `kubernetes.io/role/elb=1`, application subnets `kubernetes.io/role/internal-elb=1`.

![Vị trí subnet và NAT trong AWS architecture](/images/aws-architecture.svg)

### Cấu hình tương đương qua API (tùy chọn)

Khi tạo thủ công, AWS API tương ứng là `CreateVpc`, `CreateSubnet`, `CreateRouteTable`, `CreateRoute` và `AssociateRouteTable`. Ví dụ tạo public route sau khi export hai ID thực:

```bash
aws ec2 create-route --route-table-id "$PUBLIC_ROUTE_TABLE_ID" \
  --destination-cidr-block 0.0.0.0/0 --gateway-id "$INTERNET_GATEWAY_ID"
```

Chỉ chạy khi route chưa tồn tại. Terraform tương ứng nằm trong [main.tf](/source/terraform/main.tf) và [data-services.tf](/source/terraform/data-services.tf).

## Kiểm tra đường định tuyến của từng subnet

### Kiểm tra routes và subnet associations

```bash
VPC_ID=$(aws ec2 describe-vpcs --filters Name=tag:Name,Values=eks-did --query 'Vpcs[0].VpcId' --output text)
aws ec2 describe-subnets --filters "Name=vpc-id,Values=$VPC_ID" \
  --query 'Subnets[].{id:SubnetId,cidr:CidrBlock,az:AvailabilityZone,publicIP:MapPublicIpOnLaunch}'
aws ec2 describe-route-tables --filters "Name=vpc-id,Values=$VPC_ID" \
  --query 'RouteTables[].{id:RouteTableId,subnets:Associations[].SubnetId,routes:Routes}'
```


### Lựa chọn một NAT Gateway cho lab

Một NAT tiết kiệm chi phí nhưng tạo phụ thuộc AZ và có thể phát sinh cross-AZ traffic. Production cần đánh giá NAT theo AZ hoặc VPC Endpoints. Endpoint cho ECR API/DKR vẫn còn dependency S3, EKS Auth, DNS và dịch vụ app; thêm một endpoint không chứng minh có thể bỏ NAT.

Kết quả đúng có ba loại route: public có `0.0.0.0/0` đến `igw-…`; application có default route đến `nat-…`; database chỉ có route local. Kiểm tra `Associations[].SubnetId` để xác nhận từng route table gắn đúng nhóm subnet. Tên subnet hoặc tên route table chưa đủ làm bằng chứng.
''')
page(2,3,'edge','Edge Security: AWS WAF, ALB và HTTPS',r'''
Điểm vào public cần bảo vệ dữ liệu truyền từ trình duyệt và có khả năng chặn request theo rule đã định. Bài này cấu hình domain, certificate và HTTPS trên ALB, sau đó gắn WAF và gửi request để kiểm tra hành vi cho phép hoặc từ chối.

## ALB, ACM và WAF bảo vệ phần nào?

ALB định tuyến HTTP, ACM cung cấp certificate cho TLS và WAF kiểm tra request HTTP. WAF gắn vào ALB, không phải một máy proxy đặt trước ALB.

Các tài nguyên này đã được dựng trong [phần chuẩn bị lab](/preparation/5-https-waf/). Đối chiếu cấu hình hiện có theo các bước dưới đây; chỉ tạo mới nếu tài nguyên tương ứng chưa tồn tại.

## Bước 1: cấu hình certificate và WAF rule

1. Route 53 → chọn public hosted zone bạn quản lý. Dùng hostname `notes.<zone>`; không tạo hosted zone mới rồi bỏ qua delegation.

2. ACM tại **us-east-1** → Request public certificate → nhập hostname → DNS validation. Chọn Create records in Route 53; đợi **Issued**. Certificate phải cùng Region với ALB.

![Certificate cho domain ứng dụng](/images/console-acm-certificate.png "① Certificate Issued. ② Domain ứng dụng. ③ DNS validation Success.")

Chỉ chuyển sang cấu hình HTTPS listener khi certificate đã Issued. DNS validation thành công xác nhận quyền kiểm soát domain; domain của người thực hành sẽ khác ảnh lab.

3. WAF → Web ACLs → Create → Regional, tên `eks-did`. Default action Allow.

4. Thêm custom rule `workshop-header-test`, match **single header** `x-workshop-test`, exactly matches `block-me`, transformation None, action Block. Bật sampled requests/metrics.

5. Ingress ở 2.5 dùng ARN certificate và ARN Web ACL. Sau khi ALB xuất hiện, kiểm tra WAF resource association.

![WAF rule thử nghiệm](/images/console-waf-rule.png "① Rule workshop-header-test. ② Action Block.")

Rule này chỉ kiểm chứng đường xử lý WAF bằng header cố định. Bộ rule bảo vệ production cần được lựa chọn và đánh giá riêng.

Managed rules và rate limiting cần được lựa chọn, kiểm thử và điều chỉnh false positives riêng.

### Cấu hình certificate qua API (tùy chọn)

Nếu dùng CLI thay Console để yêu cầu cert:

```bash
aws acm request-certificate --domain-name "$APP_HOST" --validation-method DNS
```

Sau đó đọc `describe-certificate`, tạo record validation và đợi `ISSUED`. Không yêu cầu lại cert nếu đã dùng Terraform. [Terraform WAF/ACM](/source/terraform/data-services.tf) chứa cấu hình đầy đủ.

## So sánh request được phép và bị WAF chặn

### Gửi request đến HTTP, HTTPS và WAF

```bash
aws acm list-certificates --certificate-statuses ISSUED
curl -sS -o /dev/null -w '%{http_code}\n' "http://$APP_HOST/"
curl -sS -o /dev/null -w '%{http_code}\n' "https://$APP_HOST/"
curl -sS -o /dev/null -w '%{http_code}\n' -H 'x-workshop-test: block-me' "https://$APP_HOST/"
```

Mong đợi HTTP redirect, HTTPS 200, request có header 403. Không dùng `curl -k`: lệnh phải xác minh certificate và hostname.


### TLS kết thúc ở đâu?

Client → ALB dùng HTTPS với certificate ACM. TLS kết thúc tại ALB; ALB → frontend pod dùng HTTP port `8080`, và frontend → API cũng dùng HTTP. API/worker → RDS dùng TLS xác minh CA/hostname.

![Giao thức thực tế của ALB backend](/images/console-target-protocol.png "① Backend protocol và port là HTTP:8080.")

Protocol của target group mô tả chặng ALB → frontend, khác với HTTPS listener phục vụ client. Đây là vị trí cần đối chiếu khi kiểm tra phạm vi TLS.

> **Phạm vi mã hóa và bảo vệ kết nối:** Lab sử dụng HTTPS để mã hóa lưu lượng từ Internet đến ALB. Từ ALB đến frontend pod và từ frontend đến API, ứng dụng sử dụng HTTP qua địa chỉ IP nội bộ trong VPC. Security Groups giới hạn kết nối ở lớp hạ tầng; Kubernetes NetworkPolicy được bổ sung trong chương 3 để giới hạn kết nối theo workload. Đây là lựa chọn của lab để tập trung thực hành bảo mật mạng và workload trên EKS.

Thiết kế này **không mã hóa toàn bộ request path**. Nếu chính sách bảo mật hoặc yêu cầu tuân thủ đòi hỏi mã hóa các chặng nội bộ, cần cấu hình HTTPS từ ALB đến frontend và TLS cho frontend → API. ALB không xác thực certificate của HTTPS target; yêu cầu xác minh danh tính workload cần được thiết kế riêng.

Đối chiếu ba request: HTTP trả redirect sang HTTPS; HTTPS thông thường trả 200; HTTPS có header thử nghiệm trả 403. Một kết nối HTTPS thành công xác nhận certificate/hostname hợp lệ, còn 403 của request thử xác nhận WAF rule tham gia xử lý.
''')
page(2,4,'security-groups','Network Access Control: Security Groups & NACLs',r'''
Ứng dụng cần nhận request trên 443 và kết nối database trên 5432, nhưng hai cổng này không có cùng phạm vi truy cập. Bài này cấu hình các rule theo nguồn và đích thực tế, rồi xác định giới hạn của Security Groups khi nhiều pod dùng chung node.

## Security Groups và NACLs khác nhau ở đâu?

Security Group gắn với network interface (ENI), tổng hợp các allow rules và theo dõi trạng thái kết nối. NACL gắn subnet, có allow/deny theo thứ tự và phải cho cả chiều trả về. Chúng không thay thế NetworkPolicy chọn pod theo label.

## Bước 1: cấu hình Security Groups và xem NACLs

1. VPC → Security groups → Create `eks-did-database` trong VPC lab. Inbound TCP 5432, **source là cluster/node SG thực tế**, không phải `0.0.0.0/0`. Gắn SG này vào RDS.

2. EKS → Configuration → Networking → Cluster security group (giao diện cũ: Networking). EC2 → node → Network interface kiểm tra SG thực sự gắn vào node/ENI. Lab launch template không đặt SG thay thế, nên managed nodes dùng cluster SG.

3. Sau khi tạo Ingress, xem SG do controller tạo cho ALB và rule cho backend. Listener chỉ mở 80/443; backend cần 8080 từ SG của load-balancing path, không public 8080.

4. VPC → Network ACLs → xem association và rule numbers. Lab giữ default NACL để tập trung SG/NetworkPolicy; không tự siết ephemeral ports khi chưa có traffic matrix.

### Cấu hình Security Group qua API (tùy chọn)

Nếu tạo database SG bằng API, `AuthorizeSecurityGroupIngress` dùng referenced group:

```bash
aws ec2 authorize-security-group-ingress --group-id "$DB_SG_ID" \
  --ip-permissions "IpProtocol=tcp,FromPort=5432,ToPort=5432,UserIdGroupPairs=[{GroupId=$NODE_SG}]"
```

Không thêm lại rule đã tồn tại. Terraform dùng `aws_vpc_security_group_ingress_rule.database`.

## Đối chiếu rule với đường kết nối ứng dụng

### Đọc các rule đang có hiệu lực

```bash
aws ec2 describe-security-group-rules \
  --filters "Name=group-id,Values=$NODE_SG" \
  --query 'SecurityGroupRules[].{egress:IsEgress,port:FromPort,to:ToPort,source:ReferencedGroupInfo.GroupId,cidr:CidrIpv4}'
aws ec2 describe-network-acls --filters "Name=vpc-id,Values=$VPC_ID" \
  --query 'NetworkAcls[].{id:NetworkAclId,associations:Associations[].SubnetId,rules:Entries}'
```


### Phạm vi bảo vệ của node Security Group

Tất cả pod dùng node SG có thể đi qua lớp SG đến RDS nếu không có kiểm soát bổ sung. **SG này không chỉ cho phép API/worker.** Module 3 dùng NetworkPolicy chặn frontend → RDS, còn PostgreSQL grants và IAM DB auth giới hạn quyền sử dụng DB. Security Groups for Pods là lựa chọn nâng cao khi cần SG theo workload, không được bật trong lab này.

Đối chiếu inbound của database: TCP 5432 phải tham chiếu Security Group của node, không mở Internet. Luồng ghi chú ở bài 2.1 vẫn phải hoạt động. Ở bài 3.2, thử thêm frontend → RDS để kiểm chứng giới hạn theo pod; Security Group dùng chung của node chưa chứng minh được sự cách ly đó.
''')
page(2,5,'controller-ingress','AWS Load Balancer Controller và Kubernetes Ingress',r'''
Một Ingress mô tả đường truy cập Kubernetes chưa tự tạo ra ALB trên AWS. Bài này thiết lập controller và quyền cần thiết để chuyển cấu hình Ingress thành load balancer, sau đó kiểm tra các tài nguyên được tạo.

## Ai tạo ALB từ Kubernetes Ingress?

Ingress mô tả host/path/backend. AWS Load Balancer Controller theo dõi Ingress, Service và EndpointSlice rồi gọi ELB/EC2 APIs tạo ALB, listener, target group và rule SG. Controller không proxy từng HTTP request của ứng dụng.

Các tài nguyên này đã được dựng trong [phần chuẩn bị lab](/preparation/7-deploy-application/). Đối chiếu cấu hình hiện có theo các bước dưới đây; chỉ tạo mới nếu tài nguyên tương ứng chưa tồn tại.

## Bước 1: cấp quyền cho controller

IAM → Roles → `eks-did-controller`: trust principal `pods.eks.amazonaws.com`, actions `sts:AssumeRole` và `sts:TagSession`. EKS → Access → Pod Identity associations: namespace `kube-system`, ServiceAccount `aws-load-balancer-controller`, role trên. Policy lấy từ release controller, không dùng `AdministratorAccess`.

AWS Console không cung cấp trình soạn đầy đủ mọi Kubernetes resource. Vì vậy cài Helm chart và tạo Ingress bằng CLI là bước cần thiết.

## Bước 2: cài controller và tạo Ingress

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

![ALB được controller tạo trên AWS](/images/console-alb.png "① ALB eks-did-notes có trạng thái Active, loại Application và scheme internet-facing.")

```bash
kubectl get ingress -n notes --watch
# Khi ADDRESS có hostname ALB, dừng watch bằng Ctrl-C.
python3 scripts/publish-dns.py
```

## Kiểm tra tài nguyên controller đã tạo

### Đối chiếu Ingress với tài nguyên AWS

EC2 Console phải thấy ALB và target group do controller quản lý; `curl https://$APP_HOST/` phải thành công sau khi DNS cập nhật. Nếu chưa có ALB, xem controller logs và events trước khi kiểm tra app. Không sửa ALB thủ công để “fix” cấu hình mà controller sẽ reconcile lại.

Quyền sửa Ingress cũng có thể thay đổi tài nguyên AWS. Lab không dùng shared IngressGroup; chỉ admin lab được tạo/sửa Ingress. IAM policy phiên bản được lưu tại [controller-policy.json](/source/terraform/controller-policy.json).

Đối chiếu hostname trong `kubectl get ingress -n notes` với DNS name của ALB trên Console. ALB phải Active, targets healthy và domain ứng dụng trả HTTP 200. Ba trạng thái này phân biệt việc controller đã tạo hạ tầng với việc backend thực sự phục vụ request.
''')
page(2,6,'target-types','ALB Target Types: Instance vs IP',r'''
Target group của ALB có thể đăng ký EC2 instance hoặc địa chỉ IP. Lựa chọn này thay đổi đường đi của request và cách cấu hình backend. Bài này so sánh hai cơ chế, sử dụng IP targets và kiểm tra việc cập nhật targets khi frontend được rollout.

## Hai cách ALB chọn backend

| | Instance target | IP target — đường chính của lab |
|---|---|---|
| Target đăng ký | EC2 instance ID | Pod IP |
| Cổng nhận | NodePort | Container/target port 8080 |
| Data path | ALB → node → Service routing → pod | ALB → pod IP |
| Khi phù hợp | Thiết kế node targets/NodePort; pod network không trực tiếp routable từ ALB | VPC CNI và pod IP được ALB định tuyến tới; Fargate cũng yêu cầu IP targets |
| Cần quan sát | NodePort, kube-proxy/routing, node SG | EndpointSlice, pod readiness, target health, pod IP |

Lab chọn `ip` vì private pod IP của VPC CNI đã routable trong VPC, tránh bước NodePort không cần thiết. Đây là lựa chọn phù hợp kiến trúc hiện tại, không phải khẳng định instance mode luôn sai.

## Bước 1: xem target group trên AWS Console

EC2 → Target Groups → chọn target group của `eks-did-notes`. Target type phải `IP`, port 8080. EKS → Pods → frontend phải có các IP trùng với targets. Trong rollout có thể thấy IP cũ đang draining và IP mới đang đăng ký.

![IP targets và trạng thái health](/images/console-targets.png "① IP target type. ② HTTP:8080. ③ Healthy targets. ④ Registered pod IPs.")

## Kiểm tra pod IP và hành vi khi rollout

### Đối chiếu targets với pod IPs

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
Frontend cần gọi API ổn định dù pod API có thể được thay thế sau mỗi lần triển khai. Bài này xác định quan hệ giữa Pod, Service và EndpointSlice, đồng thời xem namespace tạo ra những ranh giới nào trong cluster.

## Pod IP, Service và namespace trong Notes

Pod là đơn vị chạy container, thường có IP riêng. Deployment có thể thay pod khi rollout, nên không hardcode pod IP trong Nginx. Service chọn pods bằng label; EndpointSlice thể hiện danh sách endpoints. Namespace nhóm resources và là phạm vi của nhiều policy, nhưng không tự tạo network isolation.

## Bước 1: xem workloads và Services

EKS → cluster → Resources → Workloads → Deployments: frontend và API có hai replicas, worker có một. Trong Service and networking, hai Service `frontend`/`api` đều là ClusterIP. Worker không cần Service vì chỉ chủ động long-poll SQS.

## Kiểm tra Service tìm đúng pod

### Đối chiếu Service selectors với endpoints

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

Đối chiếu selector `app: api`, labels của API pods và addresses trong EndpointSlice. Lệnh gọi health từ frontend trả JSON `workload: api` xác nhận DNS nội bộ và đường Service → pod cùng hoạt động.
''')
page(3,2,'networkpolicy','Network Segmentation với Kubernetes NetworkPolicy',r'''
Frontend cần gọi API, nhưng một pod không thuộc ứng dụng không cần kết nối đó. Khi chưa có NetworkPolicy, hai pod có thể đều truy cập API. Bài này kiểm tra trạng thái ban đầu rồi giới hạn kết nối, đồng thời giữ nguyên chức năng lưu ghi chú và tạo báo cáo.

## NetworkPolicy cho phép những kết nối nào?

NetworkPolicy chọn pod bằng labels và khai báo các kết nối ingress hoặc egress được phép. Khi một pod đã được cô lập ở một chiều, lưu lượng thuộc chiều đó phải khớp ít nhất một allow rule. Các policies cộng dồn; một policy cho phép quá rộng có thể làm mất giới hạn mong muốn. Policy agent đã được bật ở [bước chuẩn bị EKS](/preparation/3-eks/). Nếu dùng cluster có sẵn, kiểm tra cấu hình theo [bài 3.3](/3-kubernetes-security/3-vpc-cni/) trước khi áp dụng policy.

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

## Bước 1: ghi nhận kết nối trước khi áp dụng policy

Mở EKS Resources để xem labels của frontend và API. Trong terminal, xác nhận ứng dụng đã hoạt động và namespace chưa có NetworkPolicy từ một lượt thực hành trước:

```bash
source scripts/env.sh
kubectl get networkpolicy -n notes
python3 scripts/network-proof.py --stage before
```

Script tạo hai pod thử nghiệm tuân thủ Restricted, dùng cùng image đã triển khai nhưng mang labels khác nhau. Khi chưa có policy, frontend và pod `untrusted` đều kết nối được đến API. Script cũng kiểm tra lưu ghi chú và tạo báo cáo, sau đó xóa các probe pods.

Nếu policy đã tồn tại, script dừng để tránh ghi nhận sai baseline. Khi thực hành lại trên lab đã harden, dùng phần kiểm chứng sau policy; không cần xóa policy đang bảo vệ ứng dụng.

## Bước 2: áp dụng NetworkPolicy

Khi baseline ứng dụng đã hoạt động và policy agent đã được bật:

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

## So sánh kết nối trước và sau policy

### So sánh với baseline

```bash
python3 scripts/network-proof.py --stage after
```

Phép thử sau policy dùng IP Service cho negative connectivity để phân biệt lỗi DNS với kết nối bị chặn. Frontend phải gọi API được; untrusted pod gọi API và frontend gọi RDS phải timeout. Positive API → RDS phải thành công để chứng minh DB đang sẵn sàng.

### Phạm vi của các rule egress

Egress HTTPS public hiện cho phép nhiều endpoint hơn SQS. Standard NetworkPolicy không có native FQDN/HTTP authorization; dùng IAM giới hạn một queue, thêm VPC Endpoint policies hoặc giải pháp egress phù hợp nếu cần siết theo dịch vụ. Các rule của lab chưa giới hạn được mọi đường đưa dữ liệu ra ngoài.


| Phép thử | Trước policy | Sau policy |
|---|---|---|
| Frontend → API | Kết nối được | Kết nối được |
| Pod không liên quan → API | Kết nối được | Bị chặn |
| Frontend → RDS | Chưa giới hạn theo pod | Bị chặn |
| Lưu ghi chú và tạo báo cáo | Hoạt động | Hoạt động |

[Báo cáo kiểm chứng sau policy trên AWS](/evidence/network-proof-after.json) ghi lại kết quả của 5 phép thử thực tế.

Các dòng baseline thể hiện kết quả cần quan sát khi chưa có policy. Script `--stage before` kiểm tra hai kết nối đến API và luồng nghiệp vụ; script `--stage after` kiểm tra thêm frontend → RDS. Một timeout chỉ có ý nghĩa khi phép thử kết nối hợp lệ và luồng ứng dụng cùng thành công.
''')
page(3,3,'vpc-cni','NetworkPolicy Enforcement với Amazon VPC CNI',r'''
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
''')
page(3,4,'pod-security','Pod Security Standards & Pod Security Admission',r'''
Một manifest có thể yêu cầu chạy container bằng root hoặc cấp quyền Linux không cần thiết. Bài này đặt chuẩn Restricted cho namespace ứng dụng để từ chối cấu hình không phù hợp ngay khi tạo pod.

## Restricted kiểm tra cấu hình gì?

Pod Security Standards có ba mức Privileged, Baseline và Restricted. Pod Security Admission (PSA) thực thi theo namespace labels. Nó không scan lỗ hổng trong image hoặc kiểm tra HTTP request.

## Bước 1: quan sát cấu hình hiện tại

EKS → Resources → Namespaces → `notes`: quan sát labels. AWS Console có thể không hỗ trợ chỉnh tất cả labels; dùng Kubernetes API cho thay đổi sau.

## Bước 2: áp dụng Restricted cho namespace

```bash
kubectl label namespace notes \
  pod-security.kubernetes.io/enforce=restricted \
  pod-security.kubernetes.io/enforce-version=v1.35 \
  pod-security.kubernetes.io/audit=restricted \
  pod-security.kubernetes.io/warn=restricted --overwrite
```

Pin version giúp việc upgrade chuẩn Restricted được review thay vì đổi ngầm. Không áp dụng Restricted lên `kube-system` tùy tiện: CNI và một số add-on cần quyền hệ thống.

## Thử pod bị từ chối và workload hợp lệ

### Thử manifest không đáp ứng Restricted

```bash
kubectl run psa-negative -n notes --image=nginx:1.28-alpine \
  --dry-run=server -o yaml
```

Pod mặc định thiếu cấu hình Restricted nên admission phải từ chối, giải thích `runAsNonRoot`, seccomp/capabilities. `--dry-run=server` chạy admission nhưng không lưu pod. Test không bypass admission hoặc chạy host mount.

### Kiểm tra workload hợp lệ

```bash
kubectl get pods -n notes
kubectl get deployment api -n notes -o jsonpath='{.spec.template.spec.securityContext}'
```

Workloads hợp lệ vẫn Running/Ready sau rollout. Label PSA không đuổi mọi pod đang chạy; cần review/redeploy workload để chứng minh pod template đáp ứng chuẩn.

Trong manifest lab, `securityContext` do `render.py` tạo, tách pod-level và container-level settings. Bài tiếp theo giải thích ý nghĩa của từng trường thay vì chỉ copy YAML.
''')
page(3,5,'securitycontext','Container Hardening với SecurityContext',r'''
Các workload cần đáp ứng chuẩn Restricted và vẫn phục vụ ứng dụng bình thường. Bài này cấu hình quyền thực thi tối thiểu cho container, xác định nơi được ghi file và kiểm tra các giới hạn ngay trong runtime.

## Giảm quyền thực thi của container

Nếu ứng dụng bị thực thi code ngoài ý muốn, container không nên tự có quyền root hoặc ghi tùy ý vào root filesystem. Các trường cấu hình dưới đây được áp dụng ở pod hoặc container theo phạm vi tương ứng.

`runAsNonRoot` yêu cầu UID không phải root. `allowPrivilegeEscalation: false` hạn chế tăng quyền qua cơ chế như setuid; không phải sandbox tuyệt đối. `RuntimeDefault` áp dụng seccomp runtime. Bỏ capabilities giảm quyền Linux không cần thiết.

## Bước 1: cấu hình pod và container

Trong `k8s/application.yaml`, đối chiếu `spec.template.spec.securityContext` và `containers[].securityContext` của API với các trường sau:

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

Đây là một phần của Pod spec. Manifest đầy đủ do `scripts/render.py` tạo đã bao gồm các trường này cho ứng dụng lab. Khi thay đổi pod template, áp dụng lại và chờ rollout hoàn tất:

```bash
kubectl apply -f k8s/application.yaml
kubectl rollout status deployment/api -n notes
```

## Bước 2: ứng dụng cần ghi file ở đâu?

Nginx cần PID/temp directories. Lab dùng image unprivileged, listen 8080 và mount `emptyDir` có giới hạn tại `/tmp`; cấu hình đưa PID/cache paths đến đó. Không mở writable toàn root filesystem chỉ để hết lỗi.

Python tắt bytecode writes và đọc CA bundle đã có trong image. Resource requests/limits giới hạn ngân sách CPU/RAM, nhưng không phải cơ chế chống mọi kiểu DoS.

Nguồn: [Dockerfile](/source/app/Dockerfile), [render.py](/source/scripts/render.py). Non-root/Restricted không thay thế cập nhật dependencies hoặc application authorization.

## Kiểm tra quyền bên trong container

### Kiểm tra quyền thực thi trong container

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


''')
page(3,6,'node-imds','Worker Node Security và IMDSv2',r'''
Worker node có IAM role để vận hành EKS. Nếu application pod lấy được credentials của node qua IMDS, nó có thể sử dụng quyền ngoài role được cấp riêng. Bài này cấu hình metadata options và kiểm tra truy cập IMDS từ pod thông thường.

## Vì sao cần giới hạn IMDS?

EC2 Instance Metadata Service (IMDS) cung cấp thông tin instance và credentials tạm thời của instance role qua địa chỉ `169.254.169.254`. IMDSv2 yêu cầu lấy session token trước khi truy cập metadata. Cấu hình response hop limit giới hạn số network hops của phản hồi lấy token.

Node role cần pull image và thực hiện chức năng EKS. Quyền SQS/RDS của ứng dụng không nên gắn lên role này. Nếu pod lấy được node credentials qua EC2 IMDS, việc cấp role riêng theo workload có thể bị suy yếu.

## Bước 1: cấu hình metadata options trong launch template

1. EC2 → Launch templates → template node lab → Advanced details → Metadata options.

2. Metadata accessible: enabled; **IMDSv2 required**, response hop limit **1**.

3. Không mở SSH từ Internet, EBS encrypted. CNI role riêng cho `aws-node`, không bắt CNI pod phụ thuộc metadata hop 1.

4. EKS node group dùng đúng template version. Sửa launch template không tự cập nhật mọi node cũ; rollout node group có kiểm soát.

## Kiểm tra metadata options và truy cập từ pod

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
''')
page(4,1,'authentication-authorization','Authentication vs Authorization',r'''
Người vận hành dùng kubectl, trong khi API và worker gọi AWS services. Các hoạt động này đi qua những hệ thống xác thực và phân quyền khác nhau. Bài này phân biệt các bước đó để xác định đúng lớp kiểm soát khi một request được cho phép hoặc bị từ chối.

## Hai quyết định trong một lần truy cập

Authentication xác định chủ thể; authorization quyết định chủ thể được phép làm hành động nào với resource nào. Hai câu hỏi xuất hiện ở cả Kubernetes, AWS API và database, nhưng do các hệ thống khác nhau trả lời.

| Hành động | Xác thực | Phân quyền |
|---|---|---|
| Người vận hành chạy `kubectl get pods` | EKS IAM authentication | EKS access policy / Kubernetes RBAC |
| API gửi SQS message | AWS temporary credentials | IAM và queue resource policy |
| API ghi vào RDS | IAM DB token | `rds-db:connect` và PostgreSQL grants |
| Người dùng đọc ghi chú | Chưa có trong app demo | Chưa có; không dùng app cho dữ liệu nhạy cảm |

## Bước 1: đối chiếu các danh tính

Mở IAM role của API trong IAM Console và Access Entry của observer trong EKS Console. Sau đó thực hiện các lệnh ở phần kiểm chứng để phân biệt danh tính terminal với quyền Kubernetes.

## Kiểm tra danh tính và quyền tương ứng

### Quan sát danh tính và quyền truy cập

Trong terminal của người quản trị, chạy:

```bash
aws sts get-caller-identity
kubectl auth can-i list pods -n notes
kubectl auth can-i get secrets -n notes
```

Với admin hiện tại, câu trả lời có thể đều `yes`; điều đó không chứng minh observer được hạn chế. Bài 4.4 sẽ dùng credentials của observer thật để thử lại.

### Khi nào bị từ chối ở đâu?

Network timeout không phải `AccessDenied`. Kubernetes trả `Forbidden` khi đã nhận request nhưng principal không có permission cần thiết. AWS trả authorization error khi request được xử lý nhưng thiếu quyền hoặc có explicit deny. PostgreSQL có thể chấp nhận kết nối nhưng từ chối một câu SQL.

Terraform tạo role và access entry; YAML Role/RoleBinding quy định Kubernetes verbs. Không dùng NetworkPolicy để giải quyết lỗi `sqs:SendMessage AccessDenied`, cũng không thêm IAM policy để chữa một connection timeout. Phân biệt các kết quả này giúp xác định lớp kiểm soát cần kiểm tra.

Lệnh `get-caller-identity` xác định AWS principal của terminal. `kubectl auth can-i` trả lời quyền Kubernetes của danh tính đang dùng. Giữ kết quả của admin để đối chiếu với role observer ở bài 4.4; không dùng quyền admin làm bằng chứng cho quyền của observer.
''')
page(4,2,'endpoint','EKS API Endpoint Security',r'''
Website cần public, nhưng endpoint quản trị Kubernetes chỉ cần phục vụ các nguồn được phép. Bài này giới hạn public access CIDRs của EKS API và giữ private access cho các thành phần trong VPC.

## Đường mạng đến Kubernetes API

![Đường quản trị EKS](/images/human-access.svg)

ALB public phục vụ website. EKS API endpoint phục vụ Kubernetes API. Một người có thể mở website nhưng không kết nối được endpoint quản trị; một người đến được endpoint vẫn phải qua authentication/authorization.

### Giới hạn nguồn truy cập EKS API (tùy chọn)

EKS → cluster → Configuration → Networking → Manage → endpoint access (giao diện cũ: Networking → Manage endpoint access). Lab chọn Public and private, public CIDRs = IP workstation `/32`. Nodes/controller dùng private endpoint trong VPC. Không mở `0.0.0.0/0` để xử lý lỗi từ workstation.

Thiết kế production có VPN/private connectivity có thể dùng private-only. Đánh đổi: người học từ Internet cần một đường quản trị vào VPC, không thể chỉ chạy kubectl từ bất kỳ đâu.

![Endpoint access và public CIDR allowlist](/images/console-eks-endpoint.png "① EKS API endpoint access. ② Public access source allowlist.")

Lab bật public và private access, đồng thời giới hạn public endpoint bằng CIDR quản trị. Dùng IP workstation của bạn thay cho IP trong ảnh.

## Bước 1: cập nhật IP quản trị khi cần

Nếu IP workstation đổi, cập nhật **đúng IP mới**:

```bash
ADMIN_IP=$(curl -fsS https://checkip.amazonaws.com)
aws eks update-cluster-config --name eks-did \
  --resources-vpc-config "endpointPublicAccess=true,endpointPrivateAccess=true,publicAccessCidrs=$ADMIN_IP/32"
```

Chỉ dùng API nếu đó là đường quản lý bạn chọn. Với Terraform, sửa `admin_cidr`, plan rồi apply để tránh drift. Giữ kết nối quản trị đang hoạt động và đợi update hoàn tất trước khi thử context mới.

## Kiểm tra endpoint access và CIDR

### Đọc endpoint configuration và cập nhật CIDR

```bash
aws eks describe-cluster --name eks-did \
  --query 'cluster.resourcesVpcConfig.{public:endpointPublicAccess,private:endpointPrivateAccess,cidrs:publicAccessCidrs}'
curl -fsS https://checkip.amazonaws.com
```


`kubectl get nodes` từ workstation được cho phép phải thành công. Đọc public CIDR từ API để xác nhận không có mạng rộng ngoài dự kiến. Workshop không dùng một timeout từ mạng chưa biết để tuyên bố đã kiểm chứng private-only; giới hạn test được ghi trong validation.
''')
page(4,3,'human-access','Human Access: AWS IAM & EKS Access Entries',r'''
Một người cần xem trạng thái ứng dụng mà không có quyền quản trị cluster. Bài này tạo IAM role observer và đưa danh tính đó vào EKS qua Access Entry; quyền Kubernetes cụ thể sẽ được cấu hình ở bài RBAC.

## Từ IAM principal đến danh tính Kubernetes

Lab dùng role `eks-did-observer`, access entry map vào group `notes-observers`. Group được bind vào Role chỉ đọc của namespace `notes`. Không associate thêm policy admin cho role này.

## Bước 1: tạo IAM role và Access Entry

1. IAM → Roles → Create role → Custom trust policy. Cho phép **IAM principal quản trị lab của bạn** `sts:AssumeRole`; không dùng wildcard principal hoặc hardcode principal của account ví dụ.

2. Đặt `eks-did-observer`. Identity policy chỉ cần `eks:DescribeCluster` cho ARN cluster `eks-did` để lấy endpoint/config. Kubernetes verbs không nằm trong policy này.

3. EKS → cluster → Access → Create access entry: chọn role ARN, type Standard, Kubernetes group `notes-observers`.

4. Không associate `AmazonEKSClusterAdminPolicy`. Bài tiếp theo tạo RoleBinding.

![Observer Access Entry trên EKS](/images/console-observer-access.png "① Observer role. ② Group notes-observers. ③ Cột access policies.")

Dòng observer sử dụng Kubernetes group và không có EKS access policy admin. Những entries khác trong ảnh thuộc node, add-on hoặc danh tính quản trị của lab.

### Tạo Access Entry qua API (tùy chọn)

Nếu tạo bằng API thay Console, sau khi role tồn tại:

```bash
aws eks create-access-entry --cluster-name eks-did \
  --principal-arn "$OBSERVER_ARN" --type STANDARD --kubernetes-groups notes-observers
```

Không tạo trùng entry đã có. Terraform chứa `aws_iam_role.observer`, `aws_eks_access_entry.observer` tại [data-services.tf](/source/terraform/data-services.tf).

## Kiểm tra Access Entry và các nguồn cấp quyền

### Đối chiếu Access Entry và access policies

```bash
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
OBSERVER_ARN="arn:aws:iam::$ACCOUNT_ID:role/eks-did-observer"
aws eks list-access-entries --cluster-name eks-did
aws eks describe-access-entry --cluster-name eks-did --principal-arn "$OBSERVER_ARN"
aws eks list-associated-access-policies --cluster-name eks-did --principal-arn "$OBSERVER_ARN"
```


### Kiểm tra các nguồn cấp quyền

EKS access policies và RBAC có thể cùng cấp quyền. RoleBinding read-only không thu hồi quyền admin từ một access policy khác. Kiểm tra cả hai trước khi kết luận observer bị hạn chế. Không xóa bootstrap/admin hiện tại trước khi identity thay thế đã đăng nhập và thực hiện đủ quyền quản trị cần thiết.

Access Entry phải chứa đúng observer role và group `notes-observers`. Danh sách associated access policies của observer phải rỗng trong thiết kế lab. Bài 4.4 tiếp tục tạo RoleBinding và dùng chính role này để kiểm tra quyền đọc và quyền bị từ chối.
''')
page(4,4,'rbac','Kubernetes RBAC: Role, ClusterRole và Bindings',r'''
Role observer đã được EKS nhận diện, nhưng vẫn cần quy định những tài nguyên và thao tác được phép. Bài này cấp quyền đọc workload trong namespace notes và kiểm tra bằng credentials thật của observer.

## Quyền đọc trong một namespace

Role có phạm vi namespace. ClusterRole có thể dùng cho cluster-scoped resources hoặc tái sử dụng qua RoleBinding. RoleBinding cấp quyền trong namespace; ClusterRoleBinding có phạm vi toàn cluster. Các quyền được cộng dồn, không có deny Role để hủy allow khác.

## Bước 1: tạo Role và RoleBinding

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

Lưu Role trên vào `.local/observer-rbac.yaml` và bổ sung RoleBinding:

```yaml
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: observer
  namespace: notes
subjects:
  - kind: Group
    name: notes-observers
    apiGroup: rbac.authorization.k8s.io
roleRef:
  kind: Role
  name: observer
  apiGroup: rbac.authorization.k8s.io
```

Áp dụng bằng danh tính admin của lab:

```bash
kubectl apply -f .local/observer-rbac.yaml
```

Các tài nguyên này cũng có trong [manifest do render.py tạo](/source/scripts/render.py). Không gắn thêm ClusterRoleBinding cho observer.

## Dùng observer thử quyền được phép và bị từ chối

### Đăng nhập bằng observer và thử quyền

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

### Các quyền có khả năng mở rộng phạm vi truy cập

`pods/exec`, đọc Secret, tạo pod với ServiceAccount khác, sửa Ingress hoặc RoleBinding có thể mang lại quyền gián tiếp đáng kể. Lab observer không có các quyền đó. Không cấp wildcard verbs/resources vì tiện demo.
''')
page(4,5,'workload-identity','Workload Identity: IRSA vs EKS Pod Identity',r'''
API cần gửi message vào SQS, còn worker cần nhận và xóa message. Hai workload cần danh tính AWS riêng mà không lưu access key trong container. Bài này so sánh IRSA với EKS Pod Identity và cấu hình association theo từng ServiceAccount.

## Pod nhận AWS credentials như thế nào?

AWS SDK sử dụng temporary credentials do cơ chế workload identity cấp. Pod Identity association liên kết cluster, namespace và ServiceAccount với một IAM role; IAM policy của role quy định thao tác AWS được phép. IRSA thực hiện liên kết bằng OIDC trust và ServiceAccount annotation.

![Cấp temporary credentials theo workload](/images/workload-identity.svg)

| | IRSA | EKS Pod Identity — app của lab |
|---|---|---|
| Liên kết | OIDC trust + ServiceAccount annotation | EKS association namespace/ServiceAccount/role |
| Cấp credentials | STS AssumeRoleWithWebIdentity | Agent + EKS Auth + SDK credential provider |
| Khi chọn | Cấu hình hiện có, môi trường/compute cần IRSA | EKS compute được hỗ trợ, muốn quản lý association qua EKS |
| Dependency | OIDC provider, STS, SDK | Agent, EKS Auth, SDK tương thích |

Lab dùng Pod Identity cho API, worker, db-init và controller. VPC CNI dùng IRSA riêng để bootstrap mạng không phụ thuộc node IMDS. Không gán đồng thời hai cơ chế cho cùng một workload rồi đoán SDK dùng cái nào.

Các tài nguyên này đã được dựng trong [phần chuẩn bị lab](/preparation/6-workload-permissions/). Đối chiếu cấu hình hiện có theo các bước dưới đây; chỉ tạo mới nếu tài nguyên tương ứng chưa tồn tại.

## Bước 1: tạo trust policy và Pod Identity associations

1. EKS → Add-ons: Pod Identity Agent `ACTIVE` trên managed nodes.

2. IAM → tạo các role `eks-did-api`, `eks-did-worker`, `eks-did-db-init`, `eks-did-controller`.

3. Trust service principal `pods.eks.amazonaws.com`, actions `sts:AssumeRole`, `sts:TagSession`. Dùng điều kiện session tags giới hạn namespace/ServiceAccount như [data-services.tf](/source/terraform/data-services.tf).

![Trust policy của API role](/images/console-api-trust.png "① pods.eks.amazonaws.com. ② sts:AssumeRole. ③ sts:TagSession.")

Phần Condition phía dưới giới hạn namespace `notes` và ServiceAccount `api`. Trust policy xác định bên được assume role; permissions policy xác định role được gọi AWS API nào.

4. EKS → Access → Pod Identity associations: namespace `notes`, ServiceAccount tương ứng `api`, `worker`, `db-init`; controller là `kube-system/aws-load-balancer-controller`.

![Pod Identity associations của ứng dụng](/images/console-pod-identity.png "① Namespace notes. ② ServiceAccount api. ③ ServiceAccount worker.")

Đọc cùng hàng từ IAM role đến namespace và ServiceAccount để kiểm tra association. API và worker sử dụng role khác nhau dù cùng namespace.

5. Gắn identity policies theo 4.6. Association có thể tạo trước ServiceAccount nhưng workload chỉ chạy đúng khi cả hai có mặt.

### Đọc association qua EKS API (tùy chọn)

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

## Kiểm tra AWS role thực tế trong pod

### Xác nhận IAM role bên trong pod

```bash
kubectl exec -n notes deployment/api -- python -c \
  'import boto3; print(boto3.client("sts").get_caller_identity()["Arn"])'
```

ARN phải là assumed role `eks-did-api`, không phải node role. Egress phải cho agent `169.254.170.23:80` và AWS APIs cần thiết. `automountServiceAccountToken: false` tắt token Kubernetes API mặc định; Pod Identity vẫn có projected token riêng do EKS cấp, không mâu thuẫn với cấu hình đó.

ARN trả về phải chứa `assumed-role/eks-did-api/`, không phải node role. Association trên Console và ARN quan sát bên trong pod cung cấp hai bằng chứng: cấu hình liên kết đúng và ứng dụng thực sự nhận đúng danh tính.
''')
page(4,6,'least-privilege','Least Privilege và IAM Policies',r'''
Có IAM role riêng chưa bảo đảm workload chỉ thực hiện đúng công việc được giao. Bài này giới hạn action và resource của từng role, kết hợp quyền IAM database authentication với SQL grants trong PostgreSQL.

## Quyền được tách theo nhiệm vụ

| Identity | Quyền AWS | Quyền SQL |
|---|---|---|
| Frontend | Không có role ứng dụng | Không có user DB |
| API | `sqs:SendMessage` trên queue lab; `rds-db:connect` cho `notes_api` | Insert/select notes, select reports |
| Worker | Receive/Delete/GetQueueAttributes trên queue lab; connect `notes_worker` | Select notes, insert/select reports |
| db-init | GetSecretValue đúng RDS master secret | Bootstrap schema/users; job kết thúc sau khởi tạo |
| Controller | Policy ELB controller release đã pin | Không có |

## Bước 1: giới hạn IAM actions và resources

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

## So sánh thao tác nghiệp vụ với thao tác vượt quyền

### Thử luồng nghiệp vụ và thao tác vượt quyền

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
Image đã build và chạy được vẫn có thể chứa dependency có lỗ hổng đã biết. Bài này bật scanning, đọc kết quả của đúng image digest và thực hiện kiểm tra điều kiện phát hành trước khi chấp nhận image.

## Scan đúng image đang chạy

Image scanning tìm các package/dependency có vulnerability đã biết. Kết quả cần được đánh giá theo mức độ, khả năng khai thác, bản sửa và exception có thời hạn. Scan không tự ngăn Kubernetes chạy image.

## Bước 1: cấu hình scanning cho ECR

1. ECR → Private registry → Features & Settings → Scanning: xem loại scanning đang dùng. Basic scan tập trung OS packages; enhanced scanning tích hợp Inspector, có thể theo dõi cả language packages theo khả năng hỗ trợ.

2. Inspector → Activate → ECR scanning, với quyền quản lý Inspector trong tài khoản AWS. Đây là cấu hình account/Region; review phạm vi trước khi đổi trong account dùng chung.

3. Chọn repository `eks-did/notes`, xem digest đã push và scan findings. Chờ scan hoàn tất; “không thấy findings” trong lúc pending không phải kết quả sạch.

![Image tags và digest trong ECR](/images/console-ecr-images.png "① Image digest. ② Image tags.")

Chọn đúng digest đang triển khai trước khi mở findings. Các artifacts chữ ký và image chưa ký dùng cho phép thử admission không phải kết quả scan của image ứng dụng.

4. Mở một finding, xem affected package, installed/fixed version và severity. Không đưa finding vào bài như bằng chứng exploit đã xảy ra.

## Đọc findings và quyết định của release gate

### Đọc kết quả theo image digest

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

### Kiểm tra điều kiện phát hành

```bash
python3 scripts/scan-gate.py
```

Script yêu cầu coverage đã scan, đọc findings của **đúng deployed digest**, trả exit 1 nếu có HIGH/CRITICAL hoặc chưa có coverage hoàn tất. [Kết quả scan thực tế](/evidence/image-scan.json) trong lượt lab ghi 4 HIGH, 8 MEDIUM, 2 LOW, 2 UNTRIAGED; 4 HIGH chưa có bản sửa theo Inspector. Gate trả `BLOCK`, không tự miễn trừ vì chưa có fix. Ứng dụng vẫn được dùng trong môi trường thực hành để kiểm tra network/identity; kết quả đó không phải phê duyệt release production.

Khi có bản vá, cập nhật base/dependency, build digest mới, scan lại rồi mới review gate. Đừng trộn kết quả scan image unsigned với image đang chạy.

### Cấu hình repository và scanning coverage

`aws_ecr_repository.app` bật immutable tags/basic scan; optional `aws_inspector2_enabler.ecr` bật ECR Inspector. Account có registry filters cần review để chắc repository lab nằm trong coverage. Tạo image mới với tag mới thay vì overwrite tag immutable.

Workshop ghi kết quả scan thực tế; không hứa “zero CVE”. Script gate của lab trả exit code để sử dụng trong quy trình phát hành. Việc scanning được bật riêng lẻ không tự chặn một deployment Kubernetes.

Điều kiện đạt của bài là xác định đúng deployed digest, chờ coverage hoàn tất và đọc đúng quyết định của gate. Gate `BLOCK` khi còn HIGH/CRITICAL là kết quả thực thi đúng policy; đó không phải kết luận image đã đủ điều kiện phát hành.
''')
page(5,2,'sbom-signing','SBOM, Image Signing & Admission Policies',r'''
Tag và tên repository chưa chứng minh image được tạo bởi nguồn đã tin cậy. Bài này tạo SBOM, ký image theo digest và áp dụng admission policy để kiểm tra chữ ký trước khi workload được tạo.

## Scan, SBOM và chữ ký giải quyết việc gì?

Ba thành phần phục vụ ba mục đích: SBOM liệt kê dependency; chữ ký gắn digest với public key tin cậy; admission policy kiểm tra image trước khi Kubernetes tạo workload. Image có chữ ký vẫn phải được quét lỗ hổng theo bài 5.1.

![Chuỗi source, build, ký và admission](/images/supply-chain.svg)

SBOM giúp đối chiếu các thành phần của image với kết quả scanning. Chữ ký xác minh nguồn ký và tính toàn vẹn của digest, không bảo đảm các dependency đã hết lỗ hổng.

## Bước 1: quan sát cấu hình hiện tại

ECR → repository → Images: ghi lại image digest thay vì chỉ tag. IAM/ECR permissions xác định ai có quyền push. Cấu hình signature verification là Kubernetes admission, nên phần tiếp theo cần CLI.

## Bước 2: tạo SBOM và ký image

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

## Bước 3: áp dụng admission policy

```bash
bash scripts/admission.sh
bash scripts/prepare-unsigned.sh
kubectl get clusterpolicy verify-notes-image
```

Policy giới hạn namespace `notes` và repository app lab, yêu cầu signature từ public key của workshop. Kyverno fetch manifest/signature từ private ECR bằng registry secret; secret được tạo qua stdin, không đưa vào Hugo hoặc command arguments. ECR token hết hạn sau khoảng 12 giờ: refresh bằng script trước lượt thử tiếp theo. Production nên dùng credential provider/identity được quản lý phù hợp.

**Positive test:** server-side dry-run pod Restricted dùng digest đã ký phải được chấp nhận. **Negative test:** cùng repo nhưng digest mới chưa ký phải bị webhook từ chối. `verify.py --supply-chain` thực hiện hai test sau bước `prepare-unsigned.sh`. Script build cùng source với một image label khác để có digest mới, push nhưng không ký hoặc deploy nó.

## Thử image có chữ ký và image chưa ký

### Kiểm tra phạm vi và kết quả admission

Ở chart 3.9.2 đã kiểm chứng, `ClusterPolicy` là API legacy vẫn được hỗ trợ; đánh giá migration sang `ImageValidatingPolicy` khi nâng cấp. Policy này kiểm tra image API/worker của lab, chưa bao phủ mọi repository hoặc image Nginx upstream. Không khẳng định toàn cluster chỉ chạy signed images. Webhook fail-closed tăng bảo vệ nhưng phụ thuộc availability của verifier/registry; một replica Kyverno chỉ phù hợp môi trường thực hành. Native CEL admission có thể kiểm tra digest/registry pattern, nhưng không tự xác minh Cosign signature, nên lab dùng verifier thực.

Chạy bộ kiểm tra sau khi đã hoàn thành các lớp bảo vệ của workshop:

```bash
python3 scripts/verify.py --supply-chain
```

Hai phép thử admission phải cho kết quả khác nhau: digest đã ký được chấp nhận; digest chưa ký bị từ chối với thông báo liên quan đến signature verification. Các phép thử dùng server-side dry-run nên không triển khai image chưa ký vào ứng dụng.
''')
page(5,3,'secrets','Kubernetes Secrets & AWS Secrets Manager',r'''
Database cần tài khoản có quyền cao để khởi tạo schema, nhưng API và worker không cần giữ master password trong quá trình chạy. Bài này tách quyền bootstrap khỏi quyền ứng dụng và kiểm tra việc truy cập secret.

## Secret nào được ứng dụng sử dụng?

Kubernetes Secret thường biểu diễn dữ liệu bằng Base64 khi xuất YAML. Base64 không phải encryption. Ai có quyền đọc Secret hoặc exec vào workload có secret có thể tiếp cận dữ liệu đó.

## Bước 1: xem metadata của RDS master secret

RDS → database → Configuration → Master credentials ARN → mở Secrets Manager. Kiểm tra encryption key và access policy. Không bấm hiển thị password để chụp ảnh đưa lên workshop.

Lab chỉ cấp `GetSecretValue` trên ARN này cho role `eks-did-db-init`. Job khởi tạo schema và hai user `notes_api`, `notes_worker`, cấp `rds_iam` và SQL grants tối thiểu. API/worker không đọc master password; SDK ký IAM DB auth token ngắn hạn khi mở connection, kết hợp TLS verify-full.

![RDS IAM authentication và master credentials](/images/console-rds.png "① Database Available. ② IAM authentication Enabled. Master credentials do Secrets Manager quản lý.")

Chỉ quan sát trạng thái và ARN của secret. Ảnh không hiển thị giá trị mật khẩu database.

## Kiểm tra metadata và quyền đọc secret

### Kiểm tra secret metadata và bootstrap job

```bash
aws secretsmanager describe-secret --secret-id "$DB_SECRET_ARN" \
  --query '{arn:ARN,rotation:RotationEnabled,key:KmsKeyId}'
kubectl get job db-init -n notes
kubectl logs job/db-init -n notes
```

Mong đợi init job hoàn tất và log không chứa password. RDS master credential rotation do dịch vụ quản lý cần được kiểm tra theo cấu hình; không suy ra chỉ từ việc secret tồn tại.

### Kiểm tra quyền truy cập master secret

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
Dữ liệu của ứng dụng tồn tại trên nhiều dịch vụ, mỗi dịch vụ có cấu hình mã hóa riêng. Bài này xác định từng ranh giới mã hóa và thực hành KMS để kiểm tra quan hệ giữa ciphertext, quyền sử dụng key và encryption context.

## Mã hóa dữ liệu và quyền sử dụng key

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

## Bước 1: tạo KMS key và đối chiếu cấu hình dịch vụ

KMS → Customer managed keys → Create symmetric Encrypt/Decrypt key → alias `eks-did`. Giới hạn key administrators/users vào identity lab cần thiết, bật rotation. Terraform tạo `aws_kms_key.lab` và alias, tùy chọn tắt nếu SCP không cho.

RDS → Configuration kiểm tra storage encrypted và KMS key ID. ECR và SQS có cấu hình riêng; đối chiếu key và cơ chế mã hóa của từng dịch vụ.

![Encryption và IAM authentication của RDS](/images/console-rds-encryption.png "① Storage encryption. ② AWS KMS key. ③ IAM DB authentication.")

Key `aws/rds` bảo vệ storage của RDS. IAM database authentication là cơ chế xác thực kết nối; không thay thế storage encryption hoặc quyền SQL.

![Cơ chế mã hóa của queue SQS](/images/console-sqs-encryption.png "① Encryption. ② Amazon SQS key (SSE-SQS).")

Queue dùng SSE-SQS, độc lập với customer managed KMS key sẽ thực hành bên dưới.

## Bước 2: mã hóa và giải mã dữ liệu thử nghiệm

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

`cmp` trả exit code 0 khi dữ liệu giải mã trùng plaintext. Encryption context là additional authenticated data (AAD), được ràng buộc với ciphertext nhưng không phải dữ liệu bí mật. Phần kiểm chứng tiếp theo thay context để quan sát kết quả từ chối.

## Thử giải mã với đúng và sai encryption context

### Kiểm tra encryption context và vòng đời key

At-rest encryption không chặn principal được cấp quyền hợp lệ đọc plaintext qua API. KMS policy, IAM và resource permissions vẫn quan trọng. Khi teardown, CMK được schedule deletion sau 7 ngày, không biến mất ngay; xem trạng thái PendingDeletion. Không xóa key bảo vệ dữ liệu còn cần khôi phục.

Thử giải mã lại ciphertext với context khác:

```bash
aws kms decrypt --ciphertext-blob fileb://.local/ciphertext.bin \
  --encryption-context Workshop=other \
  --query Plaintext --output text
```

Lệnh phải thất bại với `InvalidCiphertextException`. Lần giải mã đúng context cho file trùng plaintext (`cmp` exit 0); lần sai context bị từ chối chứng minh ciphertext được ràng buộc với encryption context.
''')
write(Path('cleanup'),'Cleanup: gỡ lab đúng thứ tự',90,r'''
## Đóng website không dừng tính phí

Chạy cleanup trong đúng account/profile. Lab dùng prefix `eks-did` và kubeconfig riêng; không xóa VPC/default resources hoặc dịch vụ của người khác.

### Console: những tài nguyên cần gỡ

1. EKS/Kubernetes: xóa Ingress trước, đợi controller xóa ALB, target groups và SG do nó quản lý. Sau đó gỡ namespace app, Kyverno và controller.

2. Route 53: xóa **record ứng dụng `notes`**, giữ lại public hosted zone đang sử dụng.

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
write(Path('validation'),'Kiểm chứng và kết quả thực hành',80,r'''
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
write(Path('summary'),'Tổng kết: các lớp bảo vệ đã kiểm chứng',70,r'''
Notes bắt đầu từ một đường truy cập HTTPS hoạt động. Sau các bài thực hành, đường truy cập đó được kiểm tra ở nhiều ranh giới: ALB và VPC, kết nối giữa pod, quyền thực thi container, danh tính người dùng/workload và dữ liệu mà ứng dụng sử dụng.

## Đối chiếu bằng chứng của bạn

| Câu hỏi | Phép thử cần đối chiếu | Bằng chứng cần có |
|---|---|---|
| Request có đến đúng frontend không? | Bài 2.1 và 2.6 | ALB target IP trùng pod IP; HTTPS trả 200 |
| WAF có tham gia xử lý request không? | Bài 2.3 | Request thường trả 200; header thử trả 403 |
| Pod không liên quan có gọi API được không? | Bài 3.2 | Kết nối bị chặn sau policy; frontend vẫn gọi API |
| Container có được chạy tùy ý không? | Bài 3.4–3.5 | Pod không đạt Restricted bị từ chối; ứng dụng chạy non-root |
| Application pod có lấy được quyền node không? | Bài 3.6 | IMDSv2 required/hop limit 1; kiểm tra truy cập IMDS từ pod bị chặn trong cấu hình lab |
| Observer có sửa được workload không? | Bài 4.4 | Đọc được namespace notes; thao tác sửa và truy cập ngoài phạm vi bị từ chối |
| API/worker có đúng AWS role không? | Bài 4.5–4.6 | Đúng role; luồng SQS cần thiết hoạt động và thao tác vượt quyền bị từ chối |
| Image có đủ điều kiện phát hành không? | Bài 5.1 | Đọc findings theo đúng digest và quyết định riêng của scan gate |
| Admission có chặn image chưa ký không? | Bài 5.2 | Image hợp lệ được chấp nhận; image thử chưa ký bị từ chối trong phạm vi policy |
| Secret và KMS có được kiểm soát không? | Bài 5.3–5.4 | Role không cần master secret bị từ chối; sai encryption context không giải mã được |

Các ô trên là điều kiện cần kiểm tra, không phải kết quả tự động đạt. [Báo cáo lab tham chiếu](/validation/results/) và [kết quả NetworkPolicy](/evidence/network-proof-after.json) ghi riêng những phép thử đã chạy. So sánh với output của môi trường bạn thực hành.

## Ứng dụng cần tiếp tục hoạt động

Sau khi giới hạn network và permissions, chạy lại hai thao tác từ [baseline](/preparation/8-baseline/): tạo/đọc ghi chú và gửi/nhận báo cáo. Chỉ nhìn thấy timeout hoặc AccessDenied chưa đủ: thao tác đúng quyền và kết nối hợp lệ cũng cần thành công.

Bộ kiểm tra tổng hợp được mô tả ở [Kiểm chứng](/validation/). Chỉ dùng lựa chọn `--supply-chain` sau khi hoàn thành các bước signing/admission tương ứng.

## Những giới hạn cần mang theo

HTTPS kết thúc tại ALB; frontend và API sử dụng HTTP nội bộ trong cấu hình lab. Security Groups và NetworkPolicy kiểm soát kết nối, không thay thế TLS khi có yêu cầu mã hóa các chặng này.

Một NAT Gateway, RDS Single-AZ và một replica controller/admission là các lựa chọn giảm chi phí thực hành; cần đánh giá lại availability khi thiết kế hệ thống sử dụng thực tế. Policy ký image chỉ bao phủ các image/repository được nêu trong bài.

[Kết quả scan tham chiếu](/evidence/image-scan.json) ghi nhận 4 HIGH chưa có bản sửa và gate **BLOCK**. Việc các kiểm tra chức năng và phân quyền đạt không phê duyệt image đó để phát hành.

## Kết thúc thực hành

Lưu lại output cần đối chiếu, sau đó thực hiện [Cleanup](/cleanup/) để gỡ tài nguyên. Không đưa credentials, Terraform state, kubeconfig hoặc private signing key vào báo cáo hay repository.
''')

CHAPTER_INTROS = {
1: """Notes có ba workload nhưng chỉ frontend nhận request từ Internet. API cần database và queue; worker cần xử lý message và ghi kết quả. Những khác biệt này là điểm bắt đầu để xác định lớp bảo vệ cần đặt ở đâu.

Phần này giới thiệu Defense in Depth, trách nhiệm của AWS/người triển khai và hai góc nhìn kiến trúc: luồng nghiệp vụ tổng quan, sau đó là các thành phần AWS/Kubernetes thực hiện luồng đó. Chưa cần chạy lệnh.

Sau khi đọc kiến trúc, chuyển sang [Chuẩn bị lab](/preparation/) để tạo ứng dụng trước khi lần theo request ở chương 2.""",
2: """Notes đã hoạt động qua domain HTTPS ở bước baseline. Bây giờ cần giải thích được vì sao request từ Internet đến được frontend trong private subnet, và những kết nối nào được lớp mạng AWS cho phép.

Bắt đầu từ một request thật, đối chiếu ALB target với pod IP rồi đọc ngược về subnets, routes và Security Groups. Tiếp tục kiểm tra HTTPS, WAF và cách controller quản lý backend. Các tài nguyên nền đã được tạo ở phần chuẩn bị; các bài chỉ rõ khi nào cần quan sát và khi nào cần thay đổi cấu hình.

Hoàn thành [baseline](/preparation/8-baseline/) trước bài 2.1. Cuối phần này, cần đối chiếu được cả request HTTPS trả 200 và request thử WAF trả 403. Giới hạn kết nối giữa pod được tiếp tục ở chương 3.""",
3: """Security Groups đã giới hạn kết nối ở lớp AWS, nhưng frontend và API vẫn cùng chạy trên EKS. Namespace giúp tổ chức workload; nó chưa tự ngăn một pod không liên quan gọi API.

Phần này kiểm tra kết nối trước khi áp dụng NetworkPolicy, thêm các allow rules cần thiết và chạy lại cùng phép thử. Sau đó kiểm tra cấu hình thực thi của policy, chuẩn Restricted, quyền container và đường truy cập metadata của node.

CNI policy agent đã được bật ở [bước tạo EKS](/preparation/3-eks/); bài 3.3 giải thích và đối chiếu điều kiện này. Kết quả cần đạt: frontend vẫn gọi API, Notes vẫn lưu ghi chú/tạo báo cáo, còn pod không liên quan bị chặn. Các kiểm tra PSA và SecurityContext xác nhận thêm giới hạn thực thi workload.""",
4: """Một pod kết nối được đến AWS endpoint chưa có nghĩa nó được phép thực hiện mọi API. Tương tự, người dùng có thể xác thực với AWS nhưng chưa có quyền sửa tài nguyên Kubernetes.

Phần này theo hai đường truy cập: người quản trị đến EKS API và workload đến dịch vụ AWS. Giới hạn endpoint, gắn danh tính qua Access Entries, cấp quyền đọc bằng RBAC, rồi đối chiếu Pod Identity và IAM policies của API/worker.

Các role cần để Notes hoạt động đã có từ phần chuẩn bị. Dùng danh tính observer để thử quyền thực tế và so sánh thao tác SQS hợp lệ với thao tác vượt quyền. Cuối phần, cần chỉ ra được principal nào bị từ chối và lớp nào đưa ra quyết định.""",
5: """Network và IAM đã thu hẹp đường truy cập, nhưng không trả lời image có lỗ hổng hay ai được phép lấy secret. Phần cuối chuyển từ kết nối và permissions sang đầu vào triển khai và dữ liệu mà ứng dụng sử dụng.

Scan đúng digest đang chạy, đọc release gate, tạo SBOM và chữ ký rồi thử admission bằng một image chưa ký. Tiếp theo kiểm tra master secret của RDS, quyền bootstrap và encryption context của KMS.

Kết quả scan phải được đánh giá riêng với chức năng ứng dụng: lab tham chiếu hiện có HIGH findings chưa có bản sửa và release gate trả BLOCK. Hoàn thành phần này rồi dùng [Tổng kết](/summary/) để đối chiếu toàn bộ bằng chứng trước khi cleanup.""",
}

for i,(slug,title) in enumerate(MODULES,1):
 rows=[f'{m}.{n}. [{t}]({"/"+p+"/"})' for m,n,p,t in PAGES if m==i]
 write(Path(slug),title,1 if i == 1 else i+1,CHAPTER_INTROS[i]+'\n\n## Các bài trong phần này\n\n'+'\n\n'.join(rows), f'<b>{i}.</b> ')
# Emit a navigation map for validation and future edits.
(ROOT/'evidence/content-map.json').write_text(json.dumps(PAGES,ensure_ascii=False,indent=2))
print('Generated',len(PAGES),'lessons across',len(MODULES),'modules.')
