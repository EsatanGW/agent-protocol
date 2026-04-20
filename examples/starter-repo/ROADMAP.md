# ROADMAP

> Multi-session tracking artifact. One row per initiative, phase table per row.
> This starter example has one closed initiative to show the shape; a real repo
> accumulates rows over time and never deletes them (closed entries preserve
> the audit trail).

## Schema

```markdown
## <initiative-slug> — <one-line title>

- **Opened:** YYYY-MM-DD
- **Driver:** <who / which request>
- **Status:** planning | in_progress | paused | closed
- **Target version:** <semver>

| Phase | Scope | Artifact(s) | Gate verification | Status | Commit | Notes |
|---|---|---|---|---|---|---|

### Phase log
<free-form notes>
```

---

## Active initiatives

_(none active)_

---

## Closed initiatives

## add-healthz-endpoint — add /healthz liveness endpoint for orchestrator probes

- **Opened:** 2026-04-20
- **Driver:** Orchestrator migrated to a probe-based liveness contract; service needs a cheap, dependency-free endpoint to report readiness without hitting the DB.
- **Status:** closed
- **Target version:** 0.3.0 (minor — additive)

| Phase | Scope | Artifact(s) | Gate verification | Status | Commit | Notes |
|---|---|---|---|---|---|---|
| P0 | Confirm scope: which surfaces, which SoT, chosen mode | Change manifest stub (`change-manifest.yaml` Planner snapshot); mode = Lean-ish with manifest kept for handoff | Two surfaces identified (system_interface + operational); no new DB / schema / auth | ✅ passed | `abcd111` | Upgraded from Lean to Full-with-manifest because the endpoint will be observed by an external orchestrator (uncontrolled interface) |
| P1 | Implement endpoint + runbook note | `backend/routes/health.ts`; `docs/runbooks/probes.md` | Endpoint returns 200 JSON in 3ms p99 on staging; runbook lists expected response shape | ✅ passed | `abcd222` | No auth on /healthz is intentional — documented in manifest as residual risk + compensating check (route is narrowly scoped) |
| P2 | Collect evidence | `evidence/contract-test-output.txt`, `evidence/access-log-sample.txt`, `evidence/screenshot-notes.md` | `evidence_plan` items flipped to `status: collected` with `artifact_location` filled in | ✅ passed | `abcd333` | All three artifacts checked into `evidence/` |
| P3 | Review + sign-off + deliver | `change-manifest.yaml` Reviewer snapshot; approval from on-call lead | Review pass_with_followup on observability (metrics dashboard TBD); approver recorded | ✅ passed | `abcd444` | Follow-up tracked separately: dashboard for /healthz latency + error rate |

### Phase log

- The endpoint is dependency-free by design: no DB call, no cache lookup, no auth. This is the industry pattern for liveness (as opposed to readiness) probes.
- During P1, considered mounting under `/api/v1/healthz` to match other routes; rejected because orchestrator probes should hit the shortest stable path available, and versioning a liveness probe couples the probe contract to API versioning churn. Documented as a conscious deviation in the manifest's `implementation_notes`.
- Residual risk accepted: no rate-limit on /healthz. Reasoning: a DOS vector through a 200-byte handler is a smaller problem than a monitoring gap. Formal accept recorded in manifest `residual_risks`.
- The `evidence/screenshot-notes.md` is a text description (not an image) so the example stays text-only; a real project would drop an actual screenshot here.
