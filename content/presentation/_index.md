---
title: "Vietnamese presentation guide"
weight: 2
chapter: false
---

# Kịch bản 25 phút: Phòng thủ theo chiều sâu cho Amazon EKS

Kịch bản này đi theo đúng **11 slide** trong `EKS_Defense_in_Depth_Vietnamese.pptx`. Mở slide tương ứng và dùng lời thoại Hugo bên dưới. Thời lượng lời nói khoảng 25 phút; phần demo Console có thể thêm 3–5 phút.

{{% notice note %}}
Phạm vi là sandbox đã chạy và kiểm chứng: ALB dùng IP targets; Service `ClusterIP`; Deployment giữ hai pod `web`; EKS API có private endpoint và public endpoint giới hạn một CIDR `/32`. WAF, Route 53, SNS/email alert và certificate domain công khai chưa được cấu hình. Chứng chỉ ACM của lần thử là certificate thử nghiệm.
{{% /notice %}}

## Slide 1 — Phòng thủ theo chiều sâu cho Amazon EKS · 1 phút

**Mục đích:** Giới thiệu đề tài và cho khán giả biết đây là buổi technical walkthrough trên lab thật.

**Lời thoại:**

“Xin chào mọi người. Hôm nay mình sẽ trình bày một workshop về phòng thủ theo chiều sâu cho Amazon EKS. Thay vì chỉ liệt kê các dịch vụ AWS, mình sẽ lần theo một request từ Internet đến ứng dụng, xem nó đi qua những ranh giới nào và mỗi ranh giới đang bảo vệ điều gì.

Lab dùng một ứng dụng mẫu đơn giản. Nó không xử lý thanh toán thật và không chứa dữ liệu khách hàng. Mục tiêu là làm rõ các thành phần mạng, Kubernetes và AWS thông qua một luồng có thể kiểm chứng: từ ALB đến pod, từ người vận hành đến Kubernetes API và từ workload đến AWS identity.”

**Chuyển ý:** “Trước khi xem kiến trúc, mình bắt đầu từ câu hỏi bảo mật cần trả lời.”

## Slide 2 — Một request cần vượt qua những ranh giới nào? · 2 phút

**Mục đích:** Đặt threat model. Trình bày phòng thủ theo lớp như những câu hỏi khác nhau, không phải một danh sách sản phẩm.

**Lời thoại:**

“Khi một request đến ứng dụng, mình cần trả lời năm câu hỏi. Thứ nhất: ai được kết nối vào hệ thống? Thứ hai: khi đã vào được, request được đi tới workload nào? Thứ ba: container được chạy với quyền gì? Thứ tư: con người và ứng dụng được phép làm gì? Cuối cùng: nếu có hành vi bất thường, mình có bằng chứng nào để phát hiện và điều tra?

Các câu hỏi này nằm ở những lớp khác nhau. Security group có thể giới hạn kết nối từ mạng; NetworkPolicy kiểm soát giao tiếp giữa pod; Pod Security Admission từ chối một số cấu hình nguy hiểm; IAM và RBAC phân quyền danh tính; log và GuardDuty hỗ trợ quan sát.

Không có một lớp nào thay thế hoàn toàn các lớp khác. Ví dụ, đặt node ở private subnet giảm khả năng bị truy cập trực tiếp từ Internet, nhưng không ngăn một pod trong cluster gọi nhầm sang workload khác. RBAC có thể giới hạn lệnh của người dùng, nhưng không tự lọc gói tin mạng. Logging cho mình biết chuyện gì đã xảy ra, nhưng bản thân log không chặn request.

Ý tưởng của defense in depth là một cấu hình sai ở một lớp không nên làm mọi lớp phía sau mất tác dụng. Và thay vì chỉ xem cấu hình, mình sẽ thử cả đường được phép lẫn đường phải bị chặn.”

**Chuyển ý:** “Để hiểu các ranh giới đó nằm ở đâu, ta xem bản đồ tổng thể.”

## Slide 3 — Tổng quan kiến trúc sandbox · 2 phút 30 giây

**Mục đích:** Giải thích VPC, public/private subnet, NAT, EKS control plane, node và pod.

**Lời thoại:**

“Đây là VPC riêng của lab, chia trên hai Availability Zone. Mỗi AZ có public subnet và private subnet. ALB nằm ở public subnets để có thể nhận kết nối từ phía người dùng. Worker node là các máy EC2 nằm trong private subnets; chúng không có public IP. Các pod ứng dụng được cấp IP trong mạng VPC thông qua Amazon VPC CNI.

Public subnet và private subnet không được xác định bởi tên. Điều quan trọng là route table: public subnet có route mặc định tới Internet Gateway; private subnet không có route trực tiếp đó. Private subnet của lab có đường outbound qua một NAT Gateway. NAT cho phép máy bên trong mở kết nối đi ra ngoài, chẳng hạn tải image hoặc gọi dịch vụ cần thiết; nó không có nghĩa Internet có thể tự mở kết nối mới vào node.

Lab dùng một NAT Gateway để giảm chi phí. Đây là trade-off: hai AZ có node, nhưng đường outbound phụ thuộc vào NAT nằm ở một AZ. Vì thế không nên gọi đây là thiết kế HA đầy đủ.

Phần control plane là Kubernetes API server và các thành phần điều phối do EKS quản lý. Nó không phải pod ứng dụng chạy trên worker node. Worker node mới là EC2 do mình quản lý trong VPC; pod chạy trên worker node.

EKS API endpoint trong sandbox bật cả private lẫn public access, nhưng public bị giới hạn vào một CIDR `/32` để chạy CLI từ máy quản trị. Đây không phải private-only. Nếu triển khai thực tế chặt hơn, có thể tắt public endpoint và quản trị từ VPN, Direct Connect hoặc máy trong VPC.

WAF và Route 53 xuất hiện trong kiến trúc tham khảo, nhưng chưa được tạo trong lần chạy sandbox này. ALB đang được gọi qua DNS name do AWS cấp.”

**Chỉ trên trang:** [Module 2 — VPC và subnet](../eks-defense-in-depth/02-network/) và [Module 3 — EKS cluster](../eks-defense-in-depth/03-cluster/).

**Chuyển ý:** “Giờ mình phóng to riêng luồng request và xem Ingress/controller/target group kết nối ra sao.”

## Slide 4 — Từ Internet đến pod: ALB dùng IP targets · 3 phút

**Mục đích:** Giải thích Ingress, AWS Load Balancer Controller, ALB, target group, pod IP, Service và EndpointSlice.

**Lời thoại:**

“Client gửi HTTPS tới ALB ở cổng 443. Listener của ALB nhận kết nối và chuyển request đến target group. Target group là danh sách backend mà ALB sẽ gọi; trong lab, danh sách có IP của hai pod `web`, port 8080.

Vậy làm sao một Kubernetes manifest tạo ra ALB trong AWS? Mình cài AWS Load Balancer Controller trong cluster. Đây là một controller: nó liên tục theo dõi các tài nguyên Kubernetes mà nó quản lý. Khi thấy Ingress có class `alb`, controller gọi AWS API để tạo hoặc cập nhật ALB, listener, target group và các security-group rule cần thiết.

Ingress là cấu hình, không phải load balancer. Controller là thành phần chuyển cấu hình đó thành tài nguyên AWS. Target group mới là danh sách đích thực tế của ALB.

Trong manifest, `target-type: ip` yêu cầu controller đăng ký IP pod trực tiếp. App lắng nghe ở 8080. ALB kết thúc TLS tại listener HTTPS và trong cấu hình lab gửi HTTP nội bộ tới pod.

Service `web` vẫn được khai báo kiểu `ClusterIP`. Nó cung cấp địa chỉ ổn định để các workload khác trong cluster gọi ứng dụng. Nhưng ở IP target mode, ALB không gửi request qua NodePort hay ClusterIP. Controller lấy các backend pod qua EndpointSlice do Kubernetes duy trì.

Nếu một pod dừng, Deployment nhận thấy số bản sẵn sàng thấp hơn hai và tạo pod khác. Pod mới có thể có IP mới. EndpointSlice cập nhật; controller quan sát thay đổi rồi đăng ký địa chỉ mới vào target group, đồng thời gỡ địa chỉ cũ. ALB health check `/healthz`; khi target mới khỏe thì traffic được gửi tới đó.

Đây cũng là điểm khác cách quen thuộc ở ECS. Với ECS, mình thường gắn target group vào ECS Service và ECS Service đồng bộ các task. Với EKS, trách nhiệm được tách ra giữa Deployment, Service, Ingress và AWS Load Balancer Controller.”

**Chỉ trên trang:** [Module 6 — Ingress và NetworkPolicy](../eks-defense-in-depth/06-traffic/). Nếu có Console, mở **EC2 → Target Groups → Targets** để cho xem hai pod IP.

**Chuyển ý:** “Có route đúng chưa đủ; bây giờ xem firewall ở AWS và policy trong Kubernetes phối hợp thế nào.”

## Slide 5 — Security Group và NetworkPolicy · 3 phút

**Mục đích:** Phân biệt hai loại kiểm soát mạng và kể lại sự cố 504 đã xử lý.

**Lời thoại:**

“Security group là firewall stateful gắn với network interface hoặc tài nguyên AWS. ALB nhận HTTPS từ CIDR được cho phép. Trên đường backend, security group chỉ cho port ứng dụng từ security group của ALB. Như vậy client Internet không được mở kết nối tùy ý thẳng tới node hoặc pod.

NetworkPolicy hoạt động ở lớp Kubernetes pod. Namespace `payments` có default-deny cho ingress và egress. Sau đó mình thêm các allow rule cụ thể: DNS, Pod Identity agent, frontend test client và nguồn ALB tới app port. NetworkPolicy không thay security group; một lớp giới hạn traffic bên trong cluster, lớp kia điều khiển traffic ở ranh giới AWS network interface.

Điều kiện quan trọng là CNI phải thực thi policy. Trong lab, VPC CNI add-on bật NetworkPolicy và agent chạy trên node. Nếu chỉ `kubectl apply` một object NetworkPolicy nhưng plugin không hỗ trợ/enforce, người vận hành có thể tưởng traffic đã bị chặn trong khi thực tế chưa.

Khi kiểm tra lần đầu, AWS Target Group báo cả hai target healthy, nhưng gọi HTTPS vào app bị 504. Target healthy chỉ cho biết health check của target group đạt yêu cầu; nó không chứng minh mọi request user đi qua policy giống health check. Mình đối chiếu NetworkPolicy và thấy thiếu nguồn traffic từ ALB. Sau khi thêm rule hẹp cho các CIDR public subnet của ALB tới port 8080, `/healthz` trả HTTP 200.

Bài học là kiểm tra theo đường đi end-to-end, không dừng ở một dấu xanh. Đồng thời thử request được phép và request không được phép. Trong lab, frontend được vào `payments`; client ở namespace `default` bị timeout như mong muốn.”

**Chỉ trên trang:** [Module 6 — NetworkPolicy](../eks-defense-in-depth/06-traffic/). Có thể chiếu policy allow/deny và kết quả `/healthz`.

**Chuyển ý:** “Mạng giới hạn pod liên hệ với ai; tiếp theo là giới hạn pod được khởi chạy với cấu hình nào.”

## Slide 6 — Giảm quyền từ lúc workload được tạo · 2 phút

**Mục đích:** Giải thích Pod Security Admission và hardening container.

**Lời thoại:**

“Container không phải máy ảo. Nó chia sẻ kernel của node với các workload khác, nên nếu cấp quá nhiều quyền thì một lỗi trong app có thể gây ảnh hưởng rộng hơn.

Namespace `payments` bật Pod Security Admission ở mức `restricted`. Đây là admission control tích hợp trong Kubernetes API server: khi người dùng gửi manifest, API server kiểm tra cấu hình trước khi tạo pod. Mình thử một manifest privileged; API từ chối và pod không được tạo.

Deployment app cũng được harden ở runtime: chạy non-root, filesystem root chỉ đọc, bỏ Linux capabilities không cần thiết, đặt resource request/limit và health probes. Readiness probe giúp hệ thống không gửi traffic vào pod chưa sẵn sàng; limit giúp một workload không dùng tài nguyên vô hạn.

Không phải cấu hình nào cũng tương thích với restricted policy. Với ứng dụng thật, nên thử ở môi trường lab, xem warning/audit, rồi áp enforcement có kế hoạch. Một lớp admission tốt ngăn cấu hình nguy hiểm ngay từ đầu, nhưng không thay thế việc cập nhật image và theo dõi runtime.”

**Chỉ trên trang:** [Module 4 — Node, namespace và pod](../eks-defense-in-depth/05-workloads/).

**Chuyển ý:** “Khi pod chạy an toàn hơn, ta cần giới hạn quyền mà con người và ứng dụng mang theo.”

## Slide 7 — Tách danh tính người vận hành và ứng dụng · 3 phút

**Mục đích:** Giải thích IAM authentication, EKS Access Entry, RBAC, service account và Pod Identity.

**Lời thoại:**

“Có hai identity path riêng. Người vận hành gọi `kubectl`; ứng dụng trong pod gọi AWS API. Không nên dùng chung quyền.

Với con người, IAM xác thực AWS principal. EKS Access Entry cho cluster biết principal đó được phép xác thực vào cluster và có thể ánh xạ họ vào nhóm Kubernetes. Kubernetes RBAC mới là nơi quyết định user được get, create hay delete resource nào trong namespace nào. Nói ngắn gọn: IAM cho biết bạn là ai ở AWS; RBAC quyết định bạn làm gì trong Kubernetes.

Lab có admin, DevOps và observer. Admin dành cho quản trị. DevOps có quyền triển khai trong namespace `payments`, xem pod/log và service liên quan, nhưng không đọc Secrets, sửa RoleBinding hay truy cập namespace khác. Observer chỉ xem thông tin workload và log. Mình kiểm tra cả allow và deny bằng `kubectl auth can-i`.

Có một gotcha quan trọng: trong sandbox, policy EKS managed `AmazonEKSEditPolicy` cho phép đọc Secret trong namespace. Vì vậy nếu yêu cầu là deploy nhưng không đọc Secret, mình không dùng managed edit policy; mình ánh xạ group `payments-deployers` vào Kubernetes Role tùy chỉnh hẹp hơn.

Với workload, pod dùng Kubernetes ServiceAccount `web-reader`, liên kết với IAM role thông qua EKS Pod Identity. Agent trên node cung cấp credential tạm thời cho AWS SDK. Không đặt access key dài hạn trong image, environment manifest hay source code.

Role mẫu của app không có quyền AWS vì app không cần gọi dịch vụ AWS. Node role cũng là một danh tính riêng dành cho node, ví dụ để kéo image; không nên để application tự thừa hưởng quyền node. Tách danh tính giúp giảm blast radius nếu một pod bị khai thác.”

**Chỉ trên trang:** [Module 6 — Human access/RBAC](../eks-defense-in-depth/04-identity/) và [Module 7 — Pod Identity](../eks-defense-in-depth/07-workload-identity/).

**Chuyển ý:** “Ngăn chặn và phân quyền tốt nhưng vẫn cần biết ai đã thay đổi gì; đó là vai trò của logging và detection.”

## Slide 8 — Quan sát để trả lời: ai làm gì, kết nối đi đâu? · 2 phút

**Mục đích:** Nêu nguồn telemetry, giới hạn của detection và những gì chưa cấu hình.

**Lời thoại:**

“EKS audit logs cho biết ai gọi Kubernetes API, verb gì và tác động đến object nào. VPC Flow Logs ghi metadata kết nối mạng ở cấp VPC/ENI. GuardDuty Runtime Monitoring cung cấp tín hiệu runtime trên node. CloudTrail ghi lại hoạt động gọi AWS API. Tài khoản đã có organization CloudTrail từ trước; lab giữ nguyên trail đó, không sửa hay xóa.

Các nguồn này bổ sung góc nhìn chứ không tự chặn request. GuardDuty finding cần người xem xét và quy trình ứng cứu. Log cần retention và quyền truy cập phù hợp. Alert cần có người nhận, nếu không thì alert chỉ tồn tại trên màn hình.

Trong sandbox có EKS control-plane logs, VPC Flow Logs và GuardDuty coverage để kiểm tra. WAF, Route 53, certificate domain công khai và SNS/email alert chưa cấu hình. Đây là phần cần triển khai bổ sung nếu biến workshop thành môi trường production.”

**Chỉ trên trang:** [Module 8 — Audit và threat detection](../eks-defense-in-depth/08-detection/) và [Module 9 — Incident response](../eks-defense-in-depth/09-response/).

**Chuyển ý:** “Giờ gom lại các bằng chứng để xem mình đã chứng minh điều gì, thay vì chỉ nhìn dịch vụ đang ở trạng thái Active.”

## Slide 9 — Đừng chỉ nhìn trạng thái xanh: thử allow và deny · 2 phút 30 giây

**Mục đích:** Tóm lược kiểm chứng end-to-end.

**Lời thoại:**

“Mình xác minh từng lớp bằng kết quả cụ thể. Ở network edge, ALB ở public subnet và node ở private subnet, node không có public IP. Ở ingress, target group hiển thị hai pod IP trên port 8080. Ở NetworkPolicy, nguồn được phép truy cập được; client ở `default` không vào được `payments`.

Ở admission, privileged pod bị API server từ chối trước khi chạy. Ở RBAC, DevOps làm được thao tác cần cho công việc nhưng không đọc Secret hoặc thao tác ngoài namespace. Ở workload identity, SDK nhận provider `container-role` mà app không in giá trị credential.

Ở observability, mình tạo sự kiện kiểm thử để xác nhận audit log đến CloudWatch, kiểm tra trạng thái Flow Logs và GuardDuty coverage. Những kiểm tra này quan trọng hơn một ảnh chụp chỉ có chữ ACTIVE, vì chúng chứng minh đường dữ liệu hoặc quyền thực sự hoạt động.

Kết quả cũng cho thấy kiểm chứng cần gồm cả điều kiện âm: thử điều không nên làm và xác nhận hệ thống từ chối.”

**Demo gợi ý (thêm 1–2 phút nếu thời gian cho phép):**

```bash
kubectl get nodes -o wide
kubectl get deploy,pods,svc -n payments -o wide
kubectl get ingress,endpointslice -n payments -o wide
kubectl --context eks-depth-devops auth can-i get secrets -n payments
```

Khi chuyển qua Console, che account ID, IP cá nhân, role ARN, cluster endpoint và DNS nếu không muốn công khai.

**Chuyển ý:** “Từ các kiểm tra đó, mình rút ra các lớp chính và trade-off của lab.”

## Slide 10 — Bảo mật là hành trình, không phải checkbox · 1 phút 30 giây

**Mục đích:** Tóm gọn những lớp đã xây và nhắc trade-off.

**Lời thoại:**

“Lớp entry là ALB HTTPS; EKS API public chỉ mở cho `/32`. Lớp network là private nodes/pods, security group và NetworkPolicy. Lớp workload là restricted admission, non-root, read-only filesystem. Lớp identity gồm IAM, EKS Access Entry, RBAC và Pod Identity. Lớp detection gồm audit logs, Flow Logs và GuardDuty.

Mỗi quyết định đều có trade-off. Public API giới hạn `/32` giúp workstation chạy được CLI nhưng private-only sẽ hẹp hơn. Một NAT rẻ hơn hai NAT nhưng tạo phụ thuộc AZ. IP targets bỏ NodePort và chuyển thẳng tới pod, nhưng cần CNI cung cấp pod IP routable và phải cấu hình security group cùng NetworkPolicy đúng.”

**Chuyển ý:** “Slide cuối là checklist để trình bày trực tiếp bằng các trang Hugo và Console.”

## Slide 11 — Thứ tự demo trên Hugo/Console · 2 phút 30 giây

**Mục đích:** Hướng dẫn người nghe tự kiểm tra từng cấu hình.

**Lời thoại:**

“Khi demo, mình đi theo cùng thứ tự với request. Đầu tiên mở VPC Resource Map để chỉ public/private subnet, route và NAT. Tiếp theo vào EC2 Target Groups để cho thấy hai pod IP và health status. Sau đó quay lại Kubernetes để đối chiếu Ingress, ClusterIP Service và EndpointSlice.

Tiếp theo xem NetworkPolicy và kể lại sự cố 504: target healthy không có nghĩa mọi policy cho request đều đúng. Sau đó xem pod security context và chạy `kubectl auth can-i` dưới context DevOps để minh họa quyền được phép/từ chối. Cuối cùng xem audit logs, Flow Logs và GuardDuty coverage.

Trước buổi nói, kiểm tra lại các trang này trong account của mình; tên menu Console và dữ liệu thay đổi theo vùng. Không chiếu credential, account ID hay IP cá nhân. Lab tạo tài nguyên AWS thật và có phí; xong buổi nên chạy cleanup trong đúng sandbox account.”

**Kết:**

“Thông điệp cuối cùng của mình là: hãy vẽ đường đi, xác định ranh giới, kiểm tra bằng hành vi thật và thử cả allow lẫn deny. Đó là cách hiểu bảo mật EKS như một hệ thống hoàn chỉnh, thay vì học thuộc tên dịch vụ.”

## Câu hỏi thường gặp

### Vì sao ALB public nhưng pod lại ở private subnet?

ALB cần nhận request từ Internet. Pod không cần public IP; ALB gọi pod IP qua mạng VPC, với security group và NetworkPolicy giới hạn đường vào.

### ALB có đi qua Service không?

Với cấu hình này, **không**. ALB dùng IP targets nên gửi tới pod IP trong target group. Service `ClusterIP` vẫn dùng cho traffic nội bộ và endpoint ổn định; controller theo dõi EndpointSlice để đồng bộ backend pod.

### Nếu pod đổi IP thì sao?

Deployment tạo pod thay thế; EndpointSlice đổi theo pod sẵn sàng; AWS Load Balancer Controller cập nhật target group; ALB gửi traffic sau khi health check target mới thành công.

### Lab đã sẵn sàng cho production chưa?

Chưa. Đây là sandbox học tập. Cần certificate domain công khai, WAF/alert nếu yêu cầu, cập nhật image có findings, đánh giá HA cho NAT, quy trình quản lý secret, backup, logging retention và ứng cứu theo yêu cầu thực tế.

## Bản slide gốc

Kịch bản này được mở rộng từ file `EKS_Defense_in_Depth_Vietnamese.pptx` gồm 11 slide. File gốc được đọc từ Desktop và không được thêm vào repository; trang Hugo này giữ phần lời thoại để có thể mở trực tiếp khi thuyết trình.
