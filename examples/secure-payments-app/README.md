# Secure Payments Sample for Amazon EKS

A small, deployable application that ties the workshop's security controls together. It is deliberately not a payment processor and contains no customer data, credentials, or payment logic. The app exposes health checks and a diagnostic endpoint that confirms the AWS SDK received short-lived EKS Pod Identity credentials without returning credential values or making an AWS service API call.

## What this project demonstrates

- A real container image built locally and pushed to Amazon ECR.
- An EKS Deployment and ClusterIP Service with non-root execution, a read-only root filesystem, dropped Linux capabilities, resource bounds, and health probes.
- A restricted Pod Security Admission namespace.
- Default-deny network policy with explicit DNS, Pod Identity agent, frontend-to-app, and ALB-subnet-to-app paths.
- An EKS Pod Identity association whose IAM role trust is limited to one account and cluster. The role has no permissions because this sample does not call AWS services.
- An optional HTTPS ALB Ingress using IP targets and an explicit allowed client CIDR. It requires the AWS Load Balancer Controller and an ACM certificate in the cluster's region; WAF is optional.
- Namespace-scoped Kubernetes Roles for deployment operators and read-only observers.
- A repeatable allow/deny connectivity check and a cleanup script that removes only this sample's resources.

The implementation is intentionally small enough to review. The web process does not accept user-supplied URLs, object keys, shell commands, or secrets. `/api/identity` returns the credential provider name and expiration only; it never serializes access keys, session tokens, or the frozen credential object.

## Request and identity paths

```text
Browser --HTTPS--> WAF (optional) --> ALB --> pod IPs --> web Pods
                                      private EKS VPC subnets

Operator --IAM role--> EKS access entry --> Kubernetes RBAC --> private EKS API
web Pod --service account--> EKS Pod Identity agent --> short-lived role credentials
```

The ALB uses **IP** targets and sends requests directly to pod IPs; the Service stays `ClusterIP`, so no NodePort is allocated. The VPC CNI must assign routable VPC IPs to pods, and the security group attached to pod ENIs/nodes must accept the app port from the ALB security group. The `allow-alb-subnets-to-web` NetworkPolicy permits only the ALB public subnet CIDRs to reach the app port; replace the example CIDRs if your VPC differs. Security groups and NetworkPolicy are separate boundaries, and both must allow the path. Verify target health and an HTTPS request end to end; target health alone does not prove app traffic is permitted.

## Requirements

- An existing EKS cluster in a non-production AWS account, with `kubectl` access from an approved network.
- AWS CLI v2, Docker, `kubectl`, and `sed` on the build/deploy machine.
- Private worker nodes with a node role that can pull images from ECR.
- Amazon VPC CNI NetworkPolicy enforcement enabled and healthy. Creating a NetworkPolicy object alone does not filter packets.
- EKS Pod Identity Agent add-on support in the cluster's region and Kubernetes version.
- For the optional public Ingress: AWS Load Balancer Controller installed with its own least-privilege IAM role, public subnet tags, and an ACM certificate in the same region as the ALB.

This code deploys application resources only. Create the VPC, EKS cluster, node group, endpoint settings, load balancer controller, GuardDuty configuration, and logging settings through the workshop modules. Those controls are account-specific and are not created by these scripts.

## 1. Set the target cluster and region

Use the same non-production account and region as the EKS cluster. Verify the active identity before creating ECR or IAM resources:

```bash
export AWS_REGION=us-east-1
export CLUSTER_NAME=eks-depth-lab
aws sts get-caller-identity
aws eks describe-cluster --name "$CLUSTER_NAME" --region "$AWS_REGION" \
  --query 'cluster.{Status:status,Version:version,Endpoint:endpoint}' --output table
```

Do not continue if this is the wrong account, role, or cluster.

## 2. Build and push the application image

The script creates an immutable, scan-on-push ECR repository if needed. The default image tag is the current Git commit. A node role needs ECR pull permissions; the application role does not.

```bash
./scripts/build-push.sh

export IMAGE_TAG="$(git rev-parse --short=12 HEAD)"
export ACCOUNT_ID="$(aws sts get-caller-identity --query Account --output text)"
export IMAGE_URI="${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/secure-payments-workshop:${IMAGE_TAG}"
```

Expected result: Docker pushes the image and ECR image scanning starts. Review scan results before using the image beyond this lab. For production, pin the base image and dependencies to approved digests/lock files, sign the image, and promote an immutable digest through your release process.

In the sandbox verification on 2026-11-06, ECR reported **9 HIGH, 10 MEDIUM, and 3 LOW** findings for image tag `8484070e093b`. The findings included OS-library CVEs in SQLite, util-linux, glibc, zlib, and libtirpc. Treat this image as a lab artifact; check the current scan for your own build, refresh the base image, and do not promote an image with unresolved findings without an explicit risk review. Scanner results change over time, so these counts are evidence from that run, not a lasting assessment.

## 3. Create and associate the workload identity

Create a trust-only role. The script reads the actual account and cluster ARN, fills the trust-policy template, and does not attach any permissions policy:

```bash
export ROLE_NAME=EKSDepthSampleWebIdentity
./scripts/create-identity-role.sh
export ROLE_ARN="$(aws iam get-role --role-name "$ROLE_NAME" \
  --query 'Role.Arn' --output text)"
```

Create or update the EKS Pod Identity association and install the managed agent add-on if it is absent:

```bash
./scripts/associate-pod-identity.sh
aws eks describe-addon --cluster-name "$CLUSTER_NAME" \
  --addon-name eks-pod-identity-agent --region "$AWS_REGION" \
  --query 'addon.status' --output text
```

Wait until the add-on is `ACTIVE`. The namespace and service account can be created in the next step; the EKS association is keyed by their names.

## 4. Deploy the app and network boundaries

The script applies the `payments` namespace, service account, policies, service, application Deployment, and two disposable test clients. It waits for all three Deployments to become ready.

```bash
./scripts/deploy.sh
kubectl rollout restart deployment/web -n payments
kubectl rollout status deployment/web -n payments --timeout=5m
```

The restart ensures newly created pods receive the Pod Identity association. The script does not create a public endpoint unless `ACM_CERTIFICATE_ARN` is set.

### Optional HTTPS ALB

Set a regional ACM certificate ARN and run the deploy script again. To attach WAF, also set a regional Web ACL ARN:

```bash
export ACM_CERTIFICATE_ARN=arn:aws:acm:us-east-1:123456789012:certificate/REPLACE_ME
export ALB_ALLOWED_CIDR=203.0.113.10/32
export WAF_ACL_ARN=arn:aws:wafv2:us-east-1:123456789012:regional/webacl/REPLACE_ME
./scripts/deploy.sh
kubectl get ingress web -n payments --watch
```

Set `ALB_ALLOWED_CIDR` to a trusted client network, preferably a single `/32`; the script refuses to create an internet-facing ALB without this value. Omit `WAF_ACL_ARN` to create an HTTPS ALB without WAF. Do not copy the example ARNs; replace them with resources from your own account. Verify the ALB's HTTPS listener, certificate, WAF association (if configured), target health, and security-group source rules in the console.

## 5. Verify expected allow and deny results

Run the verification script:

```bash
./scripts/verify.sh
```

Expected observations:

- The `frontend` test client reaches `web.payments.svc.cluster.local` and receives HTTP 200.
- `/api/identity` returns a provider of `container-role`, a credential expiration, and `credential_values_returned: false`.
- The unrelated client in the `default` namespace times out or is denied when it tries to reach the `payments` pods.
- The app pods show `Running`, `READY 1/1`, and use the `web-reader` service account.
- If the optional ALB is configured, an HTTPS request to `/healthz` returns HTTP 200. A healthy ALB target alone does not prove NetworkPolicy permits forwarded application traffic.

Example identity response:

```json
{
  "status": "available",
  "provider": "container-role",
  "expected_provider": "container-role",
  "expires_at": "2026-11-06T12:00:00+00:00",
  "credential_values_returned": false
}
```

The timestamp is illustrative. A `503` from `/api/identity` means the SDK did not obtain Pod Identity credentials or received credentials from an unexpected source. Check the association, agent status, service account name, node compatibility, and the `169.254.170.23:80` egress rule. Do not solve this by adding permissions to the node role.

## 6. Optional observer RBAC

Map a named IAM role to the `payments-observers` Kubernetes group, then apply the namespace Role and RoleBinding:

```bash
export OBSERVER_ROLE_ARN=arn:aws:iam::123456789012:role/EKSDepthReadOnly
aws eks create-access-entry --cluster-name "$CLUSTER_NAME" \
  --principal-arn "$OBSERVER_ROLE_ARN" --type STANDARD \
  --kubernetes-groups payments-observers --region "$AWS_REGION"
kubectl apply -f k8s/60-observer-rbac.yaml
```

Use the real role ARN from your account. Test the role with `kubectl auth can-i`: it should read pods and logs in `payments`, but not create Deployments or read Secrets.

## 7. Namespace-scoped DevOps RBAC

For a daily DevOps role, prefer a custom Kubernetes group and Role over `AmazonEKSEditPolicy`. The managed edit policy is convenient, but the sandbox check confirmed that it can read namespace Secrets. The sample Role can deploy and roll back Deployments, inspect pods and logs, and read Services/events; it cannot read Secrets, change RBAC, or access other namespaces.

Create an IAM role with only `eks:DescribeCluster` for this cluster, then map it to the Kubernetes group and bind the namespace Role:

```bash
export DEVOPS_ROLE_ARN=arn:aws:iam::123456789012:role/EKSDepthDevOps
aws eks create-access-entry --cluster-name "$CLUSTER_NAME" \
  --principal-arn "$DEVOPS_ROLE_ARN" --type STANDARD \
  --kubernetes-groups payments-deployers --region "$AWS_REGION"
kubectl apply -f k8s/61-devops-rbac.yaml
```

If the access entry already exists, update it to the group instead of creating a second entry for the same principal. Do not also associate `AmazonEKSEditPolicy`, because EKS access-policy grants combine with Kubernetes RBAC and would restore the broader permissions.

Check with the DevOps IAM role:

```bash
kubectl auth can-i create deployments -n payments  # yes
kubectl auth can-i get pods/log -n payments         # yes
kubectl auth can-i get secrets -n payments          # no
kubectl auth can-i create deployments -n default    # no
kubectl auth can-i get nodes                        # no
```

## Cleanup

Remove the Ingress and only the sample's named workloads and policies, then remove the exact Pod Identity association:

```bash
export CLUSTER_NAME=eks-depth-lab
export AWS_REGION=us-east-1
./scripts/cleanup.sh
```

The script leaves the `payments` and `frontend` namespaces in place so it cannot delete unrelated resources in a reused namespace. It also leaves the ECR repository and IAM role for review. Delete those separately only after confirming their names, image contents, role trust, and that nothing else uses them. It does not delete the cluster, VPC, NAT Gateways, ACM certificate, WAF ACL, or shared security services.

## File map

```text
app/       HTTP service, dependency, and container build
iam/       Pod Identity trust template and explanation
k8s/       namespace, service account, workload, service, policies, Ingress, RBAC, test clients
scripts/   build/push, IAM role, Pod Identity association, deploy, verify, cleanup
```

## Security review notes

- No AWS keys, kubeconfig, credentials, or production data are stored in this directory.
- The application runs non-root, has a read-only filesystem, drops all Linux capabilities, and has CPU/memory requests and limits.
- Pod Identity is scoped to the cluster and account; this example role intentionally has no AWS permissions.
- Egress is restricted to DNS and the local Pod Identity agent. Add narrowly scoped destination controls before adding application calls to AWS services.
- The optional ALB is the only public app entry point. The Kubernetes API and nodes stay private.
- NetworkPolicy must be enforced by the selected CNI. Validate it with the allow/deny tests rather than relying only on successful YAML application.
- This sample is a teaching baseline, not a production payment application or a substitute for application security review.
