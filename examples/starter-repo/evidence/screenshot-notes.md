# Runbook screenshot notes

> A real project would drop a PNG here. This file keeps the starter-repo text-only so `git clone` doesn't need LFS.

## What the screenshot would show

Section "Liveness probes" added to `docs/runbooks/probes.md`:

```
## Liveness probes

Path:     GET /healthz
Response: 200 OK, application/json
Body:     {
            "status": "ok",
            "uptime_seconds": <integer>,
            "version": "<git sha7>"
          }

Orchestrator behavior:
- Probes every 30s
- 3 consecutive non-200 => pod restart
- No auth required; no logging at trace level (too chatty)

If the endpoint is unreachable:
1. Check process is bound to the expected port (default 8080)
2. Check `healthz_enabled` feature flag is on in the target environment
3. Orchestrator probe CIDR is 10.0.3.0/24 — firewall rule should allow

Escalate to on-call lead if 3 consecutive pods are restarted within 5 minutes.
```

## Evidence trail

- Runbook file:   `docs/runbooks/probes.md` (hypothetical path)
- Section header: `## Liveness probes`
- Cross-references: `backend/openapi/health.yaml` (contract) + `backend/routes/health.ts` (implementation)
- Validated by:   alice@example.com, 2026-04-20T15:20:00Z
