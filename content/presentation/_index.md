---
title: "Vietnamese presentation guide"
weight: 2
chapter: false
---

# Kịch bản trình bày: Phòng thủ theo chiều sâu cho Amazon EKS

**Thời lượng:** khoảng 12–15 phút, chưa tính hỏi đáp. Trang này được viết để bạn mở Hugo và trình bày lần lượt theo các phần bên dưới.

{{% notice note %}}
Kịch bản mô tả trạng thái sandbox đã kiểm chứng: hai pod `web`, Service `ClusterIP`, ALB dùng IP targets, EKS API private và public giới hạn một CIDR `/32`. WAF, Route 53 và certificate domain công khai chưa được cấu hình. ALB đang dùng certificate thử nghiệm ACM.
{{% /notice %}}

## 1. Mở đầu: câu hỏi bảo mật

**Lời dẫn:**

“Hôm nay mình sẽ đi theo hành trình của một request từ Internet vào ứng dụng Kubernetes, rồi xem mỗi ranh giới bảo vệ request và workload như thế nào. Mục tiêu không chỉ là tạo cluster chạy được. Mình muốn chỉ ra ai được truy cập, họ được làm gì, pod được kết nối đi đâu, và mình có bằng chứng gì khi có sự cố.”

“Phòng thủ theo chiều sâu nghĩa là có nhiều lớp kiểm soát độc lập. Nếu một lớp cấu hình sai, nó không nên tự động làm mọi lớp phía sau mất tác dụng.”

## 2. AWS, Kubernetes và EKS

**Lời dẫn:**

“AWS cung cấp mạng và máy tính: VPC, subnet, EC2, IAM và load balancer. Kubernetes điều phối container bằng cách nhận trạng thái mong muốn rồi liên tục đưa hệ thống về trạng thái đó. EKS là Kubernetes được AWS quản lý ở phần control plane.

Trong lab, AWS quản lý Kubernetes API server và control plane. Worker node là EC2 trong VPC của lab. Pod là đơn vị chạy ứng dụng; Deployment giữ đủ số pod mong muốn. Mình yêu cầu hai bản sao `web`, nên khi một pod hỏng Kubernetes tạo pod khác để bù.”

**Chỉ trên trang:** Module [EKS control plane](../eks-defense-in-depth/03-cluster/) và Module [workload hardening](../eks-defense-in-depth/05-workloads/).

## 3. VPC và subnet: đặt ranh giới mạng

**Lời dẫn:**

“VPC là mạng riêng của lab. Mạng trải trên hai Availability Zone. ALB nằm trong public subnets để nhận HTTPS từ client; worker node và pod nằm trong private subnets và không có public IP. Route table public có đường tới Internet Gateway. Private subnet dùng một NAT Gateway cho outbound.

NAT Gateway cho phép workload gọi ra ngoài theo kết nối được khởi tạo từ trong VPC; nó không tự mở cổng inbound tới node. Lab dùng một NAT để tiết kiệm chi phí, nhưng đây không phải phương án chịu lỗi AZ hoàn chỉnh.”

**Chỉ trên trang:** Module [VPC và subnet](../eks-defense-in-depth/02-network/), hoặc ảnh VPC Resource Map bạn tự chụp.

## 4. Request đi từ ALB tới pod thế nào?

**Lời dẫn:**

“Đường request là: client được phép gọi ALB qua HTTPS cổng 443; ALB chuyển request tới target group; target group hiện chứa IP của hai pod `web` trên cổng 8080.

Ingress là đối tượng cấu hình trong Kubernetes. AWS Load Balancer Controller chạy trong cluster, theo dõi Ingress và trạng thái pod, rồi gọi AWS API để tạo ALB, listener và target group. Vì Ingress chọn `target-type: ip`, controller đăng ký pod IP trực tiếp. Service `web` vẫn là `ClusterIP` cho truy cập nội bộ ổn định; ALB không forward qua NodePort hay ClusterIP trong chế độ này.”

```text
Client → ALB :443 → Target Group → Pod web IP :8080

Workload nội bộ → Service web (ClusterIP) → các pod web
```

“Nếu pod thay thế và nhận IP mới, Kubernetes cập nhật EndpointSlice. Controller thấy endpoint thay đổi và cập nhật target group; ALB kiểm tra health rồi gửi traffic tới pod khỏe.”

**So sánh ECS:** “Trong ECS, mình thường gắn target group trực tiếp vào ECS Service; ECS Service theo dõi task. Trong EKS, trách nhiệm này chia qua Deployment, Service, Ingress và Load Balancer Controller.”

**Chỉ trên trang:** Module [Ingress và NetworkPolicy](../eks-defense-in-depth/06-traffic/). Nếu có quyền Console, mở EC2 → Target Groups → Targets để chỉ hai pod IP.

## 5. Security group và NetworkPolicy

**Lời dẫn:**

“Security group là firewall ở cấp AWS network interface. ALB chỉ nhận HTTPS từ CIDR được cho phép; node/pod network chỉ nhận cổng ứng dụng từ security group của ALB.

NetworkPolicy giới hạn giao tiếp giữa pod. Namespace `payments` mặc định chặn ingress và egress, sau đó chỉ mở DNS, Pod Identity agent, client kiểm thử frontend và đường ALB tới app. VPC CNI đã bật chế độ thực thi NetworkPolicy; nếu chỉ apply YAML mà CNI không enforce thì policy không chặn gói tin.”

“Khi kiểm thử, target group báo healthy nhưng HTTPS trả 504. Health check thành công chưa chứng minh request người dùng qua hết các ranh giới. Mình tìm thấy NetworkPolicy thiếu nguồn của ALB; thêm rule chỉ cho CIDR public subnets của ALB vào port ứng dụng thì `/healthz` trả 200. Đây là ví dụ vì sao phải kiểm tra end-to-end và cả chiều allow lẫn deny.”

## 6. Namespace, pod và admission security

**Lời dẫn:**

“Namespace `payments` gom các tài nguyên của app, nhưng namespace một mình không phải ranh giới bảo mật đầy đủ. Pod Security Admission mức `restricted` từ chối workload cấu hình quá quyền.

Các pod app chạy non-root, filesystem chỉ đọc, bỏ Linux capabilities không cần và có resource limits cùng health probes. Mình thử manifest privileged trong sandbox; Kubernetes API từ chối trước khi pod được chạy.”

**Chỉ trên trang:** Module [node, namespace và pod](../eks-defense-in-depth/05-workloads/).

## 7. Danh tính con người và ứng dụng

**Lời dẫn:**

“Người vận hành và ứng dụng cần hai bộ quyền khác nhau. Với người, IAM xác thực danh tính AWS; EKS Access Entry nối principal đó với cluster; Kubernetes RBAC quyết định quyền trên resource và namespace.

Lab kiểm tra ba mức: admin, DevOps và observer. DevOps deploy trong `payments` nhưng không đọc Secret, không sửa RBAC và không deploy namespace khác. Observer chỉ đọc pod/log. Dùng `kubectl auth can-i` để kiểm tra quyền được phép và bị từ chối.

Ứng dụng dùng Kubernetes service account `web-reader`, gắn với IAM role qua EKS Pod Identity. Pod nhận credential ngắn hạn; không nhúng access key trong image. Role của app mẫu không có quyền AWS vì app không cần gọi dịch vụ AWS. Node role là danh tính cho node, không phải quyền mặc định của ứng dụng.”

**Chỉ trên trang:** Module [IAM và Kubernetes RBAC](../eks-defense-in-depth/04-identity/) và Module [Pod Identity](../eks-defense-in-depth/07-workload-identity/).

## 8. Logging và phát hiện

**Lời dẫn:**

“EKS control-plane audit logs giúp trả lời ai gọi Kubernetes API và đã thay đổi gì. VPC Flow Logs ghi metadata kết nối mạng. GuardDuty Runtime Monitoring cung cấp tín hiệu phát hiện trên node. CloudTrail của tổ chức đã tồn tại nên lab giữ nguyên, không tạo hoặc sửa trail đó.

Log và GuardDuty là lớp quan sát/phát hiện; chúng không tự chặn request. Muốn phát hiện có ích cần retention, người nhận cảnh báo và quy trình phản ứng. Sandbox chưa cấu hình WAF hay email/SNS alert.”

**Chỉ trên trang:** Module [audit và threat detection](../eks-defense-in-depth/08-detection/), sau đó [incident response](../eks-defense-in-depth/09-response/).

## 9. Kết luận

**Lời dẫn:**

“Tóm lại: ALB public nhận HTTPS; worker node và pod ở private subnet; ALB IP target tới pod trực tiếp; Service ClusterIP phục vụ truy cập nội bộ; security group và NetworkPolicy giới hạn mạng; Pod Security Admission giới hạn cấu hình container; IAM, Access Entry, RBAC và Pod Identity tách quyền; audit log và GuardDuty hỗ trợ điều tra.

Không nên kết luận hệ thống an toàn chỉ vì một biểu tượng báo xanh. Hãy vẽ đường đi, xác định từng ranh giới, kiểm tra kết quả thật và thử cả đường được phép lẫn đường phải bị chặn.”

## Demo nhanh

```bash
kubectl get nodes -o wide
kubectl get deploy,pods,svc -n payments -o wide
kubectl get ingress,endpointslice -n payments -o wide
kubectl --context eks-depth-devops auth can-i get secrets -n payments
```

Qua HTTPS, gọi `/healthz` từ mạng có CIDR được ALB cho phép. Trước khi chiếu terminal hoặc Console, che account ID, IP cá nhân, role ARN, endpoint và thông tin không thuộc lab.

## Phạm vi và trade-off cần nói rõ

- EKS API trong sandbox bật private endpoint và public endpoint giới hạn một CIDR `/32`; chưa phải private-only.
- WAF và Route 53 chưa được tạo. ALB dùng DNS do AWS cấp; certificate ACM là chứng chỉ thử nghiệm, không phải certificate domain production.
- Một NAT Gateway giúp giảm chi phí nhưng tạo phụ thuộc AZ. Hai AZ của node không đồng nghĩa mọi thành phần đều HA.
- Image ECR của lần thử trước có findings bảo mật; cần build lại từ base image đã cập nhật và scan trước khi sử dụng ngoài lab.
- Đây là lab học tập trên AWS thật. Kiểm tra chi phí và chạy module cleanup khi môi trường không còn cần thiết.
