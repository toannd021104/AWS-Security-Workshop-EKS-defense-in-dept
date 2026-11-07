# Kịch bản thuyết trình: Phòng thủ theo chiều sâu cho Amazon EKS

**Thời lượng gợi ý:** 12–15 phút, chưa tính hỏi đáp  
**Đối tượng:** Người biết cơ bản về AWS hoặc Kubernetes; không cần từng vận hành EKS  
**Mục tiêu:** Giải thích lab đã dựng gì, request đi qua đâu, từng lớp bảo vệ xử lý rủi ro nào, và những giới hạn nào đã thấy khi chạy thật.

> **Lưu ý cho người thuyết trình:** Đây là kịch bản cho cấu hình sandbox đã chạy. ALB dùng IP targets, Service `ClusterIP`, hai pod `web`. Public API endpoint của EKS vẫn bật nhưng giới hạn một CIDR `/32`; vì vậy đừng nói API hoàn toàn private. Lab chưa cấu hình WAF, Route 53, email alert hay chứng chỉ domain công khai. Chứng chỉ ACM được import để thử HTTPS. Trước khi chiếu console, che account ID, IP cá nhân, role ARN và DNS nếu không muốn công khai.

---

## 1. Mở đầu — vấn đề chúng ta giải quyết (1 phút)

**Nói:**

“Hôm nay mình sẽ trình bày một lab Amazon EKS bảo vệ ứng dụng theo nhiều lớp. Mục tiêu không phải chỉ tạo cluster chạy được. Mình muốn trả lời ba câu hỏi: người dùng đi vào ứng dụng bằng đường nào, nếu một pod bị lỗi hoặc bị xâm nhập thì nó bị giới hạn ra sao, và khi có thay đổi thì mình tìm bằng chứng ở đâu.

EKS giúp AWS quản lý Kubernetes control plane, nhưng phần mạng, node, quyền IAM, quyền Kubernetes và cấu hình workload vẫn cần mình thiết kế. Một lớp như subnet private không giải quyết được mọi rủi ro. Vì vậy lab ghép nhiều ranh giới độc lập lại với nhau.”

**Chuyển ý:** “Trước tiên, mình phân biệt nhanh AWS, EKS và Kubernetes.”

---

## 2. Nền tảng: AWS, Kubernetes và EKS là gì? (1–2 phút)

**Nói:**

“AWS cung cấp hạ tầng như VPC, subnet, EC2, IAM, load balancer và dịch vụ quản lý. Kubernetes là hệ thống điều phối container: mình khai báo trạng thái mong muốn, ví dụ ứng dụng cần hai bản chạy; Kubernetes tạo và thay pod để tiến gần trạng thái đó.

EKS là dịch vụ Kubernetes được AWS quản lý. Control plane — nơi nhận lệnh Kubernetes và lưu trạng thái cluster — do AWS vận hành. Worker node là máy EC2 trong tài khoản/VPC của mình; pod chạy trên các node đó. EKS không làm ứng dụng tự an toàn: mình vẫn phải giới hạn ai được gọi API, pod nào được nói chuyện với pod nào và container được phép làm gì.”

**Giải thích các từ khóa trên sơ đồ:**

- **Deployment:** khai báo muốn chạy bao nhiêu bản sao của ứng dụng và cách cập nhật chúng.
- **Pod:** đơn vị nhỏ nhất Kubernetes triển khai; thường chứa một container ứng dụng.
- **Service:** địa chỉ và cơ chế chọn nhóm pod theo label.
- **Ingress:** khai báo HTTP/HTTPS từ bên ngoài nên được route tới service nào. Bản thân Ingress chỉ là cấu hình Kubernetes.
- **AWS Load Balancer Controller:** chương trình chạy trong cluster, đọc Ingress và gọi AWS API để tạo/cập nhật ALB cùng target group.

---

## 3. Kiến trúc tổng thể và đường request (2 phút)

**[Chiếu sơ đồ architecture trong Module 1 hoặc VPC Resource Map.]**

**Nói:**

“VPC lab trải trên hai Availability Zone. Mỗi AZ có public subnet và private subnet. ALB ở public subnets để nhận kết nối HTTPS từ client. Hai EC2 worker node ở private subnets và không có public IP. Một NAT Gateway cho node đi outbound; lab dùng một NAT để giảm phí nên đây là lựa chọn tiết kiệm, không phải cấu hình HA hoàn chỉnh.

Đường request thật của lab là: client được phép → ALB cổng 443 → target group → IP của một trong hai pod `web` ở cổng 8080. ALB và pod liên lạc qua mạng VPC. EKS API dùng để quản trị cluster là một đường khác; nó không phải đường mà request web đi qua.”

**Vẽ hoặc chỉ theo đường đi:**

```text
Client → ALB :443 → Target Group → Pod web IP :8080
                                      ↑
                         Deployment giữ 2 pod

Ứng dụng trong cluster → Service web (ClusterIP) → các pod web
```

**Nói tiếp:**

“Trong cấu hình này Service `web` vẫn tồn tại với loại `ClusterIP`, để các workload bên trong cluster gọi ứng dụng qua địa chỉ ổn định. Nhưng vì ALB dùng IP targets, ALB chuyển thẳng đến pod IP; nó không đi qua NodePort hay ClusterIP để forward request. Ingress Controller theo dõi EndpointSlice của Service để biết pod IP nào đang sẵn sàng rồi đăng ký chúng vào target group.”

---

## 4. ALB, Ingress và target group hoạt động cùng nhau thế nào? (2 phút)

**[Chiếu EKS → Ingress và EC2 → Target Groups; có thể đối chiếu `kubectl get ingress,svc,endpointslice -n payments` với console.]**

**Nói:**

“Mình khai báo một Ingress có listener HTTPS, chứng chỉ ACM và annotation `target-type: ip`. AWS Load Balancer Controller đọc cấu hình đó rồi tạo ALB, listener, target group và các rule mạng cần thiết. Target group là danh sách đích của ALB. Hiện danh sách có hai pod IP trên port 8080.

Kubernetes Deployment giữ hai bản sao. Nếu một pod bị dừng, Kubernetes tạo pod thay thế. IP của pod mới có thể khác. Service cập nhật EndpointSlice, controller thấy thay đổi đó rồi cập nhật target group. ALB chỉ gửi traffic tới đích qua được health check `/healthz`.

Vì thế cần ba thứ khác nhau: Ingress mô tả lối vào; controller biến mô tả đó thành tài nguyên AWS; target group là danh sách đích mà ALB thực sự gọi.”

**Phân biệt với ECS:**

“Trong ECS, mình thường gắn target group trực tiếp vào ECS Service; ECS Service theo dõi task và cập nhật target group. Trong EKS, trách nhiệm được chia giữa Deployment, Service, Ingress và Load Balancer Controller. Ý tưởng target group tương tự, cách khai báo và thành phần đồng bộ khác nhau.”

**Nói rõ phạm vi demo:**

“Lab đang có HTTPS listener và giới hạn CIDR nguồn. Chứng chỉ ACM là chứng chỉ thử nghiệm được import, chưa phải certificate domain công khai. WAF và Route 53 được trình bày như lựa chọn trong tài liệu nhưng chưa tạo trong lần chạy này.”

---

## 5. Lớp mạng: subnet, security group và NetworkPolicy (2 phút)

**Nói:**

“Subnet public hay private được quyết định bởi route table, không phải tên subnet. Public subnet có route tới Internet Gateway; private subnet không có route inbound trực tiếp từ Internet. Node đi outbound qua NAT, nhưng NAT không tự mở đường inbound tới node.

Security group đặt ranh giới ở mức ENI/tài nguyên AWS. ALB chỉ nhận HTTPS từ CIDR đã cho phép. Security group của node/pod network chỉ cho port ứng dụng 8080 từ security group của ALB.

NetworkPolicy đặt ranh giới ở mức pod. Namespace `payments` mặc định chặn ingress và egress, sau đó mở đúng các luồng cần thiết: DNS, Pod Identity agent, client kiểm thử frontend và traffic từ subnet đặt ALB. NetworkPolicy chỉ có hiệu lực vì VPC CNI đã bật chức năng enforcement; tạo YAML thôi chưa đủ.”

**Bài học production thực tế:**

“Lần đầu target group báo healthy nhưng gọi HTTPS bị 504. Điều đó cho thấy health check thành công chưa chắc request thực tế được phép qua mọi lớp. Mình kiểm tra đường đi và phát hiện NetworkPolicy chưa cho nguồn của ALB vào pod. Sau khi thêm rule giới hạn theo CIDR public subnet của ALB, `/healthz` trả 200. Mình kiểm tra riêng cả security group lẫn NetworkPolicy vì hai lớp giải quyết hai loại ranh giới khác nhau.”

---

## 6. Lớp workload: nếu pod bị xâm nhập thì sao? (1 phút)

**[Chiếu Deployment và namespace labels; nếu demo trực tiếp, dùng lệnh dry-run từ Module 4.]**

**Nói:**

“Ứng dụng chạy hai pod trong namespace `payments`. Namespace giúp gom tài nguyên và áp chính sách, nhưng tự nó không phải một ranh giới bảo mật hoàn chỉnh.

Namespace bật Pod Security Admission mức `restricted`. Container chạy non-root, filesystem root chỉ đọc, bỏ Linux capabilities không cần thiết, có resource requests/limits và health probes. Khi thử tạo một pod privileged, Kubernetes API từ chối ngay lúc admission. Như vậy cấu hình nguy hiểm bị chặn trước khi container chạy.”

---

## 7. Danh tính con người và danh tính ứng dụng (2 phút)

**Nói:**

“Có hai câu hỏi quyền khác nhau. Một người dùng `kubectl` được làm gì? Và ứng dụng trong pod được gọi AWS API nào?

Với con người, IAM xác thực danh tính AWS; EKS Access Entry ánh xạ principal vào cluster; Kubernetes RBAC quyết định quyền trên resource và namespace. Lab có admin, DevOps và observer. DevOps được deploy trong `payments` nhưng không đọc Secret, không quản trị RBAC và không thao tác namespace khác. Observer xem pod và log nhưng không deploy. Mình kiểm chứng bằng `kubectl auth can-i`, cả trường hợp được phép lẫn bị từ chối.

Với workload, pod dùng Kubernetes service account `web-reader`, được liên kết qua EKS Pod Identity với IAM role. Pod nhận credential ngắn hạn từ Pod Identity Agent; không nhét access key tĩnh vào image hoặc YAML. Role của app mẫu hiện không có quyền AWS vì app chỉ kiểm tra credential provider, không cần gọi dịch vụ AWS.

IAM role của node là danh tính máy cho tác vụ của node, không nên dùng làm quyền của ứng dụng. Tách ba danh tính này giúp nếu app bị xâm nhập thì nó không mặc nhiên có quyền như node hay người quản trị.”

---

## 8. Logging, phát hiện và phản ứng (1–2 phút)

**Nói:**

“Phòng thủ không chỉ là ngăn chặn; mình cần biết chuyện gì đã xảy ra. EKS gửi control-plane audit và authenticator logs tới CloudWatch. VPC Flow Logs ghi metadata kết nối mạng. CloudTrail ghi hoạt động AWS API; tài khoản này đã có organization trail sẵn nên lab không sửa trail đó. GuardDuty Runtime Monitoring có coverage khỏe trên node và mình tạo finding mẫu để xem luồng phát hiện.

Các log này là bằng chứng và tín hiệu phát hiện, không tự chặn request. Khi ứng cứu, cần xác định pod, service account, image, node và phạm vi kết nối; lưu bằng chứng; giới hạn traffic; thu hồi quyền liên quan; sau đó thay image sạch và khôi phục workload.”

**Nói rõ việc chưa làm:**

“Email/SNS notification và WAF chưa được cấu hình trong sandbox này. Nếu triển khai thật, cần người nhận alert, quy trình xử lý và kiểm thử alert end-to-end; bật một dịch vụ mà không có người phản hồi chưa tạo thành quy trình phát hiện hoàn chỉnh.”

---

## 9. Kết luận (30–45 giây)

**Nói:**

“Tóm lại, mình dựng một đường vào rõ ràng: ALB public nhận HTTPS, target group chuyển đến pod IP private, còn node không có public IP. ClusterIP phục vụ gọi nội bộ; Ingress và AWS Load Balancer Controller kết nối EKS với tài nguyên ALB. Security group giới hạn kết nối ở mức AWS, NetworkPolicy giới hạn kết nối ở mức pod, Pod Security Admission giới hạn cấu hình container, RBAC và Pod Identity tách quyền người với quyền ứng dụng, còn logs và GuardDuty hỗ trợ điều tra.

Điểm quan trọng là mỗi lớp cần được kiểm chứng. Một trạng thái ‘healthy’ ở một dịch vụ không chứng minh toàn bộ request path hoạt động. Mình đã gặp 504, lần theo từng lớp và sửa đúng policy bị thiếu. Đó là cách tiếp cận mình muốn mọi người mang về: vẽ đường đi, xác định mỗi ranh giới, thử cả allow lẫn deny và kiểm tra bằng chứng.”

---

## Demo ngắn khi thuyết trình

Chạy các lệnh này trước buổi nói và chỉ chiếu output đã kiểm tra, không để lộ account ID, IP cá nhân hoặc credential:

```bash
kubectl get nodes -o wide
kubectl get deploy,pods,svc -n payments -o wide
kubectl get ingress,endpointslice -n payments -o wide
kubectl --context eks-depth-devops auth can-i get secrets -n payments
```

Với ALB, mở **EC2 → Target Groups → target group của app → Targets** để chỉ ra hai pod IP và trạng thái health. Sau đó gọi `/healthz` qua HTTPS từ mạng nằm trong CIDR được phép. Để kiểm tra quyền DevOps thật, chuyển sang kubeconfig context đã xác thực bằng IAM role DevOps rồi chạy `kubectl auth can-i`; không chỉ giả lập tên user bằng `--as`, vì cách đó chưa kiểm tra IAM authentication.

## Câu hỏi thường gặp

**“Sao ALB ở public subnet mà pod ở private subnet?”**  
ALB cần nhận kết nối từ Internet; pod không cần địa chỉ Internet. ALB đi vào pod qua mạng VPC và security group chỉ cho phép luồng dự định.

**“Service ClusterIP có nối request ALB không?”**  
Trong cấu hình IP targets này, ALB đi thẳng đến pod IP. Service vẫn cung cấp endpoint nội bộ ổn định và selector/EndpointSlice để Kubernetes cùng controller biết pod nào là backend.

**“Pod đổi IP thì target group có stale IP không?”**  
Deployment tạo pod thay thế, EndpointSlice đổi theo pod đang sẵn sàng, controller cập nhật target group; ALB gửi traffic khi target mới qua health check.

**“Vì sao không mở port 8080 cho cả VPC?”**  
Vì chỉ ALB cần gọi ứng dụng từ bên ngoài cluster. Mở rộng nguồn làm tăng phạm vi có thể tiếp cận; giới hạn security group theo ALB và policy theo subnet/pod giúp giảm blast radius.

**“Đây đã là production-ready chưa?”**  
Chưa. Đây là lab chạy trên AWS thật để minh họa và kiểm chứng các cơ chế. Cần thay chứng chỉ thử bằng certificate domain thật, bổ sung WAF/alert theo yêu cầu, rà findings image, chọn NAT/VPC endpoints theo HA và chi phí, cùng quy trình quản lý secret, backup và ứng cứu phù hợp môi trường thực tế.
