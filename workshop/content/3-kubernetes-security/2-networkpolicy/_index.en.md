---
title: "Network Segmentation with Kubernetes NetworkPolicy"
weight: 2
chapter: false
pre: "<b>3.2.</b> "
---

The frontend needs API access; an unrelated pod does not. Without NetworkPolicy, both may connect. Record the baseline, restrict access, and keep note storage and report processing working.

## Which connections are allowed?

NetworkPolicy selects pods by label and defines allowed ingress/egress. Once a pod is isolated in a direction, traffic in that direction must match an allow rule. Policies are additive: an overly broad allow can undo the intended restriction. The agent was enabled during [EKS preparation](/preparation/3-eks/). For an existing cluster, check [3.3](/3-kubernetes-security/3-vpc-cni/) before applying policy.

![Allowed and denied workload connections](/images/en/network-policy.svg "Start with default deny, then allow application dependencies.")

| Source | Destination | Port | Decision |
|---|---|---|---|
| ALB subnets | Frontend | TCP 8080 | Allow, together with SG controls |
| Frontend | API in the same namespace | TCP 8080 | Allow |
| API/worker | Database subnets | TCP 5432 | Allow; SG/IAM DB/SQL grants still apply |
| Workloads | CoreDNS | TCP/UDP 53 | Allow |
| API/worker/db-init | Pod Identity Agent | TCP 80 | Allow 169.254.170.23/32 |
| API/worker/db-init | Public AWS endpoints | TCP 443 | Allow outbound; IAM limits API/resource access |
| Frontend | Database/Internet | — | Deny |
| Unrelated pod | API | — | Deny |

## Step 1: record connectivity before isolation

Inspect frontend/API labels in EKS Resources. Confirm the application works and no policies remain from a previous run:

```bash
source scripts/env.sh
kubectl get networkpolicy -n notes
python3 scripts/network-proof.py --stage before
```

The script creates two Restricted-compliant Deployments with one probe pod each, using the deployed image with different labels. Controller ownership supports reliable VPC CNI enforcement. Probes lack `workshop-serving=true`, so Service/ALB never select them as serving backends even when `app=frontend` tests frontend policy. Before policy, both frontend and `untrusted` probes reach API. The script also saves a note, generates a report, and deletes its Deployments/pods. Reports are saved as `evidence/network-proof-before.json` or `network-proof-after.json`.

If policy already exists, the before test stops rather than recording a false baseline. On a hardened lab, use the after test; do not remove active protection merely to repeat it.

## Step 2: apply NetworkPolicy

After the baseline works and the agent is enabled:

```bash
kubectl get networkpolicy -n notes
kubectl apply -f k8s/network-policies.yaml
kubectl describe networkpolicy frontend -n notes
kubectl describe networkpolicy api -n notes
```

Default deny isolates ingress and egress for all selected pods. Allow policies **add together**; default deny does not override another broad allow. API ingress uses a frontend `podSelector`. If workloads span namespaces, combine `namespaceSelector` and `podSelector` within the same peer for AND semantics.

```yaml
from:
  - podSelector:
      matchLabels:
        app: frontend
ports:
  - protocol: TCP
    port: 8080
```

This is a rule excerpt, not a complete manifest. [render.py](/source/scripts/render.py) generates policy from actual subnet CIDRs instead of pinning an RDS IP that could change during failover.

## Compare before and after

### Repeat the connectivity tests

```bash
python3 scripts/network-proof.py --stage after
```

Negative tests use the Service IP to distinguish DNS failure from blocked connectivity. Frontend-to-API must succeed; untrusted-to-API and frontend-to-RDS must time out. The positive API-to-RDS transaction must still succeed, proving the database is available.

### Egress limitations

Public HTTPS egress allows more than SQS. Standard NetworkPolicy has no native FQDN/HTTP authorization. IAM limits access to the queue; use suitable endpoint policies or egress controls if service-specific network restrictions are needed. These rules do not constrain every possible data-exfiltration path.

| Test | Before policy | After policy |
|---|---|---|
| Frontend → API | Connects | Connects |
| Unrelated pod → API | Connects | Blocked |
| Frontend → RDS | No pod-specific restriction | Blocked |
| Save notes and generate reports | Works | Works |

The [AWS after-policy report](/evidence/network-proof-after.json) records five observed tests.

`--stage before` tests both API connections and the business transactions. `--stage after` additionally tests frontend-to-RDS denial. A timeout is meaningful only when valid positive connections and application transactions succeed too.
