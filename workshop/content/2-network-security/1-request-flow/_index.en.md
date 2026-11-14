---
title: "Request Flow: Internet → ALB → Pod"
weight: 1
chapter: false
pre: "<b>2.1.</b> "
---

The application has a public domain while its pods run in private subnets. Before adding protection, identify the components a request crosses and the evidence for each hop. Compare ALB configuration, pod IPs, and actual database operations.

## Where does the request go?

![Request path from client to PostgreSQL](/images/en/request-path.svg "ALB forwards to a frontend pod IP; the frontend reaches the API through an internal Service.")

When someone opens `https://notes.<domain>`, the browser first loads the interface, then requests its data:

1. **DNS helps the browser find ALB.** Resolving `notes.<domain>` identifies where to connect. DNS supplies an address; it does not proxy the application request.
2. **ALB accepts HTTPS.** The browser connects on port `443`. ALB terminates TLS, selects a healthy frontend pod, and opens a separate HTTP connection to port `8080`.
3. **The frontend serves the interface and forwards API calls.** Nginx returns HTML and JavaScript. JavaScript then requests `GET /api/notes`. That request also crosses ALB and frontend, but Nginx forwards it to the API instead of returning a static file.
4. **A Kubernetes Service locates an API pod.** Nginx uses `api.notes.svc.cluster.local:8080` in namespace `notes`. It removes the `/api/` prefix: `/api/notes` becomes `/notes`, the API endpoint.
5. **The API reads RDS and returns data.** It connects to PostgreSQL port `5432` using TLS. JSON returns through frontend and ALB; the browser displays the notes.

The read path is **browser → ALB → frontend → API → RDS**. The API queries the database; the frontend forwards API calls.

> **Encryption scope:** Internet-to-ALB uses HTTPS. ALB-to-frontend and frontend-to-API use private HTTP. Security Groups restrict infrastructure connections; chapter 3 adds workload NetworkPolicy. These controls do not encrypt HTTP. The lab keeps this choice to focus on EKS network and workload protection.

This lesson inspects an existing lab. Complete [0.8 — Check the baseline](/preparation/8-baseline/) before running these commands.

## Step 1: compare the path on AWS Console

These are read-only checks. Do not manually register additional targets.

1. **Route 53 → Hosted zones → your lab public zone**: open the `notes` record. Compare its value/alias destination with the DNS name of ALB `eks-did-notes`.
2. **EC2 → Load Balancers → eks-did-notes → Listeners and rules**: HTTP:80 should redirect to HTTPS:443; HTTPS:443 should forward to the frontend target group. Record its name.
3. Open that target group's **Targets** tab. Confirm type **IP**, backend **HTTP:8080**, and **Healthy** targets. The controller registers these IPs automatically.
4. **EKS → cluster → Resources → Workloads → Pods**: filter namespace `notes`, open a frontend pod, and read **Pod IP**. Compare it with a Healthy target. The resource browser requires Kubernetes read permissions; the `kubectl` command below gives the same information.

For example, pod IP `10.20.44.78` registered on port `8080` identifies that frontend backend. Your actual IPs will differ.

![Compare ALB IP targets with frontend pods](/images/console-targets.png "① IP target type. ② HTTP:8080 backend. ③ Two healthy targets. ④ Pod IPs and ports.")

The screenshot was taken during a rollout and includes an old Draining target. Compare current pods with Healthy targets.

## Verify that requests reach the application

### Send requests and interpret the output

Load the lab hostname and kubeconfig:

```bash
source scripts/env.sh
printf 'Hostname: %s\n' "$APP_HOST"
```

`source` normally prints nothing. `printf` must print your prepared hostname. If it is empty, complete [configuration discovery in 0.7](/preparation/7-deploy-application/) first.

Check the frontend:

```bash
curl -sS -o /dev/null -w '%{http_code}\n' "https://$APP_HOST/"
```

Expected output:

```text
200
```

`-o /dev/null` discards HTML; `-w` prints only the HTTP status. A 200 confirms the frontend responds through the HTTPS domain.

Call the API through the frontend:

```bash
curl -fsS "https://$APP_HOST/api/healthz"
printf '\n'
```

Expected response:

```json
{"status": "ok", "workload": "api"}
```

This response comes from the API after traversing ALB and Nginx. Health alone does not prove database access.

Read pod IPs for comparison with the target group:

```bash
kubectl get pods -n notes -l app=frontend -o wide
```

Example output; names and IPs will differ:

```text
NAME                        READY   STATUS    RESTARTS   AGE   IP
frontend-7c8d9f6b5d-abc12    1/1     Running   0          10m   10.20.44.78
frontend-7c8d9f6b5d-def34    1/1     Running   0          10m   10.20.54.165
```

Use the IP column to compare targets. READY 1/1 means the pod's container is ready. Read access logs:

```bash
kubectl logs -n notes -l app=frontend --tail=10 --prefix=true
```

A log line may look like:

```text
[pod/frontend-…/frontend] … "GET /api/healthz HTTP/1.1" 200 …
```

The pod/container prefix identifies the backend receiving the request. ALB health checks also appear; the last ten lines may no longer include your request.

### Test API-to-database operations

```bash
curl -fsS "https://$APP_HOST/api/notes" \
  -H 'Content-Type: application/json' -d '{"body":"Hello from the request path"}'
curl -fsS "https://$APP_HOST/api/notes"
```

POST must return an ID, and GET must include the new note. Use test data only: this application has no user authentication.

### Interpret source addresses correctly

`X-Forwarded-For` carries the client IP in an HTTP header. It is not necessarily the source IP NetworkPolicy sees on the ALB-to-pod connection. Do not use a header to define L3/L4 policy rules. Lessons 2.2–2.6 explain routing and target registration. Configuration is in [render.py](/source/scripts/render.py).

Collect three pieces of evidence: a target IP matching a frontend pod; HTTP 200 from the homepage/API health endpoint; and the posted note appearing in GET. These verify backend registration, the HTTP path, and database operations respectively.
