---
title: "SBOM, Image Signing & Admission Policies"
weight: 2
chapter: false
pre: "<b>5.2.</b> "
---

## Ba bằng chứng khác nhau

![Chuỗi source, build, ký và admission](/images/supply-chain.svg)

SBOM liệt kê thành phần. Signature chứng minh artifact digest đã được signer tin cậy ký. Admission policy quyết định workload có được tạo. Signature không bảo đảm image không có lỗ hổng; SBOM không thay vulnerability scan.

### Console trước

ECR → repository → Images: ghi lại image digest thay vì chỉ tag. IAM/ECR permissions xác định ai có quyền push. Cấu hình signature verification là Kubernetes admission, nên phần tiếp theo cần CLI.

### CLI: sinh SBOM, ký và xác minh

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

### Enforce bằng Kyverno

```bash
bash scripts/admission.sh
bash scripts/prepare-unsigned.sh
kubectl get clusterpolicy verify-notes-image
```

Policy giới hạn namespace `notes` và repository app lab, yêu cầu signature từ public key của workshop. Kyverno fetch manifest/signature từ private ECR bằng registry secret; secret được tạo qua stdin, không đưa vào Hugo hoặc command arguments. ECR token hết hạn sau khoảng 12 giờ: refresh bằng script trước lượt thử tiếp theo. Production nên dùng credential provider/identity được quản lý phù hợp.

**Positive test:** server-side dry-run pod Restricted dùng digest đã ký phải được chấp nhận. **Negative test:** cùng repo nhưng digest mới chưa ký phải bị webhook từ chối. `verify.py --supply-chain` thực hiện hai test sau bước `prepare-unsigned.sh`. Script build cùng source với một image label khác để có digest mới, push nhưng không ký hoặc deploy nó.

### Phạm vi và tradeoff

Ở chart 3.9.2 đã kiểm chứng, `ClusterPolicy` là API legacy vẫn được hỗ trợ; đánh giá migration sang `ImageValidatingPolicy` khi nâng cấp. Policy này kiểm tra image API/worker của lab, chưa bao phủ mọi repository hoặc image Nginx upstream. Không khẳng định toàn cluster chỉ chạy signed images. Webhook fail-closed tăng bảo vệ nhưng phụ thuộc availability của verifier/registry; một replica Kyverno chỉ phù hợp sandbox. Native CEL admission có thể kiểm tra digest/registry pattern, nhưng không tự xác minh Cosign signature, nên lab dùng verifier thực.
