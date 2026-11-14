---
title: "Worker Node Security and IMDSv2"
weight: 6
chapter: false
pre: "<b>3.6.</b> "
---

Worker nodes have IAM roles for EKS operation. If application pods obtain node credentials through IMDS, they may gain permissions beyond their assigned role. Configure metadata options and test an ordinary pod.

## Why restrict IMDS?

EC2 Instance Metadata Service exposes instance information and temporary instance-role credentials at `169.254.169.254`. IMDSv2 requires a session token; the response hop limit constrains the token response's network hops.

The node role needs EKS and image-pull permissions. Application SQS/RDS permissions should not be attached to it. Access to node credentials can undermine separate workload identities.

## Step 1: launch-template metadata options

1. **EC2 → Launch templates → lab node template → Advanced details → Metadata options**.
2. Enable metadata, require **IMDSv2**, and set response hop limit **1**.
3. Do not expose SSH to the Internet; encrypt EBS. Give `aws-node` a dedicated CNI role rather than depending on metadata with hop limit 1.
4. Confirm the node group uses that template version. Editing a template does not update existing nodes; perform a controlled node-group rollout.

## Verify instance settings and pod access

### Read running-instance configuration

```bash
aws ec2 describe-instances \
  --filters Name=tag:eks:cluster-name,Values=eks-did Name=instance-state-name,Values=running \
  --query 'Reservations[].Instances[].{id:InstanceId,publicIP:PublicIpAddress,metadata:MetadataOptions,profile:IamInstanceProfile.Arn}'
```

Expect no public node IPs, `HttpTokens=required`, and `HttpPutResponseHopLimit=1`. Terraform uses `aws_launch_template.nodes`.

### Try IMDS from an application pod

```bash
kubectl exec -n notes deployment/api -- python -c '
import urllib.request
r=urllib.request.Request("http://169.254.169.254/latest/api/token",method="PUT",headers={"X-aws-ec2-metadata-token-ttl-seconds":"60"})
try:
    urllib.request.urlopen(r,timeout=3)
    raise SystemExit("UNEXPECTED: pod reached IMDS; investigate")
except (TimeoutError, OSError):
    print("Expected: ordinary application pod cannot obtain IMDS token")'
```

After default deny, NetworkPolicy can also block this path. Inspect instance metadata settings and run the probe **before policy** if attributing the effect specifically to hop limit. Do not attribute every post-hardening timeout solely to IMDSv2.

IMDSv2 alone does not stop a pod requesting a token; hop limits and network restrictions add protection. `hostNetwork` behaves differently and is excluded from this application baseline. Chapter 4 shows how Pod Identity still supplies the correct temporary workload credentials.
