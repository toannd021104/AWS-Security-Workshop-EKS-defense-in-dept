---
title: "Network Security – Securing the Request Path"
weight: 3
chapter: false
pre: "<b>2.</b> "
---

Notes đã hoạt động qua domain HTTPS ở bước baseline. Bây giờ cần giải thích được vì sao request từ Internet đến được frontend trong private subnet, và những kết nối nào được lớp mạng AWS cho phép.

Bắt đầu từ một request thật, đối chiếu ALB target với pod IP rồi đọc ngược về subnets, routes và Security Groups. Tiếp tục kiểm tra HTTPS, WAF và cách controller quản lý backend. Các tài nguyên nền đã được tạo ở phần chuẩn bị; các bài chỉ rõ khi nào cần quan sát và khi nào cần thay đổi cấu hình.

Hoàn thành [baseline](/preparation/8-baseline/) trước bài 2.1. Cuối phần này, cần đối chiếu được cả request HTTPS trả 200 và request thử WAF trả 403. Giới hạn kết nối giữa pod được tiếp tục ở chương 3.

## Các bài trong phần này

2.1. [Request Flow: Internet → ALB → Pod](/2-network-security/1-request-flow/)

2.2. [VPC Architecture: Public & Private Subnets, Routing, NAT Gateway](/2-network-security/2-vpc/)

2.3. [Edge Security: AWS WAF, ALB và HTTPS](/2-network-security/3-edge/)

2.4. [Network Access Control: Security Groups & NACLs](/2-network-security/4-security-groups/)

2.5. [AWS Load Balancer Controller và Kubernetes Ingress](/2-network-security/5-controller-ingress/)

2.6. [ALB Target Types: Instance vs IP](/2-network-security/6-target-types/)
