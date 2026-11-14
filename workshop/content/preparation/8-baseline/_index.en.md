---
title: "Verify the application baseline"
weight: 80
chapter: false
pre: "<b>0.8.</b> "
---

## Verification goal

Before NetworkPolicy or advanced authorization tests, establish a working application path. Baseline results distinguish intentional denials from incomplete deployment.

Outputs below are examples; pod names, IPs, IDs, and times vary.

## Load configuration and check frontend

```bash
source scripts/env.sh
printf 'Hostname: %s\n' "$APP_HOST"
curl -sS -o /dev/null -w '%{http_code}\n' "https://$APP_HOST/"
```

Example:

```text
Hostname: notes.example.com
200
```

`source` loads `.local/lab.env` and normally prints nothing. Curl discards HTML and prints status 200, verifying HTTPS domain-to-frontend access through ALB.

## Check frontend-to-API

```bash
curl -fsS "https://$APP_HOST/api/healthz"
printf '\n'
```

Expected:

```json
{"status": "ok", "workload": "api"}
```

The request reached API through Nginx. Health alone does not test the database.

## Save and retrieve a note

```bash
curl -fsS "https://$APP_HOST/api/notes" \
  -H 'Content-Type: application/json' -d '{"body":"baseline-note"}'
printf '\n'
curl -fsS "https://$APP_HOST/api/notes"
printf '\n'
```

POST returns `id` and `body`; GET includes the same note:

```json
{"id": 1, "body": "baseline-note"}
```

```json
[{"id": 1, "body": "baseline-note"}]
```

Your ID may exceed 1 and the list may contain previous test data. Reading back the note verifies API-to-RDS operations and required SQL privileges.

If `/healthz` returns 200 but a note operation returns 503, the baseline has not passed: this health check tests the HTTP handler, not RDS. Inspect `kubectl logs -n notes -l app=api --tail=50 --prefix=true` and the `db-init` log; check Job completion, SGs, and database IAM permissions. For a transient `ConnectionTimeout`, retry a read-only GET after checking connectivity. Repeat POST only after understanding the previous result, then match the saved ID; stop here if the failure persists.

## Request a worker report

```bash
curl -fsS -X POST "https://$APP_HOST/api/reports"
printf '\n'
```

Example:

```json
{"id": "…", "status": "queued"}
```

Wait for processing, then retrieve reports:

```bash
curl -fsS "https://$APP_HOST/api/reports"
printf '\n'
kubectl logs deployment/worker -n notes --tail=10
```

GET must contain the submitted ID and `note_count`. Retry after a few seconds if absent. This verifies API → SQS → worker → RDS.

## Compare pod IPs and logs

```bash
kubectl get pods -n notes -l app=frontend -o wide
```

Example:

```text
NAME                        READY   STATUS    RESTARTS   AGE   IP
frontend-7c8d9f6b5d-abc12    1/1     Running   0          10m   10.20.44.78
frontend-7c8d9f6b5d-def34    1/1     Running   0          10m   10.20.54.165
```

Compare IPs with Healthy targets. `READY 1/1` means the pod container is ready.

```bash
kubectl logs -n notes -l app=frontend --tail=10 --prefix=true
```

Example log excerpt:

```text
[pod/frontend-…/frontend] … "GET /api/healthz HTTP/1.1" 200 …
```

`--prefix=true` identifies pod/container. Logs also include health checks; the last lines may not contain every request you sent.

## Verify WAF participation

```bash
curl -sS -o /dev/null -w '%{http_code}\n' \
  -H 'x-workshop-test: block-me' "https://$APP_HOST/"
```

A full lab returns **403** with the header and **200** without it. WAF ACL `eks-did` must list ALB `eks-did-notes` under Associated AWS resources. If using `--without-waf`, record the skipped edge test; HTTPS success alone is not WAF completion.

## Preparation acceptance criteria

| Check | Expected |
|---|---|
| Nodes | Two Ready nodes, private IPs |
| db-init | Complete |
| Deployments | Frontend 2/2, API 2/2, worker 1/1 |
| Domain/HTTPS | Homepage 200, valid certificate |
| WAF | ALB association and test-header 403 |
| API | Health contains `workload: api` |
| RDS | Retrieve the note just created |
| SQS/worker | Retrieve the report with matching ID |
| NetworkPolicy | Chapter 3 policies not yet applied |

```bash
kubectl get networkpolicy -n notes
```

Fresh labs show `No resources found in notes namespace.` On a reused hardened lab, record existing policy; do not call it a pre-policy baseline.

![Deployed application](/images/application-live.png "Frontend, API, and worker operate with RDS and SQS.")

Continue to [Request Flow](/2-network-security/1-request-flow/). Subsequent commands now have a configured `$APP_HOST` and running application pods.
