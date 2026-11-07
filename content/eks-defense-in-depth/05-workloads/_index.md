---
title: "4. Workload, pod, and image security"
weight: 4
chapter: false
---

## Goal

Reduce what a compromised container can do to the node and cluster. A container is not a virtual machine: it shares the host kernel. Restrict privileges, use supported node images, and enforce a namespace-level baseline so a bad manifest is rejected before it runs.

**Runnable example:** the [Secure Payments project](https://github.com/toannd021104/AWS-Security-Workshop-EKS-defense-in-dept/tree/main/examples/secure-payments-app) includes the image build, hardened Deployment, Service, probes, resource limits, and namespace labels used in this module.

## Harden the managed node group

In **EKS → Cluster → Compute → Node groups**, confirm the group uses private subnets and has no SSH remote access configured. Prefer EKS-optimized Amazon Linux images and managed node group updates. Schedule updates: a managed node group does not remove the need to patch Kubernetes components and host packages.

For workloads that need AWS APIs, do not let pods inherit the node instance role. In **EC2 → Instances → select a node → Security**, confirm the attached instance profile is the dedicated node role. Review its permissions and remove application-specific policies from it. Workload permissions are handled in Module 7.

EKS-managed node groups use an instance profile and EC2 metadata service. Use the supported EKS/AMI configuration for IMDSv2 and prevent ordinary pods from reaching instance metadata. The launch-template step in Module 3 requires IMDSv2 and sets the response hop limit to `1`, which commonly prevents a packet traversing a pod network namespace from reaching IMDS. Verify this against your CNI and host-network workloads before enforcing it; a host-network pod can have different reachability. Do not apply an untested launch-template change to every node at once.

## Enforce the Pod Security Standards baseline

Kubernetes Pod Security Admission is built in. Label an application namespace to enforce the **restricted** standard, while using `warn` and `audit` first to discover incompatible workloads. Do this in a test namespace before production:

```bash
kubectl create namespace payments
kubectl label namespace payments \
  pod-security.kubernetes.io/audit=restricted \
  pod-security.kubernetes.io/warn=restricted \
  pod-security.kubernetes.io/enforce=restricted \
  pod-security.kubernetes.io/enforce-version=latest --overwrite
```

`latest` follows the cluster's current policy version; pin a Kubernetes minor version in a production change process when predictable policy behavior matters. Enforcement can reject old charts, sidecars, and debugging pods. Review warnings and audit events before enabling `enforce` on an existing namespace.

## Deploy a restricted sample pod

Create namespace `payments` as above. Apply this Deployment:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web
  namespace: payments
spec:
  replicas: 2
  selector:
    matchLabels:
      app: web
  template:
    metadata:
      labels:
        app: web
    spec:
      automountServiceAccountToken: false
      securityContext:
        runAsNonRoot: true
        seccompProfile:
          type: RuntimeDefault
      containers:
        - name: web
          image: nginxinc/nginx-unprivileged:stable-alpine
          ports:
            - name: http
              containerPort: 8080
          securityContext:
            allowPrivilegeEscalation: false
            readOnlyRootFilesystem: true
            capabilities:
              drop: ["ALL"]
          resources:
            requests:
              cpu: 50m
              memory: 64Mi
            limits:
              cpu: 250m
              memory: 128Mi
          volumeMounts:
            - name: tmp
              mountPath: /tmp
      volumes:
        - name: tmp
          emptyDir: {}
```

Save it as `web-deployment.yaml`, then:

```bash
kubectl apply -f web-deployment.yaml
kubectl rollout status deployment/web -n payments
kubectl get pods -n payments
```

Expected result: two pods reach `Running` and `READY 1/1`. The unprivileged NGINX image listens on port 8080 and supplies its own non-root UID, so the pod can drop all Linux capabilities without trying to bind privileged port 80. The tag is mutable; for a reproducible deployment, resolve and pin an approved digest, and scan it before promotion.

## Check the image supply chain

An image can run with a strong `securityContext` and still contain a vulnerable operating-system package or dependency. Treat image review as a release step: build from a trusted base, scan the exact image digest, keep an inventory of its components, and promote only the reviewed artifact.

The sample ECR repository enables scan-on-push. Wait for the scan to finish, then inspect findings for the immutable tag you built:

```bash
: "${IMAGE_URI:?Build and push the sample image first}"
IMAGE_TAG="${IMAGE_TAG:-${IMAGE_URI##*:}}"
aws ecr describe-images \
  --repository-name "${ECR_REPOSITORY:-secure-payments-workshop}" \
  --image-ids "imageTag=${IMAGE_TAG}" \
  --query 'imageDetails[0].imageScanStatus.status' --output text
aws ecr describe-image-scan-findings \
  --repository-name "${ECR_REPOSITORY:-secure-payments-workshop}" \
  --image-id "imageTag=${IMAGE_TAG}" \
  --query 'imageScanFindings.{Counts:findingSeverityCounts,Findings:findings[*].{Severity:severity,CVE:name,Description:description}}' \
  --output json
```

Expected result: scan status is `COMPLETE`; review each HIGH/CRITICAL finding, its package, fixed version, and whether the affected code path is used. If status is `IN_PROGRESS`, wait and retry; if no scan is available, confirm repository scan-on-push settings and that the image finished pushing. A scan reports risk; it does not block a deployment. Add a CI/CD gate or admission policy if unsigned or over-threshold images must be rejected. Enhanced scanning through Amazon Inspector is a separate repository/account configuration and can add cost.

Generate a Software Bill of Materials (SBOM) for the same image with a tool such as Syft:

```bash
syft "${IMAGE_URI}" -o spdx-json=sbom.spdx.json
```

The SBOM lists operating-system packages and application dependencies. Store it with the image digest and build record; it helps identify affected releases when a new CVE is published. Do not commit private application source or credentials into the SBOM artifact.

Image signing can establish which trusted build produced an image. With Cosign, generate a key pair once, keep the private key in an approved secret store, and sign/verify the immutable image reference:

```bash
cosign generate-key-pair
: "${IMAGE_URI:?Build and push the sample image first}"
IMAGE_TAG="${IMAGE_TAG:-${IMAGE_URI##*:}}"
IMAGE_DIGEST="$(aws ecr describe-images \
  --repository-name "${ECR_REPOSITORY:-secure-payments-workshop}" \
  --image-ids "imageTag=${IMAGE_TAG}" \
  --query 'imageDetails[0].imageDigest' --output text)"
IMAGE_DIGEST_URI="${IMAGE_URI%:*}@${IMAGE_DIGEST}"
cosign sign --key cosign.key "${IMAGE_DIGEST_URI}"
cosign verify --key cosign.pub "${IMAGE_DIGEST_URI}"
```

Never commit `cosign.key` or print its contents in CI logs. Verification is evidence, not enforcement: EKS still admits an unsigned image unless an admission policy such as Kyverno or an equivalent verifier is installed and configured. Signature enforcement is an advanced extension and is not enabled in this sandbox.

Expose the app only inside the cluster first. Add this Service to `web-deployment.yaml` (or save it as `web-service.yaml`):

```yaml
apiVersion: v1
kind: Service
metadata:
  name: web
  namespace: payments
spec:
  type: ClusterIP
  selector:
    app: web
  ports:
    - name: http
      port: 80
      targetPort: 8080
```

Apply it and verify the selector finds both pods:

```bash
kubectl apply -f web-service.yaml
kubectl get service,endpointslice -n payments
```

Expected result: the Service has a ClusterIP and EndpointSlices list the ready pod IPs. `ClusterIP` keeps the service internal; Module 5 will add the controlled ALB entry point.

## Prove the admission control rejects an unsafe pod

Try a deliberately noncompliant pod in the test namespace:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: must-be-rejected
  namespace: payments
spec:
  containers:
    - name: shell
      image: public.ecr.aws/docker/library/busybox:1.36
      command: ["sh", "-c", "sleep 3600"]
      securityContext:
        privileged: true
```

Apply the file with `kubectl apply -f unsafe-pod.yaml`. Expected result: the API rejects it with a Pod Security violation (privileged container is not allowed by `restricted`). Delete the local sample file if you do not need it. This is a safe policy test; it does not exploit a running workload.

## Namespace boundaries are not complete isolation

Namespaces scope names and some RBAC policies. They do not isolate the kernel, node, or network by themselves. Combine them with NetworkPolicy, workload identity, admission controls, and separate node groups or clusters when a workload's risk or compliance boundary requires stronger isolation. Avoid giving application service accounts permission to create Pods, RoleBindings, or privileged workloads; those permissions can become an indirect privilege escalation path.

### Screenshots to capture

Save these as `05-01-pod-security-namespace.png`, `05-02-hardened-pods.png`, and optionally `05-03-ecr-image-scan.png`.

- **05-01 Namespace security policy:** Place after applying the namespace Pod Security Admission labels. AWS Console is not needed here. In the terminal, show `kubectl get namespace payments --show-labels` with the `pod-security.kubernetes.io/enforce=restricted` label visible. This proves the admission baseline is enabled.
- **05-02 Hardened workload:** Place after deploying the sample pods. Show `kubectl get pods -n payments -o wide` with the sample pods `Running` and `READY`, plus the relevant sanitized pod YAML showing non-root, `RuntimeDefault` seccomp, dropped capabilities, read-only root filesystem, and resource limits. Do not include Secret data or environment values.
- **05-03 ECR image scan:** Place after reviewing the image digest. Show the ECR scan status and severity counts, with account, repository identifiers, and private image names redacted if needed. State clearly that scan findings do not block deployment unless a CI/CD/admission gate is configured.

### Further reading

- [Pod Security Standards](https://kubernetes.io/docs/concepts/security/pod-security-standards/)
- [EKS security best practices for Pods](https://docs.aws.amazon.com/eks/latest/best-practices/pod-security.html)
- [EKS identity and access management best practices](https://docs.aws.amazon.com/eks/latest/best-practices/identity-and-access-management.html)
- [Amazon ECR image scanning](https://docs.aws.amazon.com/AmazonECR/latest/userguide/image-scanning.html)
- [Syft SBOM generator](https://github.com/anchore/syft)
- [Cosign image signing](https://docs.sigstore.dev/cosign/signing/signing_with_containers/)
