---
title: "Vietnamese presentation guide"
weight: 2
chapter: false
---

# Kịch bản 25 phút: Phòng thủ theo chiều sâu cho Amazon EKS

Kịch bản này đi theo đúng **11 slide** trong `EKS_Defense_in_Depth_Vietnamese.pptx`. Mở slide tương ứng, dùng phần Hugo làm lời dẫn và chỉ vào hình/nhãn mà bạn đang giải thích. Không cần đọc lại nguyên văn bullet trên slide. Thời lượng nói khoảng 25 phút; nếu demo Console trực tiếp, cộng thêm 3–5 phút.

{{% notice note %}}
Các kết quả được kể trong kịch bản là từ lần sandbox đã chạy và kiểm chứng: ALB dùng IP targets; Service `ClusterIP`; Deployment giữ hai pod `web`; EKS API có private endpoint và public endpoint giới hạn một CIDR `/32`. Trước buổi nói, kiểm tra xem sandbox hiện có đang chạy để demo trực tiếp hay cần dùng ảnh/kết quả đã lưu. WAF, Route 53, SNS/email alert và certificate domain công khai chưa được cấu hình. Chứng chỉ ACM của lần thử là certificate thử nghiệm.
{{% /notice %}}

## Slide 1 — Phòng thủ theo chiều sâu cho Amazon EKS · 1 phút

**Mục đích:** Giới thiệu đề tài và cho khán giả biết đây là buổi technical walkthrough trên lab thật.

**Lời thoại:**

“Xin chào mọi người. Hôm nay mình sẽ trình bày cách bảo vệ một ứng dụng chạy trên Amazon EKS. Mình sẽ không bắt đầu bằng danh sách tên dịch vụ. Thay vào đó, mình sẽ theo chân một request từ người dùng Internet đến ứng dụng, rồi xem các lớp bảo vệ ở dọc đường.

Lab dùng một website mẫu tên `web`. Đây không phải hệ thống thanh toán thật và không chứa dữ liệu khách hàng. Qua ví dụ nhỏ này, mình sẽ giải thích ba luồng: request của người dùng vào pod, người vận hành gọi Kubernetes API, và ứng dụng lấy danh tính để gọi AWS khi cần.”

**Chuyển ý:** “Trước khi xem kiến trúc, mình bắt đầu từ câu hỏi bảo mật cần trả lời.”

## Slide 2 — Một request cần vượt qua những ranh giới nào? · 2 phút

**Mục đích:** Đặt threat model. Trình bày phòng thủ theo lớp như những câu hỏi khác nhau, không phải một danh sách sản phẩm.

**Lời thoại:**

“Hãy tưởng tượng ứng dụng như một tòa nhà. Câu hỏi đầu tiên là ai được qua cổng? Sau cổng, request được đi tới phòng nào? Một container trong phòng được chạy với quyền gì? Người vận hành và ứng dụng được phép làm gì? Cuối cùng, nếu có sự cố thì camera hay nhật ký nào giúp mình biết chuyện gì đã xảy ra?

Trong AWS và Kubernetes, những câu hỏi đó tương ứng với các lớp khác nhau. Security group giới hạn kết nối tới network interface ở AWS. NetworkPolicy giới hạn luồng giữa các pod. Pod Security Admission kiểm tra cấu hình pod trước khi Kubernetes tạo nó. IAM, EKS Access Entry và Kubernetes RBAC xác định danh tính và quyền. Log cùng GuardDuty giúp phát hiện và điều tra.

Mỗi lớp giải quyết một kiểu rủi ro. Private subnet giảm khả năng ai đó kết nối trực tiếp từ Internet vào node, còn NetworkPolicy giúp ngăn một pod gọi sang workload không liên quan. Security group lọc kết nối mạng; RBAC quyết định một người dùng Kubernetes được làm gì. Log ghi lại sự kiện để mình xem xét sau đó.

Đó là ý nghĩa của phòng thủ theo chiều sâu: có nhiều ranh giới, mỗi ranh giới làm một việc cụ thể. Cuối buổi mình sẽ chỉ kết quả thử nghiệm của cả đường được cho phép và đường bị chặn.”

**Chuyển ý:** “Để hiểu các ranh giới đó nằm ở đâu, ta xem bản đồ tổng thể.”

## Slide 3 — Tổng quan kiến trúc sandbox · 2 phút 30 giây

**Mục đích:** Giải thích VPC, public/private subnet, NAT, EKS control plane, node và pod.

**Lời thoại:**

“Đây là mạng VPC của lab. VPC là mạng riêng do mình tạo trong AWS; nó được chia qua hai Availability Zone, tức hai khu vực hạ tầng tách biệt trong cùng region. Mỗi AZ có một public subnet và một private subnet. Subnet là một dải địa chỉ IP nằm trong VPC.

ALB — Application Load Balancer — được đặt ở public subnets để nhận kết nối của người dùng. Worker node là các máy EC2 chạy Kubernetes worker; chúng nằm ở private subnets và không có public IP. Pod ứng dụng chạy trên các node. VPC CNI cấp địa chỉ IP VPC cho pod trong cấu hình này.

Tên subnet không quyết định nó public hay private; route table mới quyết định. Route table giống bảng chỉ đường: public subnet có đường mặc định tới Internet Gateway, cánh cổng kết nối VPC với Internet. Private subnet không có đường trực tiếp đó. Nó dùng NAT Gateway cho kết nối outbound, ví dụ worker tải container image. NAT cho phép máy trong VPC bắt đầu kết nối đi ra; nó không mở cổng để người ngoài tự kết nối vào node.

Lab dùng một NAT Gateway để giảm chi phí. Đây là trade-off: hai AZ có node, nhưng đường outbound phụ thuộc vào NAT nằm ở một AZ. Vì thế không nên gọi đây là thiết kế HA đầy đủ.

EKS quản lý control plane — phần nhận lệnh Kubernetes và điều phối trạng thái cluster — còn worker node là EC2 chạy các pod của mình. Nói đơn giản: mình gửi cấu hình lên Kubernetes API; control plane quyết định cần tạo pod nào; worker node cung cấp máy tính để pod chạy.

EKS API endpoint trong sandbox bật cả private lẫn public access, nhưng public bị giới hạn vào một CIDR `/32` để chạy CLI từ máy quản trị. Đây không phải private-only. Nếu triển khai thực tế chặt hơn, có thể tắt public endpoint và quản trị từ VPN, Direct Connect hoặc máy trong VPC.

WAF và Route 53 xuất hiện trong kiến trúc tham khảo, nhưng chưa được tạo trong lần chạy sandbox này. ALB đang được gọi qua DNS name do AWS cấp.”

**Chỉ trên trang:** [Module 2 — VPC và subnet](../eks-defense-in-depth/02-network/) và [Module 3 — EKS cluster](../eks-defense-in-depth/03-cluster/).

**Chuyển ý:** “Giờ mình phóng to riêng luồng request và xem Ingress/controller/target group kết nối ra sao.”

## Slide 4 — Từ Internet đến pod: ALB dùng IP targets · 3 phút

**Mục đích:** Giải thích Ingress, AWS Load Balancer Controller, ALB, target group, pod IP, Service và EndpointSlice.

**Lời thoại:**

“Người dùng mở kết nối HTTPS tới ALB ở cổng 443. HTTPS mã hóa kết nối từ trình duyệt đến ALB. Trên ALB có listener — thành phần nghe ở một cổng, ở đây là 443 — rồi quyết định request được chuyển đi đâu.

Đích của ALB là target group. Có thể hiểu target group như danh sách địa chỉ của những máy chạy ứng dụng mà ALB được phép gọi. Trong lab, danh sách đó có IP của hai pod `web`, cùng cổng 8080.

Vậy làm sao cấu hình trong Kubernetes tạo được tài nguyên AWS? Trong cluster có AWS Load Balancer Controller. Controller là chương trình chạy liên tục để theo dõi cấu hình và giữ tài nguyên thật khớp với cấu hình đó. Khi thấy Ingress khai báo dùng ALB, controller gọi AWS API để tạo hoặc cập nhật ALB, listener, target group và security-group rule cần thiết.

Ingress là bản khai báo về đường vào ứng dụng; nó không phải chính cái ALB. Controller là người thực hiện bản khai báo đó trên AWS. Target group là nơi ta nhìn thấy các đích mà ALB thực sự có thể gọi.

Manifest chọn `target-type: ip`, nghĩa là đăng ký IP pod vào target group. App bên trong pod lắng nghe ở cổng 8080. ALB giải mã HTTPS tại listener, rồi gửi HTTP tới pod bên trong VPC. Vì vậy client dùng HTTPS, còn đoạn ALB tới app trong lab là HTTP.

Service `web` có loại `ClusterIP`. Service là địa chỉ ổn định trong cluster để các ứng dụng nội bộ gọi `web`, kể cả khi pod được thay thế và đổi IP. Nhưng với IP target mode, ALB đi thẳng đến pod IP; request ALB không chạy qua ClusterIP và cũng không qua NodePort.

Kubernetes duy trì EndpointSlice, tức danh sách pod IP hiện đang làm backend cho Service. Controller đọc danh sách này để cập nhật target group.

Nếu một pod dừng, Deployment — cấu hình giữ số bản chạy mong muốn — tạo pod mới để duy trì hai bản sao. Pod mới có thể nhận IP khác. EndpointSlice đổi theo; controller gỡ IP cũ và thêm IP mới vào target group. ALB liên tục gọi health check `/healthz`. Khi pod mới trả kết quả khỏe, ALB bắt đầu gửi request tới nó.

Đây cũng là điểm khác cách quen thuộc ở ECS. Với ECS, mình thường gắn target group vào ECS Service và ECS Service đồng bộ các task. Với EKS, trách nhiệm được tách ra giữa Deployment, Service, Ingress và AWS Load Balancer Controller.”

**Chỉ trên trang:** [Module 6 — Ingress và NetworkPolicy](../eks-defense-in-depth/06-traffic/). Nếu có Console, mở **EC2 → Target Groups → Targets** để cho xem hai pod IP.

**Chuyển ý:** “Có route đúng chưa đủ; bây giờ xem firewall ở AWS và policy trong Kubernetes phối hợp thế nào.”

## Slide 5 — Security Group và NetworkPolicy · 3 phút

**Mục đích:** Phân biệt hai loại kiểm soát mạng và kể lại sự cố 504 đã xử lý.

**Lời thoại:**

“Security group có thể hình dung như firewall gắn ở phía AWS. Trong lab, nó chỉ nhận HTTPS từ địa chỉ client đã cho phép. Ở chiều backend, nó cho phép cổng ứng dụng 8080 từ security group của ALB. Client Internet không được kết nối tùy ý thẳng tới node hoặc pod.

NetworkPolicy là luật mạng áp cho pod. Namespace `payments` bắt đầu bằng default-deny: chặn mọi luồng vào và ra, trừ các luồng được mở rõ ràng. Sau đó lab cho phép DNS, liên lạc với Pod Identity agent, frontend test client và ALB tới app port. Tóm lại, security group bảo vệ ranh giới network của AWS; NetworkPolicy giới hạn giao tiếp giữa workload Kubernetes.

Điều kiện quan trọng là CNI phải thực thi policy. Trong lab, VPC CNI add-on bật NetworkPolicy và agent chạy trên node. Nếu chỉ `kubectl apply` một object NetworkPolicy nhưng plugin không hỗ trợ/enforce, người vận hành có thể tưởng traffic đã bị chặn trong khi thực tế chưa.

Khi kiểm tra lần đầu, Target Group báo cả hai pod healthy nhưng gọi HTTPS vào website bị lỗi 504. Health check và request người dùng là hai phép thử khác nhau; target xanh chưa chứng minh toàn bộ request path hoạt động. Mình lần theo đường đi và thấy NetworkPolicy chưa cho nguồn traffic của ALB vào pod. Thêm rule chỉ cho các CIDR của public subnets đặt ALB tới port 8080 thì `/healthz` trả HTTP 200.

Bài học là kiểm tra theo đường đi end-to-end, không dừng ở một dấu xanh. Đồng thời thử request được phép và request không được phép. Trong lab, frontend được vào `payments`; client ở namespace `default` bị timeout như mong muốn.”

**Chỉ trên trang:** [Module 6 — NetworkPolicy](../eks-defense-in-depth/06-traffic/). Có thể chiếu policy allow/deny và kết quả `/healthz`.

**Chuyển ý:** “Mạng giới hạn pod liên hệ với ai; tiếp theo là giới hạn pod được khởi chạy với cấu hình nào.”

## Slide 6 — Giảm quyền từ lúc workload được tạo · 2 phút

**Mục đích:** Giải thích Pod Security Admission và hardening container.

**Lời thoại:**

“Container đóng gói ứng dụng và thư viện của nó, nhưng không phải một máy tính hoàn toàn tách biệt. Các container trên cùng node vẫn dùng chung kernel Linux của máy đó. Nếu một container được chạy với quyền quá cao, sự cố của nó có thể ảnh hưởng tới node hoặc workload khác.

Namespace `payments` bật Pod Security Admission mức `restricted`. Có thể hiểu đây là cửa kiểm tra ở Kubernetes API: trước khi nhận một Pod mới, API kiểm tra các trường bảo mật trong manifest. Một pod khai báo privileged — tức xin quyền gần như toàn bộ máy chủ — bị từ chối ngay, trước khi container được chạy.

Các pod ứng dụng cũng được cấu hình hạn chế quyền: chạy bằng user thường thay vì root; filesystem gốc chỉ đọc; bỏ các Linux capabilities không cần. Resource request cho Kubernetes biết lượng CPU/bộ nhớ tối thiểu để sắp xếp pod; limit đặt mức sử dụng tối đa. Readiness probe là phép thử xem app đã sẵn sàng nhận request chưa; nếu chưa, Kubernetes và load balancer không nên gửi traffic tới pod đó.

Không phải cấu hình nào cũng tương thích với restricted policy. Với ứng dụng thật, nên thử ở môi trường lab, xem warning/audit, rồi áp enforcement có kế hoạch. Một lớp admission tốt ngăn cấu hình nguy hiểm ngay từ đầu, nhưng không thay thế việc cập nhật image và theo dõi runtime.”

**Chỉ trên trang:** [Module 4 — Node, namespace và pod](../eks-defense-in-depth/05-workloads/).

**Chuyển ý:** “Khi pod chạy an toàn hơn, ta cần giới hạn quyền mà con người và ứng dụng mang theo.”

## Slide 7 — Tách danh tính người vận hành và ứng dụng · 3 phút

**Mục đích:** Giải thích IAM authentication, EKS Access Entry, RBAC, service account và Pod Identity.

**Lời thoại:**

“Ở đây có hai loại danh tính. Một là danh tính của người vận hành chạy `kubectl` để xem hoặc thay đổi cluster. Hai là danh tính của ứng dụng trong pod khi nó cần gọi AWS API, chẳng hạn đọc một object từ S3. Hai loại này nên được cấp quyền riêng.

Với người dùng, IAM là dịch vụ AWS xác thực tài khoản hoặc role. EKS Access Entry nối IAM principal đó với cluster. Sau khi xác thực xong, Kubernetes RBAC quyết định người đó được xem hay thay đổi loại tài nguyên nào, trong namespace nào. Ví dụ: IAM/EKS nhận biết đây là role DevOps; RoleBinding Kubernetes giới hạn role đó vào Deployment trong `payments`.

Lab kiểm tra ba vai trò. Admin có quyền quản trị cluster. DevOps có thể triển khai ứng dụng trong namespace `payments` và xem pod/log cần thiết, nhưng không đọc Secret, sửa RoleBinding hay triển khai sang namespace khác. Observer chỉ xem pod và log, không deploy. Lệnh `kubectl auth can-i` giúp hỏi API “danh tính hiện tại có được phép làm thao tác này không?” Mình chạy cả câu trả lời `yes` lẫn `no`.

Có một điểm dễ bỏ sót: khi thử `AmazonEKSEditPolicy`, mình phát hiện policy có thể cho đọc Secret trong namespace. Secret thường chứa mật khẩu hoặc token, nên quyền này có thể rộng hơn nhu cầu của đội triển khai. Vì vậy lab dùng Kubernetes Role tự viết cho group `payments-deployers`, chỉ cấp các thao tác cần để quản lý app.

Với ứng dụng, pod chạy bằng Kubernetes ServiceAccount `web-reader`. ServiceAccount là danh tính trong cluster. EKS Pod Identity nối danh tính đó với một IAM role; agent trên node giúp AWS SDK trong container lấy credential tạm thời. Nhờ vậy mình không phải ghi access key dài hạn vào source code, container image hoặc manifest.

Role mẫu của app không có quyền AWS vì app không cần gọi dịch vụ AWS. Node role cũng là một danh tính riêng dành cho node, ví dụ để kéo image; không nên để application tự thừa hưởng quyền node. Tách danh tính giúp giảm blast radius nếu một pod bị khai thác.”

**Chỉ trên trang:** [Module 6 — Human access/RBAC](../eks-defense-in-depth/04-identity/) và [Module 7 — Pod Identity](../eks-defense-in-depth/07-workload-identity/).

**Chuyển ý:** “Ngăn chặn và phân quyền tốt nhưng vẫn cần biết ai đã thay đổi gì; đó là vai trò của logging và detection.”

## Slide 8 — Quan sát để trả lời: ai làm gì, kết nối đi đâu? · 2 phút

**Mục đích:** Nêu nguồn telemetry, giới hạn của detection và những gì chưa cấu hình.

**Lời thoại:**

“EKS audit log ghi lại hoạt động với Kubernetes API: danh tính nào gọi, thao tác gì và tài nguyên nào bị tác động. VPC Flow Logs ghi thông tin metadata về kết nối mạng, ví dụ địa chỉ nguồn/đích và trạng thái cho phép hay từ chối. GuardDuty Runtime Monitoring phân tích tín hiệu trên node để tìm hành vi đáng ngờ. CloudTrail lưu hoạt động gọi AWS API, như thay đổi IAM hoặc EKS. Tài khoản có organization CloudTrail từ trước; lab giữ nguyên cấu hình dùng chung đó.

Những nguồn này giúp phát hiện và điều tra; chúng không tự chặn request của ứng dụng. Finding cần người xem xét và quy trình phản ứng. Log cần thời hạn lưu trữ và quyền truy cập có kiểm soát. Alert cần người nhận và quy trình làm tiếp.

Trong sandbox có EKS control-plane logs, VPC Flow Logs và GuardDuty coverage để kiểm tra. WAF, Route 53, certificate domain công khai và SNS/email alert chưa cấu hình. Đây là phần cần triển khai bổ sung nếu biến workshop thành môi trường production.”

**Chỉ trên trang:** [Module 8 — Audit và threat detection](../eks-defense-in-depth/08-detection/) và [Module 9 — Incident response](../eks-defense-in-depth/09-response/).

**Chuyển ý:** “Giờ gom lại các bằng chứng để xem mình đã chứng minh điều gì, thay vì chỉ nhìn dịch vụ đang ở trạng thái Active.”

## Slide 9 — Đừng chỉ nhìn trạng thái xanh: thử allow và deny · 2 phút 30 giây

**Mục đích:** Tóm lược kiểm chứng end-to-end.

**Lời thoại:**

“Mình không chỉ kiểm tra rằng các tài nguyên đã được tạo; mình thử hành vi thực tế. Về mạng, ALB đặt ở public subnet còn node ở private subnet và không có public IP. Về đường vào, target group có hai pod IP ở cổng 8080. Về NetworkPolicy, frontend được vào ứng dụng còn client ở namespace `default` bị chặn.

Về admission, Kubernetes API từ chối pod privileged trước khi chạy. Về RBAC, DevOps triển khai được trong phạm vi cần thiết nhưng không đọc Secret hoặc làm việc ngoài namespace. Về Pod Identity, AWS SDK bên trong app nhận credential provider `container-role`; endpoint kiểm thử chỉ trả tên provider và thời hạn, không trả access key hay token.

Về quan sát, mình tạo thay đổi Kubernetes có kiểm soát rồi tìm nó trong audit log ở CloudWatch. Mình cũng kiểm tra Flow Logs đang gửi dữ liệu và GuardDuty báo coverage trên node. Những kiểm tra này cho biết dữ liệu có đi tới nơi cần đến hay không; một ảnh chụp chữ `ACTIVE` riêng lẻ chưa chứng minh pipeline đầy đủ.

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

“Mình có thể tóm tắt kiến trúc bằng năm nhóm. Cửa vào ứng dụng là ALB HTTPS; Kubernetes API của sandbox vẫn có public endpoint nhưng giới hạn vào một địa chỉ quản trị `/32`. Mạng bên trong gồm worker/pod private, security group và NetworkPolicy. Workload bị giới hạn bởi Pod Security Admission và container chạy non-root, filesystem chỉ đọc. Danh tính được tách giữa người dùng và ứng dụng. Cuối cùng, audit log, Flow Logs và GuardDuty cung cấp tín hiệu để điều tra.

Các lựa chọn đều có giá phải trả. `/32` giúp máy quản trị chạy CLI nhưng private-only sẽ giảm thêm bề mặt public. Một NAT rẻ hơn hai NAT nhưng tạo phụ thuộc một AZ. IP targets giúp ALB gọi pod trực tiếp nên không cần NodePort, nhưng yêu cầu pod có IP VPC routable và security group cùng NetworkPolicy cho đúng luồng.”

**Chuyển ý:** “Slide cuối là checklist để trình bày trực tiếp bằng các trang Hugo và Console.”

## Slide 11 — Thứ tự demo trên Hugo/Console · 2 phút 30 giây

**Mục đích:** Hướng dẫn người nghe tự kiểm tra từng cấu hình.

**Lời thoại:**

“Khi trình bày trực tiếp, mình đi cùng chiều với request. Đầu tiên mở VPC Resource Map để chỉ đâu là public/private subnet, Internet Gateway và NAT. Tiếp theo mở EC2 Target Groups để chỉ hai pod IP và trạng thái healthy — tức health check đang thành công. Sau đó vào Kubernetes để đối chiếu: Ingress khai báo đường vào, Service ClusterIP dùng nội bộ, còn EndpointSlice liệt kê các pod IP hiện tại.

Tiếp theo mở NetworkPolicy và kể câu chuyện 504. Điều này cho thấy khi thấy lỗi, mình lần theo từng hop thay vì mở rộng firewall thật rộng. Sau đó xem security context của pod, chuyển sang kubeconfig đã đăng nhập bằng role DevOps và chạy `kubectl auth can-i` để minh họa quyền được phép hoặc từ chối. Cuối cùng mở audit logs, Flow Logs và GuardDuty để nói về điều tra.

Trước buổi nói, xác nhận cluster và tài nguyên đang tồn tại trong đúng AWS account/region; menu Console và dữ liệu thay đổi theo vùng. Nếu lab đã dọn, dùng ảnh chụp hoặc chạy lại các bước tạo lab trước buổi demo. Không chiếu credential, account ID, role ARN hay IP cá nhân. Tài nguyên AWS thật có thể phát sinh phí; sau khi trình bày xong, cleanup trong đúng sandbox account.”

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
