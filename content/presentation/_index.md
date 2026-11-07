---
title: "Vietnamese presentation guide"
weight: 2
chapter: false
---

# Kịch bản 25 phút: Defense in Depth for Amazon EKS

Kịch bản này theo đúng **15 slide** trong `EKS_Defense_in_Depth_Presentation_15slides.pptx`. Mỗi mục có thời lượng gần đúng, lời thoại và gợi ý chỉ vào sơ đồ. Hãy dùng slide để chỉ hình, còn trang Hugo này để giải thích; không cần đọc nguyên văn toàn bộ chữ trên slide.

{{% notice note %}}
Phân biệt kết quả thật với kiến trúc mở rộng: lần sandbox đã kiểm tra ALB IP targets → pod IP, hai pod `web`, Service `ClusterIP`, security groups, NetworkPolicy, PSA, RBAC, Pod Identity, audit logs, Flow Logs và GuardDuty coverage. EKS API có private endpoint và public endpoint giới hạn `/32`. WAF, image signature enforcement, Route 53/domain certificate, EventBridge/SNS alert và tự động hóa response chưa triển khai. Chứng chỉ ACM của lần lab là certificate thử nghiệm. Kiểm tra sandbox còn chạy không trước khi demo trực tiếp.
{{% /notice %}}

## Slide 1 — Amazon EKS Defense in Depth · 1 phút

**Mục đích:** Nêu chủ đề, hứa hẹn một hành trình cụ thể.

**Lời thoại:**

“Xin chào mọi người. Hôm nay mình sẽ nói về cách bảo vệ một ứng dụng chạy trên Amazon EKS. Mình sẽ theo dõi request từ người dùng đến pod, xem quyền của con người và ứng dụng được tách ra sao, và khi có sự cố thì lấy bằng chứng ở đâu.

Đây là workshop thực hành trên sandbox AWS. Ứng dụng `web` chỉ để học, không xử lý thanh toán hay dữ liệu khách hàng. Mình sẽ phân biệt rõ phần đã triển khai và kiểm tra với các lựa chọn kiến trúc được đưa ra để tham khảo.”

**Chuyển ý:** “Trước hết, đây là lộ trình chúng ta sẽ đi qua.”

## Slide 2 — Agenda · 1 phút

**Mục đích:** Giới thiệu bốn nhóm kiểm soát.

**Lời thoại:**

“Có bốn nhóm. Đầu tiên là network: VPC, subnet, ALB và security group. Tiếp theo là Kubernetes: NetworkPolicy, pod security và workload. Nhóm thứ ba là identity: người dùng vào EKS API bằng quyền gì, còn pod gọi AWS bằng quyền gì. Cuối cùng là detection và response: mình thấy dấu hiệu nào, rồi làm gì tiếp.

Câu hỏi xuyên suốt là: giả sử một lớp bị cấu hình sai hoặc bị vượt qua, lớp tiếp theo có giới hạn được thiệt hại không? Ví dụ pod bị xâm nhập thì NetworkPolicy, IAM least privilege và logging có thể giảm khả năng lan rộng và giúp điều tra.”

**Chuyển ý:** “Lý do cần nhiều lớp là vì mỗi lớp chỉ giải quyết một phần rủi ro.”

## Slide 3 — Why Defense in Depth? · 1 phút 30 giây

**Mục đích:** Giải thích Prevent, Limit, Detect, Respond.

**Lời thoại:**

“Defense in Depth có thể nhớ qua bốn động từ: ngăn chặn, giới hạn, phát hiện và ứng phó.

Ngăn chặn là giảm cơ hội xảy ra sự cố, ví dụ chỉ cho phép HTTPS từ nguồn dự định. Giới hạn là nếu pod có vấn đề, nó không được tùy ý liên lạc với mọi namespace hoặc dùng quyền AWS của node. Phát hiện là ghi nhận API, network và runtime events. Ứng phó là cô lập đúng phạm vi, giữ bằng chứng, thu hồi quyền bị lộ rồi khôi phục workload sạch.

Không một công nghệ đơn lẻ làm được cả bốn việc. Private subnet không thay RBAC; scanner không tự chặn image; log không tự cách ly pod. Vì vậy mình sẽ nối từng kiểm soát với rủi ro cụ thể.”

**Chuyển ý:** “Sơ đồ tiếp theo quan trọng vì nó cho thấy có nhiều luồng riêng, không phải request nào cũng đi qua ALB.”

## Slide 4 — One cluster, four security areas · 2 phút 30 giây

**Mục đích:** Phân biệt data plane, control plane, workload identity và evidence.

**Lời thoại:**

“Nhìn vào sơ đồ có bốn đường.

Đường thứ nhất là request người dùng: Internet → ALB → pod IP. WAF có thể đặt trước hoặc gắn với ALB để lọc HTTP; trong sandbox WAF chưa bật.

Đường thứ hai là người vận hành hoặc pipeline: IAM role → EKS API endpoint → Access Entry → EKS access policy hoặc Kubernetes RBAC. Đây là đường quản trị cluster, độc lập với ALB ứng dụng. `kubectl` không đi qua load balancer của website.

Đường thứ ba là pod gọi AWS: ứng dụng dùng ServiceAccount, EKS Pod Identity hoặc IRSA, rồi nhận một IAM role có quyền hẹp. Đây không phải quyền của người đang chạy `kubectl`, cũng không phải Node IAM Role.

Đường thứ tư là quan sát: CloudTrail, EKS audit logs, VPC Flow Logs, GuardDuty và application logs cung cấp các góc nhìn khác nhau.

Control plane là phần EKS quản lý để nhận lệnh và điều phối Kubernetes. Data plane là node và pod chạy workload. Tách các luồng ra giúp chẩn đoán đúng: nếu người dùng không gọi được website thì kiểm tra ALB path; nếu `kubectl` không kết nối được thì kiểm tra EKS API, mạng quản trị và IAM.”

**Chuyển ý:** “Bây giờ đi từ ranh giới ngoài cùng của request: VPC, subnet và ALB.”

## Slide 5 — VPC, subnets và ALB · 2 phút

**Mục đích:** Giải thích public/private, security groups, NACL và NAT.

**Lời thoại:**

“VPC là mạng riêng trong AWS. Subnet là một dải IP trong VPC, đặt trong một Availability Zone. Public hay private không do tên quyết định mà do route table. Public subnet có route tới Internet Gateway; private subnet không có đường trực tiếp đó.

ALB internet-facing nằm trong public subnets để nhận HTTPS cổng 443. Worker nodes và pods ở private subnets, không có public IP. ALB vẫn có thể gọi pod IP qua mạng VPC.

Security group là firewall stateful gắn với tài nguyên hoặc network interface. Nó kiểm tra nguồn, cổng và giao thức; phản hồi của một kết nối được phép tự quay về. Network ACL áp ở subnet và stateless: phải tính cả luật chiều đi-và-về cùng ephemeral ports. Vì NACL rộng phạm vi và khó debug hơn, lab tập trung vào security group; chỉ thêm NACL khi có yêu cầu rõ.

Private subnet cần đường outbound để node tải image hoặc gọi AWS APIs. NAT Gateway làm nhiệm vụ đó; NAT không phải firewall và không tự mở inbound vào node. VPC endpoints là lựa chọn để một số AWS API đi qua private network. Sandbox dùng một NAT để giảm chi phí; nếu AZ chứa NAT gặp sự cố, outbound từ AZ khác cũng bị ảnh hưởng.”

**Chuyển ý:** “Khi request tới ALB, target type quyết định nó đi tiếp qua node hay trực tiếp tới pod.”

## Slide 6 — ALB: Instance targets vs IP targets · 2 phút 30 giây

**Mục đích:** Giải thích hai mode và cấu hình lab.

**Lời thoại:**

“Với instance target, target group chứa EC2 node. ALB gửi request tới NodePort; Kubernetes Service sau đó chọn pod. Đường đi là ALB → node → NodePort → Service → pod.

Với IP target, target group chứa IP của từng pod. ALB gửi thẳng tới pod IP cổng 8080. Đây là mode lab đang dùng. Service `web` vẫn có mặt với type `ClusterIP`, để workload bên trong cluster có một địa chỉ ổn định và để controller biết backend nào thuộc Service. Nhưng ClusterIP không phải một hop trong request ALB ở IP target mode.

AWS Load Balancer Controller chạy trong cluster. Nó đọc Ingress và Service/endpoints, rồi gọi AWS APIs để tạo ALB, listener, target group và đồng bộ danh sách pod. Target group là danh sách backend mà ALB gọi; health check `/healthz` kiểm tra pod có sẵn sàng không.

Khi pod đổi IP, Deployment tạo pod thay thế, EndpointSlice cập nhật và controller cập nhật target group. TLS trong lab kết thúc ở ALB: client tới ALB bằng HTTPS 443, ALB gửi HTTP tới pod 8080. Nếu yêu cầu mã hóa cả đoạn backend, phải cấu hình HTTPS tới target và chứng chỉ phù hợp.”

**Chuyển ý:** “Đường đã đúng chưa đủ; ta còn phải giới hạn pod nào được phép giao tiếp.”

## Slide 7 — NetworkPolicy · 2 phút

**Mục đích:** Phân biệt security group, NetworkPolicy và Security Groups for Pods.

**Lời thoại:**

“Security group kiểm soát kết nối ở lớp AWS network interface. Kubernetes NetworkPolicy kiểm soát luồng vào/ra của pod — ví dụ cho frontend gọi backend cổng 8080, nhưng chặn pod không liên quan.

Mô hình thường dùng là default-deny rồi mở từng luồng cần thiết. Nhưng khi chặn egress phải nhớ DNS. Nếu không mở DNS tới CoreDNS, pod có thể không phân giải được tên Service.

NetworkPolicy chỉ có hiệu lực nếu CNI thực thi. Trong lab, Amazon VPC CNI được cấu hình bật NetworkPolicy agent. Apply YAML thành công chỉ chứng minh API đã lưu policy, không chứng minh packet bị chặn; cần thử request được phép lẫn request bị cấm.

Security Groups for Pods là tính năng riêng của VPC CNI để gắn security group vào một số pod ENI. Nó có thể hữu ích khi pod cần ranh giới VPC riêng tới AWS resources, nhưng có yêu cầu về instance type và enforcement mode. Lab này không bật tính năng đó; không nên nhầm nó với NetworkPolicy.”

**Chuyển ý:** “NetworkPolicy kiểm soát pod nói chuyện với ai; slide kế tiếp kiểm soát pod được tạo với quyền gì.”

## Slide 8 — Harden the pod before it runs · 2 phút

**Mục đích:** Giải thích admission, runtime context và namespace.

**Lời thoại:**

“Pod Security Admission là cửa kiểm tra trong Kubernetes API. Khi người dùng gửi manifest, API kiểm tra chính sách trước khi tạo Pod. Ta có thể dùng Audit và Warn để tìm workload không tương thích, rồi mới Enforce Restricted.

Trong runtime, securityContext đặt container chạy non-root, cấm privilege escalation, bỏ Linux capabilities thừa, bật seccomp và filesystem chỉ đọc. Requests/limits giúp scheduler xếp tài nguyên và ngăn workload dùng quá mức. Readiness probe báo ứng dụng đã sẵn sàng nhận traffic chưa.

Namespace giúp nhóm resource và áp RBAC/NetworkPolicy, nhưng namespace không tạo một kernel riêng. Workload cùng node vẫn dùng chung kernel. Vì vậy cân nhắc hostPath, hostPID, hostNetwork và privileged; nếu cần ranh giới cô lập cao hơn có thể dùng node group hoặc cluster riêng.

Trong lab, thử tạo Pod privileged trong `payments`; API từ chối trước khi container chạy. Đó là bằng chứng admission đang enforce, không chỉ là một nhãn trên namespace.”

**Chuyển ý:** “Bây giờ chuyển sang danh tính con người — ai được quyền thay đổi cluster?”

## Slide 9 — Human access · 1 phút 30 giây

**Mục đích:** Tách authentication khỏi authorization.

**Lời thoại:**

“Authentication trả lời ‘bạn là ai?’. Người dùng đăng nhập qua IAM Identity Center hoặc IAM role để có AWS credentials. EKS API xác thực principal đó qua Access Entry. Authorization trả lời ‘bạn được làm gì?’; EKS access policy hoặc Kubernetes RBAC quyết định quyền và phạm vi.

Trong lab, admin dành cho quản trị, DevOps được triển khai trong `payments` nhưng không đọc Secret, còn observer chỉ xem pod/log. Dùng `kubectl auth can-i` để kiểm tra cả `yes` và `no`.

Endpoint quản trị cũng là một ranh giới. Sandbox bật private endpoint và public endpoint giới hạn một CIDR `/32` để chạy CLI. Đây không phải private-only. Thiết kế private-only cần VPN, Direct Connect hoặc máy quản trị trong VPC. Nhớ đây là EKS API path, không đi qua ALB của ứng dụng.”

**Chuyển ý:** “Người vận hành đã có identity riêng; ứng dụng trong pod cũng phải có identity riêng.”

## Slide 10 — Pod to AWS · 1 phút 30 giây

**Mục đích:** Giải thích Pod Identity, IRSA và Node IAM Role.

**Lời thoại:**

“Pod cần gọi S3 hoặc Secrets Manager thì không nên mượn quyền của node. Pod dùng Kubernetes ServiceAccount, EKS Pod Identity hoặc IRSA liên kết nó với IAM role, rồi role chỉ cấp đúng API và resource cần thiết.

Nếu mọi pod dùng chung Node IAM Role, một ứng dụng bị compromise có thể thừa hưởng quyền của toàn node group. Đồng thời cần hạn chế pod truy cập EC2 Instance Metadata Service, vì metadata có thể cung cấp credentials của node. Lab yêu cầu IMDSv2 và hop limit 1, rồi cấp Pod Identity riêng.

EKS Auto Mode tích hợp Pod Identity Agent vào data plane. Lab này chạy managed node group tiêu chuẩn nên cài managed `eks-pod-identity-agent` add-on. Hai cách này khác trong triển khai, nhưng nguyên tắc vẫn là mỗi workload chỉ có quyền cần thiết.”

**Chuyển ý:** “Identity bảo vệ quyền lúc chạy; bảo mật còn bắt đầu từ image và tiếp tục tới dữ liệu.”

## Slide 11 — Supply chain, secrets và encryption · 2 phút 30 giây

**Mục đích:** Giải thích scan, SBOM, signature, Secrets và mã hóa.

**Lời thoại:**

“Một container có thể chạy non-root nhưng vẫn chứa package có lỗ hổng. Supply chain security theo image từ source, build, scan tới lúc admission cho phép deploy.

Scanner như ECR/Inspector báo CVE trong operating-system packages và dependencies. Scan không tự chặn deployment; muốn chặn cần CI/CD quality gate hoặc admission policy. SBOM là danh sách thành phần trong image, giúp tìm image nào bị ảnh hưởng khi một thư viện có CVE mới. Image signing cho biết image đến từ pipeline đáng tin cậy và chưa bị thay đổi; muốn tự động reject image không có chữ ký cần thêm admission verifier. Lab đã scan image và ghi nhận findings, nhưng chưa cấu hình SBOM, chữ ký hay admission enforcement.

Kubernetes Secret dùng Base64 để biểu diễn dữ liệu; Base64 không phải mã hóa. EKS 1.28 trở lên mặc định envelope-encrypt Kubernetes API data bằng AWS-owned key. Customer-managed KMS key là lựa chọn khi cần quyền kiểm soát khóa riêng. Cơ chế đó không thay RBAC và không tự mã hóa EBS, EFS hay database.

Production app nên lấy secret từ Secrets Manager hoặc Parameter Store qua role giới hạn đúng secret ARN. Cần thiết kế rotation và cách ứng dụng reload; thay secret trong store không đảm bảo app tự dùng giá trị mới.”

**Chuyển ý:** “Khi các lớp phòng ngừa đã có, ta cần quan sát để biết điều gì đang xảy ra.”

## Slide 12 — Detect · 1 phút 30 giây

**Mục đích:** Phân biệt nguồn log.

**Lời thoại:**

“Mỗi loại log trả lời câu hỏi khác. CloudTrail: ai thay đổi IAM, security group hay EKS qua AWS API? EKS audit log: ai tạo hoặc sửa Kubernetes resource? VPC Flow Logs: network interface nào giao tiếp và được accept hay reject? GuardDuty Runtime: có hành vi process, file hoặc network đáng ngờ trên node không? ALB, WAF và app logs: request nào tới edge, bị rule nào xử lý và app trả kết quả gì?

VPC Flow Logs chỉ có metadata, không chứa payload HTTP. GuardDuty EKS Protection phân tích audit signals qua luồng do GuardDuty quản lý; CloudWatch EKS control-plane logs là bản sao riêng để mình lưu và truy vấn. Bật một nguồn không tự bật nguồn còn lại.

Để điều tra, ghép identity, thời gian, API action, network flow và runtime finding. Các nguồn phát hiện cần retention, quyền đọc/xóa riêng và người chịu trách nhiệm.”

**Chuyển ý:** “Phát hiện được một finding mới là bắt đầu; cần có quy trình xử lý.”

## Slide 13 — Incident response · 1 phút 30 giây

**Mục đích:** Trình bày vòng phản ứng.

**Lời thoại:**

“Quy trình có sáu bước: phát hiện, phân loại phạm vi, cô lập, giữ bằng chứng, loại bỏ nguyên nhân và khôi phục workload sạch.

Đừng bắt đầu bằng xóa pod nếu cần điều tra; Deployment có thể tạo lại pod từ chính image dễ bị khai thác. Cordon node chỉ ngăn pod mới được schedule lên node, nó không chặn network traffic và không dừng pod đang chạy. Nếu credentials bị lộ, phải revoke/rotate và kiểm tra AWS API activity; gỡ Pod Identity association không nhất thiết làm mọi STS credential đã cấp mất hiệu lực ngay lập tức.

Containment có thể làm gián đoạn dịch vụ hoặc thay đổi bằng chứng, nên làm theo quyền hạn và runbook. Automation có thể gửi alert, mở ticket, gom context; hành động phá hủy như xóa pod nên có phê duyệt cho tới khi quy trình được kiểm chứng.”

**Chuyển ý:** “Trong sandbox, có một tình huống cụ thể cho thấy kiểm tra end-to-end quan trọng ra sao.”

## Slide 14 — Lab story: target healthy, client gets 504 · 2 phút

**Mục đích:** Chia sẻ quy trình debug có bằng chứng.

**Lời thoại:**

“Trong lần chạy lab, target group báo hai pod healthy nhưng client gọi `/healthz` qua ALB nhận 504. Thay vì mở thêm port rộng, mình lần theo đường đi: listener và target group, security groups, CNI enforcement, NetworkPolicy, rồi pod logs.

Ở sandbox, thêm rule hẹp cho nguồn ALB cần thiết tới cổng 8080 thì `/healthz` trả 200. Tuy nhiên không nên chép một CIDR đoán mò sang môi trường khác. Source mà policy datapath nhìn thấy có thể phụ thuộc target type, CNI và đường routing. Quan sát VPC Flow Logs, kiểm tra CNI/version và thử đúng request trước khi thêm allow rule.

Lab đã thể hiện ALB IP target, security group, NetworkPolicy, PSA, Access Entry/RBAC, Pod Identity, audit/flow logs và GuardDuty coverage. WAF, image signature enforcement và EventBridge/SNS notification là phần mở rộng, chưa bật trong sandbox.”

**Demo nếu môi trường còn chạy:** mở Target Group → Targets, đối chiếu hai pod IP; sau đó gọi HTTPS `/healthz` và chỉ policy tương ứng. Nếu cluster đã dọn, dùng ảnh chụp đã chuẩn bị.

**Chuyển ý:** “Mình kết thúc bằng ba điều cần nhớ.”

## Slide 15 — Wrap-up · 1 phút

**Mục đích:** Chốt thông điệp.

**Lời thoại:**

“Thứ nhất, network: security group giới hạn ranh giới VPC; NetworkPolicy phân đoạn pod traffic. Thứ hai, identity: quyền người vận hành khác quyền workload; mỗi workload chỉ nhận quyền cần thiết. Thứ ba, response: phát hiện, cô lập, giữ bằng chứng, loại bỏ nguyên nhân rồi mới khôi phục.

Thông điệp chung là hãy vẽ đường đi, xác định ai sở hữu từng quyền, rồi kiểm tra cả allow lẫn deny. Một control đáng tin khi mình chứng minh được nó hoạt động và biết cách phản ứng khi nó thất bại.

Xin cảm ơn mọi người. Mình sẵn sàng đi sâu vào luồng ALB tới pod hoặc phần IAM/RBAC trong hỏi đáp.”

## Gợi ý mở workshop Hugo khi trình bày

| Slide | Trang workshop |
|---|---|
| 3–4 | [Architecture and threat model](../eks-defense-in-depth/01-architecture/) |
| 5 | [VPC, subnet and security groups](../eks-defense-in-depth/02-network/) |
| 6–7 | [Ingress and NetworkPolicy](../eks-defense-in-depth/06-traffic/) |
| 8, 11 | [Workload hardening and image supply chain](../eks-defense-in-depth/05-workloads/) |
| 9 | [Human access and RBAC](../eks-defense-in-depth/04-identity/) |
| 10–11 | [Pod Identity and secrets](../eks-defense-in-depth/07-workload-identity/) |
| 12 | [Audit and threat detection](../eks-defense-in-depth/08-detection/) |
| 13 | [Incident response](../eks-defense-in-depth/09-response/) |
| 14–15 | [Validation and cleanup](../eks-defense-in-depth/10-cleanup/) |

## Câu hỏi có thể gặp

### ALB có đi qua Service không?

Trong lab dùng `target-type: ip`, ALB target group nhận pod IP trực tiếp. `ClusterIP` Service vẫn tồn tại cho các workload gọi app nội bộ và để controller theo dõi endpoints, nhưng không phải network hop của request ALB.

### Target group healthy mà website vẫn lỗi thì sao?

Health check chỉ chứng minh đường health check tới target đang hoạt động. Hãy lần theo listener, target group, security group, CNI, NetworkPolicy và app logs; xác minh source thực tế trước khi mở rule.

### Những phần nào chưa triển khai?

WAF, CloudFront, Route 53/domain certificate, SBOM/signature enforcement, Security Groups for Pods, EventBridge/SNS alert và tự động containment chưa được bật trong sandbox. Đây là lựa chọn nâng cao, không phải bằng chứng đã có trong lab.

## Slide deck gốc

Kịch bản này được viết theo `EKS_Defense_in_Depth_Presentation_15slides.pptx` đọc từ Desktop. File PowerPoint không được thêm vào repository; nội dung Hugo này là phần lời thoại và liên kết tới các module workshop.
