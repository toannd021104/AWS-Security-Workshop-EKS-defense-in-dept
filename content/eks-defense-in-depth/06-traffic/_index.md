---
title: "5. Ingress and network policy"
weight: 5
chapter: false
---

## Goal

Allow the intended path from the public ALB to the app and deny unnecessary east-west traffic between pods. Use an AWS Load Balancer Controller for ingress resources; keep the Kubernetes API and worker nodes off the public internet.

**Runnable example:** the [Secure Payments project](https://github.com/toannd021104/AWS-Security-Workshop-EKS-defense-in-dept/tree/main/examples/secure-payments-app) provides the IP-target Ingress, ClusterIP Service, NetworkPolicies, and scripts that verify one allowed and one denied pod path.

## Important prerequisite: network policy enforcement

Kubernetes NetworkPolicy objects have no effect unless the network plugin enforces them. Amazon VPC CNI support depends on its version and network-policy feature configuration. Before applying policies, follow the current AWS VPC CNI documentation for your cluster version, enable the NetworkPolicy feature, and confirm the agent is healthy. A successful `kubectl apply` only proves the API stored the object; it does not prove packets are filtered.

Check the CNI pods and configuration:

```bash
kubectl -n kube-system get daemonset aws-node
kubectl -n kube-system get pods -l k8s-app=aws-node -o wide
```

Expected result: the `aws-node` DaemonSet has a ready pod on each Linux node. Consult the version-matched AWS guide before changing its ConfigMap or environment variables; enabling enforcement can change traffic behavior for every pod on a node.

For a managed add-on, enable it in **EKS → Cluster → Add-ons → Amazon VPC CNI → Edit**. Select a supported current add-on version (at least VPC CNI 1.21 for standard network policies), expand optional configuration, and set:

```json
{"enableNetworkPolicy":"true"}
```

Save the add-on configuration and wait for it to return to `ACTIVE`. The `aws-node` pods should have both the CNI and network-policy agent containers ready (`2/2`). EKS VPC CNI policy enforcement applies to Linux EC2 nodes; review AWS support limitations before mixing Fargate, Windows, alternate CNIs, or multiple pod network interfaces. In standard enforcement mode, newly started pods can briefly have default-allow behavior before their policy is programmed. Strict mode starts pods default-deny, but requires explicit policies for all required endpoints, including CoreDNS; use it only after testing system add-ons.

## Apply default-deny, then explicit allows

Start with a deny policy in the application namespace, then add narrowly scoped DNS and application rules. Test in a lab namespace first. The DNS exception below assumes CoreDNS pods have label `k8s-app=kube-dns` in `kube-system`; inspect your labels and adjust if they differ.

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny
  namespace: payments
spec:
  podSelector: {}
  policyTypes: [Ingress, Egress]
---
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-dns
  namespace: payments
spec:
  podSelector: {}
  policyTypes: [Egress]
  egress:
    - to:
        - namespaceSelector:
            matchLabels:
              kubernetes.io/metadata.name: kube-system
          podSelector:
            matchLabels:
              k8s-app: kube-dns
      ports:
        - protocol: UDP
          port: 53
        - protocol: TCP
          port: 53
```

Once DNS is confirmed, allow only the frontend path to the selected app port. The policy in `payments` selects source pods in a separate `frontend` namespace:

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-frontend-to-web
  namespace: payments
spec:
  podSelector:
    matchLabels:
      app: web
  policyTypes: [Ingress]
  ingress:
    - from:
        - namespaceSelector:
            matchLabels:
              kubernetes.io/metadata.name: frontend
          podSelector:
            matchLabels:
              app: frontend
      ports:
        - protocol: TCP
          port: 8080
```

Create the `frontend` namespace and a small non-root client Deployment so the allow rule has a real source to match:

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: frontend
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: frontend-client
  namespace: frontend
spec:
  replicas: 1
  selector:
    matchLabels:
      app: frontend
  template:
    metadata:
      labels:
        app: frontend
    spec:
      automountServiceAccountToken: false
      securityContext:
        runAsNonRoot: true
        runAsUser: 10001
        runAsGroup: 10001
        seccompProfile:
          type: RuntimeDefault
      containers:
        - name: client
          image: public.ecr.aws/docker/library/busybox:1.36
          command: ["sh", "-c", "sleep 3600"]
          securityContext:
            allowPrivilegeEscalation: false
            readOnlyRootFilesystem: true
            capabilities:
              drop: ["ALL"]
          resources:
            requests:
              cpu: 10m
              memory: 16Mi
            limits:
              cpu: 100m
              memory: 64Mi
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: blocked-client
  namespace: default
spec:
  replicas: 1
  selector:
    matchLabels:
      app: blocked-client
  template:
    metadata:
      labels:
        app: blocked-client
    spec:
      automountServiceAccountToken: false
      securityContext:
        runAsNonRoot: true
        runAsUser: 10001
        runAsGroup: 10001
        seccompProfile:
          type: RuntimeDefault
      containers:
        - name: client
          image: public.ecr.aws/docker/library/busybox:1.36
          command: ["sh", "-c", "sleep 3600"]
          securityContext:
            allowPrivilegeEscalation: false
            readOnlyRootFilesystem: true
            capabilities:
              drop: ["ALL"]
          resources:
            requests:
              cpu: 10m
              memory: 16Mi
            limits:
              cpu: 100m
              memory: 64Mi
```

Save as `frontend-client.yaml`, apply it with the policies, and wait for the client pod to become ready. Verify the allowed path and a denied path:

```bash
kubectl apply -f network-policies.yaml
kubectl apply -f frontend-client.yaml
kubectl rollout status deployment/frontend-client -n frontend
kubectl rollout status deployment/blocked-client -n default
kubectl exec -n frontend deploy/frontend-client -- \
  wget -T 3 -qO- http://web.payments.svc.cluster.local
kubectl exec -n default deploy/blocked-client -- \
  wget -T 3 -qO- http://web.payments.svc.cluster.local
```

The first request should return the NGINX welcome page. The second should time out or fail because `default` is not an allowed source namespace. If both requests work, first confirm `aws-node` has `2/2` containers and a `PolicyEndpoint` exists for the `web` pods before changing policies.

With IP targets, ALB forwards directly to pod IPs. The security group on the pod/node network must accept the application port from the ALB security group. NetworkPolicy also needs to allow the packet as its source is presented to the selected CNI datapath. During the sandbox test, an allow rule for the ALB public subnet CIDRs fixed a `504`; do not assume those CIDRs are always the source identity in every target mode, CNI, or policy enforcement path. Correlate VPC Flow Logs where they expose the relevant ENI traffic with VPC CNI policy-agent behavior and the version-matched AWS documentation; then allow only the required source and port. A healthy target-group check alone does not prove the request reaches the application.

## Create an HTTPS ingress

Prerequisites: AWS Load Balancer Controller installed, its service account has its dedicated IAM role, public subnets are tagged for load balancer discovery, and an ACM certificate exists in the same region as the ALB. See AWS's versioned installation guide for controller IAM policy and Helm values; do not give the controller broad administrator permissions.

### Prepare the controller, certificate, and WAF

The AWS Load Balancer Controller watches Kubernetes Ingress resources and creates AWS load balancers. It is not the same component as the EKS control plane. The following command path pins the controller release (`v2.14.1`) and matching Helm chart (`1.14.1`); check AWS's installation page for newer supported releases when you repeat this workshop. The controller role is scoped to its own Kubernetes service account through this cluster's OIDC provider. Because the controller can create and modify AWS resources, keep its IAM policy release-matched and avoid granting `AdministratorAccess`. Restrict who can create or edit Ingress objects and their security-sensitive annotations.

#### Treat shared Ingress groups as a trust boundary

An explicit `alb.ingress.kubernetes.io/group.name` lets multiple Ingress objects share one ALB. A user who can join that group may be able to add or change listener rules on the shared load balancer. Use an IngressGroup only for namespaces and teams with the same trust level; otherwise keep separate groups/load balancers and enforce ownership through RBAC and admission policy. Do not let an untrusted namespace attach itself to a privileged shared ALB.

1. Confirm the cluster has an IAM OIDC provider. In the console, find the issuer at **EKS → Clusters → select the cluster → Overview → OpenID Connect provider URL**, then create or confirm it in **IAM → Identity providers** with audience `sts.amazonaws.com`. The Terraform foundation in [`infrastructure/terraform`](../../infrastructure/terraform/) creates this provider. Download and review the release-matched controller policy:

   ```bash
   export LBC_VERSION=v2.14.1
   curl -o iam_policy.json \
     "https://raw.githubusercontent.com/kubernetes-sigs/aws-load-balancer-controller/${LBC_VERSION}/docs/install/iam_policy.json"
   cat iam_policy.json
   aws iam create-policy --policy-name AWSLoadBalancerControllerIAMPolicy \
     --policy-document file://iam_policy.json
   ```

   Inspect `iam_policy.json` before creating the policy. If the policy name already exists, retrieve its ARN and review the current default version instead of creating a duplicate. In the console, this is **IAM → Policies → Create policy → JSON**.

2. Create a role whose trust is restricted to the controller service account. In the console, choose **IAM → Roles → Create role → Web identity**, select this cluster's OIDC provider, set audience `sts.amazonaws.com`, and subject `system:serviceaccount:kube-system:aws-load-balancer-controller`; attach only `AWSLoadBalancerControllerIAMPolicy`. The equivalent API steps are:

   ```bash
   ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
   OIDC_ISSUER=$(aws eks describe-cluster --name "$CLUSTER_NAME" --region "$AWS_REGION" \
     --query 'cluster.identity.oidc.issuer' --output text)
   OIDC_HOSTPATH="${OIDC_ISSUER#https://}"
   OIDC_PROVIDER_ARN="arn:aws:iam::${ACCOUNT_ID}:oidc-provider/${OIDC_HOSTPATH}"
   cat > /tmp/lbc-trust.json <<EOF
   {
     "Version": "2012-10-17",
     "Statement": [{
       "Effect": "Allow",
       "Principal": {"Federated": "${OIDC_PROVIDER_ARN}"},
       "Action": "sts:AssumeRoleWithWebIdentity",
       "Condition": {"StringEquals": {
         "${OIDC_HOSTPATH}:aud": "sts.amazonaws.com",
         "${OIDC_HOSTPATH}:sub": "system:serviceaccount:kube-system:aws-load-balancer-controller"
       }}
     }]
   }
   EOF
   aws iam create-role --role-name AWSLoadBalancerControllerRole \
     --assume-role-policy-document file:///tmp/lbc-trust.json
   aws iam attach-role-policy --role-name AWSLoadBalancerControllerRole \
     --policy-arn "arn:aws:iam::${ACCOUNT_ID}:policy/AWSLoadBalancerControllerIAMPolicy"
   LBC_ROLE_ARN=$(aws iam get-role --role-name AWSLoadBalancerControllerRole \
     --query 'Role.Arn' --output text)
   kubectl create serviceaccount aws-load-balancer-controller -n kube-system \
     --dry-run=client -o yaml | kubectl apply -f -
   kubectl annotate serviceaccount aws-load-balancer-controller -n kube-system \
     "eks.amazonaws.com/role-arn=${LBC_ROLE_ARN}" --overwrite
   ```

   If the role or service account already exists, inspect its trust and annotation first instead of overwriting a role used by another cluster. This path does not require `eksctl` or CloudFormation.

3. Install the Gateway API standard CRDs required by the current AWS controller installation guide. This lab uses Ingress resources, not Gateway resources:

   ```bash
   kubectl apply --server-side -f \
     https://github.com/kubernetes-sigs/gateway-api/releases/download/v1.2.0/standard-install.yaml
   ```

4. Install the pinned Helm chart. Because this node group restricts IMDS, pass the region and VPC ID explicitly:

   ```bash
   helm repo add eks https://aws.github.io/eks-charts
   helm repo update eks
   helm install aws-load-balancer-controller eks/aws-load-balancer-controller \
     --namespace kube-system \
     --version 1.14.1 \
     --set clusterName="$CLUSTER_NAME" \
     --set region="$AWS_REGION" \
     --set vpcId="$VPC_ID" \
     --set serviceAccount.create=false \
     --set serviceAccount.name=aws-load-balancer-controller
   ```

5. Verify that the controller is available and its logs show no IAM or subnet-discovery errors:

   ```bash
   kubectl get deployment aws-load-balancer-controller -n kube-system
   kubectl logs -n kube-system deployment/aws-load-balancer-controller --tail=50
   ```

   Expected result: deployment is `2/2` available and logs do not show repeated `AccessDenied` or "unable to resolve at least one subnet" errors. Helm upgrades do not automatically update all CRDs; follow the AWS upgrade procedure when changing controller versions.

For the certificate, open **AWS Certificate Manager → Request certificate**, request a public certificate for a domain you control, choose DNS validation, and create the validation record in the authoritative hosted zone. Wait for status **Issued**. A certificate in another region cannot be attached to a regional ALB.

For WAF, open **AWS WAF & Shield → Web ACLs → Create web ACL**, choose **Regional** scope and the same region as the ALB, add a managed rule group appropriate for the app, and create the ACL. Start in count mode where possible, review false positives, then move to block mode. Record the Web ACL ARN. WAF has separate pricing and may block valid app traffic if rules are enabled without tuning.

Keep the sample Service as `ClusterIP` and configure ALB **IP targets**. The AWS Load Balancer Controller registers the ready pod IPs from EndpointSlices, and the ALB forwards directly to those pods. Confirm that the VPC CNI assigns VPC-routable pod IPs and that security groups permit the application port from the ALB security group:

```bash
kubectl get service web -n payments
kubectl get endpointslice -n payments -l kubernetes.io/service-name=web
```

Expected result: the Service type is `ClusterIP`, and EndpointSlices show ready pod IPs on port `8080`. No NodePort should appear. After ALB reconciliation, the target group should list those pod IPs as healthy; verify that the target security group allows port `8080` only from the ALB security group.

Example Ingress (replace the certificate ARN and host):

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: web
  namespace: payments
  annotations:
    alb.ingress.kubernetes.io/scheme: internet-facing
    alb.ingress.kubernetes.io/target-type: ip
    alb.ingress.kubernetes.io/listen-ports: '[{"HTTPS":443}]'
    alb.ingress.kubernetes.io/certificate-arn: arn:aws:acm:us-east-1:123456789012:certificate/REPLACE_ME
    alb.ingress.kubernetes.io/ssl-redirect: "443"
    alb.ingress.kubernetes.io/wafv2-acl-arn: arn:aws:wafv2:us-east-1:123456789012:regional/webacl/REPLACE_ME
spec:
  ingressClassName: alb
  rules:
    - host: app.example.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: web
                port:
                  number: 80
```

Save the Ingress as `web-ingress.yaml`, then run `kubectl apply -f web-ingress.yaml` and `kubectl get ingress -n payments -w`. The ADDRESS should eventually show an ALB DNS name. Check **EC2 → Load Balancers → Security**: inbound should expose only the intended listener, and target access should be restricted to the ALB security group. Check **WAF & Shield → Web ACLs** to confirm the ACL is associated.

```bash
kubectl get service web -n payments
kubectl describe ingress web -n payments
kubectl get events -n payments --sort-by=.lastTimestamp | tail -20
```

Expected result: the Service has ready endpoints, the Ingress has an ALB address, and its events do not show reconciliation errors. If the Ingress remains pending, check the controller logs, public subnet tags, IAM policy/role association, and security group rules before opening additional ports.

Expected outcome: HTTPS requests to the configured hostname reach the app; HTTP is redirected or unavailable; direct access to node addresses is not part of the design. ALB terminates TLS and sends HTTP directly to pod IPs inside the VPC in this example. If policy requires encryption to the target, configure HTTPS target protocol and certificates on the app as well. A newly created ALB can take several minutes. `ADDRESS` remaining blank usually means controller/IAM/subnet discovery errors; inspect controller logs before changing network rules.

## Console inspection and screenshot


## Trade-offs and common failures

- A public ALB is intentional for a public app; a private ALB is better for internal services. Pick the scheme explicitly.
- WAF protects HTTP(S) requests at the ALB/CloudFront layer; it does not filter pod-to-pod traffic.
- Default-deny egress can break DNS, telemetry, image pulls from in-pod tools, and application dependencies. Add only required destinations and ports, then observe logs and test.
- NetworkPolicy semantics for host-network pods and traffic to node-local services vary. Verify using the chosen CNI and version.
- `target-type: ip` avoids NodePort traffic, but requires correct subnet discovery, security-group behavior, and routable pod IPs.

### Screenshots to capture

Save these as `06-01-https-alb-targets.png` and `06-02-network-policy-tests.png`. If you separately configure WAF, add a distinct screenshot for the Web ACL and its association.

- **06-01 HTTPS ingress:** Place after creating the Ingress. AWS Console → **EC2 → Load Balancers → select the lab ALB → Listeners and rules / Security**. Show the HTTPS listener, ACM certificate, IP target group, and healthy pod targets. The base sandbox has no WAF association; if you enable WAF as an extension, show it separately. Crop out the public DNS name if you do not want it shared.
- **06-02 Network policy proof:** Place after verifying both client paths. Show the applied default-deny and allow policies, then terminal results where the `frontend` test reaches `web` and the unrelated `default` namespace client is denied. Include the namespace and command output, but no account credentials.

### Further reading

- [AWS Load Balancer Controller installation](https://docs.aws.amazon.com/eks/latest/userguide/lbc-helm.html)
- [Route application traffic with an ALB](https://docs.aws.amazon.com/eks/latest/userguide/alb-ingress.html)
- [Enable VPC CNI network policy](https://docs.aws.amazon.com/eks/latest/userguide/cni-network-policy-configure.html)
- [AWS WAF web ACLs](https://docs.aws.amazon.com/waf/latest/developerguide/web-acl.html)
