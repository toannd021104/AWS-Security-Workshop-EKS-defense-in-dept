"""Shared English labels for the editable workshop diagrams."""
EN = {
 'Người dùng': 'User', 'Điểm vào ứng dụng': 'Application entry',
 'Xử lý nghiệp vụ': 'Business logic', 'Dữ liệu': 'Data', 'Hàng đợi': 'Queue',
 'Tạo báo cáo': 'Generate reports', 'Gửi yêu cầu': 'Send request',
 'Nhận yêu cầu': 'Poll requests', 'DNS → địa chỉ ALB': 'DNS → ALB address',
 'Kết thúc TLS': 'TLS termination', 'Queue của workload': 'Workload queue',
 'Namespace + tên SA': 'Namespace + SA name', 'Quyền trên queue': 'Queue permissions',
 'Yêu cầu credentials': 'Request credentials', 'Trả temporary credentials': 'Return credentials',
 'HTTPS ký SigV4': 'SigV4-signed HTTPS', 'Người quản trị': 'Operator',
 'Token xác thực': 'Authentication token', 'Kiểm tra identity': 'Authenticate identity',
 'Kiểm tra quyền': 'Authorize request', 'Gửi request': 'Send request',
 'Ánh xạ / cấp quyền': 'Map / authorize', 'Cho phép thao tác': 'Allow operation',
 'Ký image digest': 'Sign image digest', 'Sau khi đạt gate': 'After gate approval',
 'Kiểm tra trước chạy': 'Verify before execution', 'Đánh giá kết quả': 'Review results',
 'Pod không tin cậy': 'Untrusted pod', 'Không được gọi API': 'API access denied',
 'Bài thực hành encrypt / decrypt': 'Encrypt / decrypt exercise',
 'Vị trí pod minh họa; scheduler phân bố replicas trên các node.': 'Illustrative placement; the scheduler distributes replicas across nodes.',
 'Database subnets · RDS private / Single-AZ trong lab': 'Database subnets · Private RDS / Single-AZ lab',
 'Chỉ outbound': 'Outbound only', 'Xử lý báo cáo': 'Process reports',
 'Hàng đợi báo cáo': 'Report queue', 'Gắn Web ACL / certificate với ALB': 'Associate Web ACL / certificate with ALB',
 'Qua IGW · HTTPS :443': 'Via IGW · HTTPS :443',
}

def translate(text, language):
    if language != 'en':
        return text
    for source, target in sorted(EN.items(), key=lambda item: len(item[0]), reverse=True):
        text = text.replace(source, target)
    return text
