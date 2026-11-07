---
title: "Tổng kết: các lớp bảo vệ đã kiểm chứng"
weight: 70
chapter: false
pre: ""
---

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
