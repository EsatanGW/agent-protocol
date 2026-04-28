# Observability Legibility Discipline

> **English TL;DR**
> Three rules that keep the running system's *operational evidence* (logs, metrics, traces) reachable by an agent in-loop, not only by a human after the fact. **Rule 1 — Structured-by-default.** Every log, metric, trace must be emitted in a parseable shape; an agent that can read source but cannot read runtime output has half the loop missing. **Rule 2 — Per-change isolation.** A change being verified must be observable on its own runtime stack (per-worktree, per-branch, per-task), so its evidence is not contaminated by ambient traffic from unrelated changes. **Rule 3 — Query-by-capability, not by tool.** Agents reach observability via three capability categories — log query, metric query, trace query — never by binding to a specific backend. The discipline is the operational-surface counterpart of `repo-as-context-discipline.md`: anything an agent cannot query in-context effectively does not exist as evidence. Used at Phase 4 (capture), Phase 5 (review), and Phase 8 (post-delivery observation). Defaults to advisory severity; runtime bridges may promote to block.

---

## Why this discipline exists

The methodology already names observability as a cross-cutting concern (`cross-cutting-concerns.md` §Observability). What it does **not** say in one place is the contract an observability stack must satisfy *for an agent* — not for a human SRE — to make the running system legible. Without that contract, three failures recur:

- **Source-readable, runtime-illegible changes.** The agent reads code fluently but cannot answer "did this change increase p99 latency?" — the metric exists but is locked behind a UI the agent cannot drive. Application-driven evidence (`application-driven-loop.md`) collapses to BEFORE/AFTER screenshots only, and second-order effects (a fix that doubled background-task traffic) escape the loop.
- **Cross-change contamination.** Two changes share one runtime instance. Change A's noise pollutes change B's metric baselines; both Reviewers fail to spot real regressions because the signal-to-noise ratio is ruined upstream.
- **Tool lock-in.** The team's observability stack is upgraded; every methodology rule that named the old backend by class (Prometheus, Loki, Jaeger, X-Ray) drifts; rules quietly stop firing. The discipline must be capability-shaped, not tool-shaped, to survive backend changes.

This discipline is the operational-surface counterpart of `repo-as-context-discipline.md`: that doc says repo-resident knowledge governs agent behaviour; this doc says runtime-queryable evidence governs agent verification. Both reduce to "what an agent cannot reach effectively does not exist."

---

## The three rules

### Rule 1 — Structured-by-default

Every log line, metric sample, and trace span the system emits must be in a shape an agent can parse without bespoke handling: typed fields, stable keys, JSON or another self-describing format. Free-form text logs that require regex archaeology are a non-conformance — an agent that reads source fluently and runtime output crudely has half the verification loop missing.

**Per-Phase enforcement points.**

- Phase 1 (Survey) — when registering the operational surface, the manifest's `sot_map` row for each emission point names the shape (e.g. `log_format: structured-json`, `metric_dimensions: [...]`).
- Phase 3 (Test plan) — verification rows that cite log / metric / trace evidence resolve to a structured-format query, never to a screenshot of a dashboard.
- Phase 5 (Review) — Reviewer rejects an evidence row that cites "checked the dashboard, looked OK" without a query expression.

**Failure mode.** "Logs are debug strings; we'll structure them later." Later is Phase 8 of an incident, not now. The retrofit cost grows with log volume.

### Rule 2 — Per-change isolation

A change being verified must run against its own observability surface, populated by its own per-worktree (or per-branch, or per-task) runtime instance. The instance can be a containerized stack, a dedicated namespace on shared infrastructure, or a process tree marked with the change's identifier — what matters is that the change's evidence is queryable in isolation from changes the agent did not author.

**Per-Phase enforcement points.**

- Phase 4 (Implement) — the application-driven loop (`application-driven-loop.md`) presupposes per-change isolation; without it, step 1's "clear runtime event streams" cannot run cleanly.
- Phase 5 (Review) — Reviewer's sampling right (per `ai-operating-contract.md`) extends to re-running queries against the change's isolated stack, not just re-reading captured artefacts.
- Phase 8 (Observe) — the per-change isolation ends at delivery; Phase 8 observation runs against the production stack, with the change identified by its release marker. The boundary between "isolated verification" and "production observation" is a deliberate handoff, not a gradient.

**Failure mode.** A staging environment shared across all in-flight changes. Cross-change contamination is undiagnosable; the Reviewer cannot tell whether a metric blip belongs to this change or to an unrelated change merged 20 minutes earlier.

### Rule 3 — Query-by-capability

Agents reach observability through three **capability categories**, never through a specific backend's name:

- **Log query** — given a time window and a structured filter, return the matching log lines.
- **Metric query** — given a metric name, dimensions, and a time window, return aggregated samples.
- **Trace query** — given a trace identifier or a service-and-operation pair, return the matching spans.

The capability category names match `docs/glossary.md §Capability category` and the `evidence_plan[*].type` enum values (`log_sample`, `metric_diff`, `trace_span_check`). Runtime bridges map these capabilities to the team's actual backend; bridge files are the only place where backend names appear (per `CLAUDE.md §2`).

**Per-Phase enforcement points.**

- Phase 0 (Triage) — when the change's surface includes operational, the manifest's `capability_dependencies` row names "log query / metric query / trace query" rather than a backend.
- Phase 4 (Implement) — evidence rows record the query expression in a backend-agnostic form (e.g. PromQL, LogQL, TraceQL — these are query-language categories, not backend products) so the Reviewer can replay the query under the same capability category against any compatible backend.
- Phase 8 (Observe) — the post-delivery observation window's queries are recorded as query expressions, not as dashboard screenshots, so a future agent re-running the observation under a different backend can reproduce the check.

**Failure mode.** A rule that says "check the Datadog dashboard for 5xx spikes." The rule fires for one backend; when the team migrates to a different backend, the rule silently stops working. Capability-category framing — "run a metric query on `http_5xx_total` aggregated by service over the post-delivery window" — survives backend migration.

---

## Mapping to the manifest

The discipline resolves to existing manifest fields; no new schema is introduced.

| Discipline aspect | Manifest field | What the field carries |
|---|---|---|
| Structured emission shape | `sot_map[*].extension_fields.observability_shape` | One of `structured-json` / `structured-protobuf` / `unstructured-text` (the last is a non-conformance signal) |
| Per-change isolation | `verification_environment.kind` | One of `per-worktree` / `per-branch` / `per-task` / `shared-staging` (the last is a Rule-2 non-conformance signal at `breaking_change.level >= L2`) |
| Query expression | `evidence_plan[*].artifact_location` | The query text plus a pointer to the captured result; the query text is what reproduces the check, the result is what the Reviewer reads |
| Capability category | `evidence_plan[*].type` | One of `log_sample` / `metric_diff` / `trace_span_check` / `runtime_log` per `evidence-quality-per-type.md` |

A change that touches the operational surface and lacks rows in two or more of these columns has not satisfied the discipline; the manifest's `escalations[*].trigger` carries `observability_legibility_gap` and the change is reviewed against the gap.

---

## Per-rung minima (cross-reference with `autonomy-ladder-discipline.md`)

The autonomy ladder names the rung at which observability-stack evidence is required per surface. This discipline names the *shape* of that evidence.

| Rung | Operational surface | Information surface | User surface | System interface |
|---|---|---|---|---|
| L0 / L1 | Out of scope | Out of scope | Out of scope | Out of scope |
| L2 | Structured emission required; query expression captured for every cross-cutting check | Structured emission required | Structured emission required when application-driven loop runs | Structured emission required |
| L3 | Per-change isolation required; query-by-capability required | Per-change isolation required | Structured emission required | Per-change isolation required |
| L4 | All three rules in full force on every change | All three rules in full force | All three rules in full force | All three rules in full force |

---

## Anti-patterns

- **Dashboard-as-evidence.** A screenshot of a dashboard in `evidence_plan[*].artifact_location` instead of a query expression. Screenshots cannot be replayed; the Reviewer cannot re-run the check; the next agent that opens the manifest a month later cannot reproduce the verification.
- **Backend leakage in rules.** A normative rule that names "Datadog" or "New Relic" or "Splunk" rather than the capability category. Per `CLAUDE.md §2`, capability category names; bridge files name backends.
- **Shared-staging at L3+.** Per-change isolation is non-optional at L3 and L4. A team running L4 on shared staging is rung-claiming per `autonomy-ladder-discipline.md` §Anti-patterns.
- **Free-form text logs at L2+.** Unstructured logs are a Rule-1 non-conformance; an `escalations[*].trigger: observability_legibility_gap` entry must accompany the change, with a remediation plan in the manifest's `phase_log`.
- **Query-without-time-window.** A query expression that does not bound the time window is non-deterministic — re-running it later reads different data. Time windows are part of the query, not separate metadata.
- **"Observability is the SRE team's problem."** When observability is owned by a separate team, application-driven evidence becomes a hand-off, not a loop. The agent cannot close its own verification; the change waits on a human to cross-check. This is L2 at best, regardless of what the team's adoption record claims.
- **Rule-3 simulation by exporting metrics into the repo.** A team that exports yesterday's metric snapshots into the repo and claims they satisfy `repo-as-context-discipline.md` has confused "in-repo" with "in-context for this change." The query is what governs; a snapshot is one captured result, not the capability.

---

## Default severity and bridge promotion

The discipline defaults to **advisory severity** (per `automation-contract.md` Rule 2.13's posture). A non-conformance surfaces as a finding in the manifest's `phase_log` rather than blocking the merge. Runtime bridges may promote individual rules to **block** when the team's observability stack already meets the rule's bar — promotion is bridge-local and recorded in the bridge's `DEVIATIONS.md`.

The advisory default exists because retrofitting structured logging or per-change isolation onto a legacy stack is a multi-month project; blocking changes on it would freeze the methodology in place. Advisory findings still appear in the manifest, accumulate in the `anti-entropy-discipline.md` quality-score sweeps, and pressure the team toward the rung-stable shape.

---

## Cross-references

- `docs/cross-cutting-concerns.md` §Observability — the per-surface checklist this discipline operationalises.
- `docs/cross-cutting-concerns.md` §Application-driven verification — the discipline whose Phase 4/5/8 enforcement points overlap with this one.
- `docs/repo-as-context-discipline.md` — the source-of-truth-side counterpart; together they cover "what an agent cannot reach in-context effectively does not exist."
- `docs/autonomy-ladder-discipline.md` — names the rung × surface matrix this discipline supplies the shape for.
- `docs/post-delivery-observation.md` — Phase 8 observation cadence; query-by-capability is the shape of every observation in that window.
- `docs/evidence-quality-per-type.md` — per-evidence-type acceptance signals for `log_sample` / `metric_diff` / `trace_span_check` / `runtime_log`.
- `skills/engineering-workflow/references/application-driven-loop.md` — step 1 / step 3 / step 7 of that loop presuppose this discipline's three rules.
- `docs/automation-contract.md` Rule 2.13 (Evidence provenance) — the same posture (default advisory; bridges may promote to block) applies here.
