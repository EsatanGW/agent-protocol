# CI/CD Integration Hooks

> **English TL;DR**
> Vendor-neutral specification of *where* the methodology can be wired into an automation pipeline and *what each hook should check* — without binding to any specific CI/CD product. Defines seven hook points: (1) PR create → surface-label check, (2) PR create → cross-cutting checklist reminder, (3) PR update → docs-sync check, (4) PR update → SoT-change warning, (5) PR review → evidence attachment check, (6) pre-merge → Change Manifest schema validation, (7) post-merge → observation-window start. Each hook specifies: trigger event, input, expected output, advisory-vs-blocking policy. Principle: methodology stays usable *without* any hooks; automation is an accelerator, not a gate. Pairs with `automation-contract-algorithm.md` (the normative algorithm) and `reference-implementations/` (non-normative example validators).

Where the methodology can be wired into automation to accelerate adoption and reduce human oversight.
This document does not bind a specific CI/CD tool — it defines only the **hook points** and the **expected behavior**.

---

## Design principles

1. **The methodology does not depend on automation** — without any CI/CD integration, the methodology remains fully usable.
2. **Automation is an accelerator** — it reduces the risk of "forgetting to do something."
3. **Hooks are advisory, not mandatory** — teams choose what to wire in.

---

## Hook points at a glance

```
PR created
  → Hook 1: surface-label check
  → Hook 2: cross-cutting checklist reminder

PR content updated
  → Hook 3: docs-sync check
  → Hook 4: Source-of-Truth change warning

PR review
  → Hook 5: evidence attachment check

Pre-merge
  → Hook 6: completion-report existence check

Post-merge / post-deploy
  → Hook 7: Phase 8 observation reminder schedule
```

---

## Hook 1: surface-label check

**Trigger:** PR creation.
**Expected behavior:** verify that the PR description includes an `Affected Surfaces` block.

```yaml
# Example (vendor-agnostic CI pseudocode)
- name: Check surface tags
  run: |
    if ! grep -q "Affected Surfaces:" "$PR_BODY_FILE"; then
      echo "::warning::PR description is missing the Affected Surfaces block"
    fi
```

**PR template suggestion:**

```markdown
## Affected Surfaces
- [ ] User surface
- [ ] System-interface surface
- [ ] Information surface
- [ ] Operational surface
- [ ] Other: ___

## Mode
- [ ] Lean
- [ ] Full
```

---

## Hook 2: cross-cutting checklist reminder

**Trigger:** PR creation, based on the file paths touched.
**Expected behavior:** auto-suggest which cross-cutting items to check.

```
If the change touches auth / login / permission files:
  → Remind: confirm the system-interface security checklist.

If the change touches migration / schema files:
  → Remind: confirm the information-surface performance checklist.

If the change touches API route files:
  → Remind: confirm the security checklist (auth + rate limit + CORS).
```

---

## Hook 3: docs-sync check

**Trigger:** PR content update.
**Expected behavior:** when certain sources of truth are modified, warn that the corresponding docs likely need to update too.

```
If API endpoints are modified (routes/*, controllers/*):
  → Check whether API docs / OpenAPI spec were also updated.

If DB schema is modified (migrations/*):
  → Check whether models / DTOs were also updated.

If enum / status definitions are modified:
  → Check whether i18n keys / UI display were also updated.
```

**Implementation hint:** use file-path pattern matching; code parsing is not required.

---

## Hook 4: Source-of-Truth change warning

**Trigger:** PR modifies a file registered as a known source of truth.
**Expected behavior:** enumerate potentially affected consumers; prompt the reviewer to check.

This requires a mapping configuration (can live at the repo root):

```yaml
# .source-of-truth-map.yml
- source: "db/migrations/"
  consumers:
    - "models/"
    - "api/serializers/"
    - "docs/api/"
  message: "DB schema changed — confirm models, serializers, API doc are in sync."

- source: "config/feature_flags.yml"
  consumers:
    - "frontend/src/flags/"
    - "backend/services/"
  message: "Feature flag changed — confirm both frontend and backend are handled."
```

---

## Hook 5: evidence attachment check

**Trigger:** PR review.
**Expected behavior:** if the PR flags a public behavior change, check whether evidence is attached.

```
If PR description includes "public behavior: yes":
  → Check whether the PR comments or description contain screenshots / recordings / test logs.
  → If none, add a reminder comment.
```

---

## Hook 6: completion-report check

**Trigger:** pre-merge (Full-mode PRs).
**Expected behavior:** verify that a corresponding completion report exists.

```
If PR description includes "Mode: Full":
  → Check for docs/<ticket-id>*/completion-report*.md
  → If missing, block merge and remind.
```

---

## Hook 7: Phase 8 observation reminder

**Trigger:** post-merge / post-deploy.
**Expected behavior:** schedule reminders at T+24h, T+72h, T+7d for post-delivery observation.

```
Implementation options (choose one):
- Chat-bot scheduled message.
- Calendar event.
- Issue tracker auto-creates follow-up ticket.
- This repo's scheduled task (if any).
```

---

## Progressive adoption guide

Do not wire everything in at once. Suggested order:

| Stage | Hook | Rationale |
|-------|------|-----------|
| Stage 1 | Hook 1 (surface labels) | Lightest — pure reminder |
| Stage 2 | Hook 3 (docs sync) | Most common omission |
| Stage 2 | Hook 7 (Phase 8 reminders) | Builds the observation habit |
| Stage 3 | Hook 2 (cross-cutting) | Proactive security / performance defense |
| Stage 3 | Hook 4 (SoT warnings) | Requires mapping maintenance |
| Optional | Hook 5, 6 | Add once Full mode has matured |

---

## Relationship to the methodology

| Hook | Corresponding Phase | Corresponding document |
|------|---------------------|------------------------|
| Hook 1 | Phase 0 | `docs/surfaces.md` |
| Hook 2 | Phase 5 | `docs/cross-cutting-concerns.md` |
| Hook 3 | Phase 5 | `docs/source-of-truth-patterns.md` |
| Hook 4 | Phase 1 | `docs/source-of-truth-patterns.md` |
| Hook 5 | Phase 6 | Phase 6 sign-off requirements |
| Hook 6 | Phase 7 | Phase 7 delivery requirements |
| Hook 7 | Phase 8 | `docs/post-delivery-observation.md` |

---

## Relationship to runtime-layer hooks

This document defines **CI/CD-platform** hooks (fire on PR events, merge events). Its sibling, [`runtime-hook-contract.md`](./runtime-hook-contract.md), defines **agent-runtime** hooks (fire on tool use, response completion, commit). The two share the exit-code contract (`0 = pass`, `1 = fail`, `2 = warn`), so a rule implemented as a runtime hook can be lifted into a CI hook — and vice versa — with only the event-payload translation rewritten. Use the runtime contract when you want guardrails to fire *inside* the agent loop (pre-commit blocking, drift warnings on edit); use the CI contract when you want them to fire *after* the change leaves the agent (PR review, pre-merge).
