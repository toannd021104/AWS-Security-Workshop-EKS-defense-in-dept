---
title: "Network Segmentation với Kubernetes NetworkPolicy"
weight: 2
chapter: false
pre: "<b>3.2.</b> "
---

## Vấn đề

Frontend cần gọi API, nhưng một pod không thuộc ứng dụng không cần kết nối đó. Khi chưa có NetworkPolicy, hai pod có thể đều truy cập API. Bài này kiểm tra trạng thái ban đầu rồi giới hạn kết nối, đồng thời giữ nguyên chức năng lưu ghi chú và tạo báo cáo.

## Kiến thức cần dùng

NetworkPolicy chọn pod bằng labels và khai báo các kết nối ingress hoặc egress được phép. Khi một pod đã được cô lập ở một chiều, lưu lượng thuộc chiều đó phải khớp ít nhất một allow rule. Các policies cộng dồn; một policy cho phép quá rộng có thể làm mất giới hạn mong muốn. Trước khi thực hành, bật policy enforcement theo [bài 3.3](/3-kubernetes-security/3-vpc-cni/).

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

## Thực hiện

### Ghi nhận kết nối trước khi áp dụng policy

Mở EKS Resources để xem labels của frontend và API. Trong terminal, xác nhận ứng dụng đã hoạt động và namespace chưa có NetworkPolicy từ một lượt thực hành trước:

```bash
source scripts/env.sh
kubectl get networkpolicy -n notes
python3 scripts/network-proof.py --stage before
```

Script tạo hai pod thử nghiệm tuân thủ Restricted, dùng cùng image đã triển khai nhưng mang labels khác nhau. Khi chưa có policy, frontend và pod `untrusted` đều kết nối được đến API. Script cũng kiểm tra lưu ghi chú và tạo báo cáo, sau đó xóa các probe pods.

Nếu policy đã tồn tại, script dừng để tránh ghi nhận sai baseline. Khi thực hành lại trên lab đã harden, dùng phần kiểm chứng sau policy; không cần xóa policy đang bảo vệ ứng dụng.

### Áp dụng NetworkPolicy

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

## Kiểm chứng kết quả

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
