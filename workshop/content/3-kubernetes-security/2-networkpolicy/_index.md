---
title: "Network Segmentation với Kubernetes NetworkPolicy"
weight: 2
chapter: false
pre: "<b>3.2.</b> "
---

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
