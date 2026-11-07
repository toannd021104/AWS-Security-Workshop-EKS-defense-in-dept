---
title: "SBOM, Image Signing & Admission Policies"
weight: 2
chapter: false
pre: "<b>5.2.</b> "
---

Tag và tên repository chưa chứng minh image được tạo bởi nguồn đã tin cậy. Bài này tạo SBOM, ký image theo digest và áp dụng admission policy để kiểm tra chữ ký trước khi workload được tạo.

## Scan, SBOM và chữ ký giải quyết việc gì?

Ba thành phần phục vụ ba mục đích: SBOM liệt kê dependency; chữ ký gắn digest với public key tin cậy; admission policy kiểm tra image trước khi Kubernetes tạo workload. Image có chữ ký vẫn phải được quét lỗ hổng theo bài 5.1.

![Chuỗi source, build, ký và admission](/images/supply-chain.svg)

SBOM giúp đối chiếu các thành phần của image với kết quả scanning. Chữ ký xác minh nguồn ký và tính toàn vẹn của digest, không bảo đảm các dependency đã hết lỗ hổng.

## Bước 1: quan sát cấu hình hiện tại

ECR → repository → Images: ghi lại image digest thay vì chỉ tag. IAM/ECR permissions xác định ai có quyền push. Cấu hình signature verification là Kubernetes admission, nên phần tiếp theo cần CLI.

## Bước 2: tạo SBOM và ký image

```bash
source scripts/env.sh
bash scripts/supply-chain.sh
```

Script dùng image digest trong `.local/image.txt`, sinh `.local/sbom.cdx.json` bằng Trivy và ký bằng Cosign. Public key được lưu `k8s/cosign.pub`; private key chỉ ở `.local/` bị gitignore. Lab dùng key tạm với password rỗng để demo; production dùng signer được bảo vệ và policy quản lý key/rotation riêng.

Lab không upload signature vào public transparency log; `--tlog-upload=false` khi ký và `--insecure-ignore-tlog` khi xác minh chỉ bỏ yêu cầu transparency log, **không bỏ kiểm tra signature bằng public key**.

```bash
IMAGE=$(cat .local/image.txt)
cosign verify --insecure-ignore-tlog --key k8s/cosign.pub "$IMAGE"
```

## Bước 3: áp dụng admission policy

```bash
bash scripts/admission.sh
bash scripts/prepare-unsigned.sh
kubectl get clusterpolicy verify-notes-image
```

Policy giới hạn namespace `notes` và repository app lab, yêu cầu signature từ public key của workshop. Kyverno fetch manifest/signature từ private ECR bằng registry secret; secret được tạo qua stdin, không đưa vào Hugo hoặc command arguments. ECR token hết hạn sau khoảng 12 giờ: refresh bằng script trước lượt thử tiếp theo. Production nên dùng credential provider/identity được quản lý phù hợp.

**Positive test:** server-side dry-run pod Restricted dùng digest đã ký phải được chấp nhận. **Negative test:** cùng repo nhưng digest mới chưa ký phải bị webhook từ chối. `verify.py --supply-chain` thực hiện hai test sau bước `prepare-unsigned.sh`. Script build cùng source với một image label khác để có digest mới, push nhưng không ký hoặc deploy nó.

## Thử image có chữ ký và image chưa ký

### Kiểm tra phạm vi và kết quả admission

Ở chart 3.9.2 đã kiểm chứng, `ClusterPolicy` là API legacy vẫn được hỗ trợ; đánh giá migration sang `ImageValidatingPolicy` khi nâng cấp. Policy này kiểm tra image API/worker của lab, chưa bao phủ mọi repository hoặc image Nginx upstream. Không khẳng định toàn cluster chỉ chạy signed images. Webhook fail-closed tăng bảo vệ nhưng phụ thuộc availability của verifier/registry; một replica Kyverno chỉ phù hợp môi trường thực hành. Native CEL admission có thể kiểm tra digest/registry pattern, nhưng không tự xác minh Cosign signature, nên lab dùng verifier thực.

Chạy bộ kiểm tra sau khi đã hoàn thành các lớp bảo vệ của workshop:

```bash
python3 scripts/verify.py --supply-chain
```

Hai phép thử admission phải cho kết quả khác nhau: digest đã ký được chấp nhận; digest chưa ký bị từ chối với thông báo liên quan đến signature verification. Các phép thử dùng server-side dry-run nên không triển khai image chưa ký vào ứng dụng.
