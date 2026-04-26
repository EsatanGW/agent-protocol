# Change Manifest Cookbook

> **Companion to [`change-manifest-spec.md`](change-manifest-spec.md).** The spec defines fields, semantics, and conditional rules. This cookbook holds the **applied material** that does not change the spec but helps you *use* it: CI integration recipes, AI-usage modes, the mission-shaped manifest pattern, and a tour of the worked examples under `skills/engineering-workflow/templates/manifests/`.
>
> If you need a normative rule, the spec is the source. If you need a worked recipe, this is the place.

---

## CI integration (recommended)

Add a validation job to your CI:

```yaml
# Illustrative: .github/workflows/change-manifest-validate.yaml
- name: Validate manifest
  run: |
    ajv validate \
      -s schemas/change-manifest.schema.yaml \
      -d "$(git diff --name-only origin/main | grep change-manifest)"
```

Additional gates the methodology enforces beyond pure schema conformance:

- `phase == signoff` → every `primary` surface must have evidence with `status: collected`.
- `breaking_change.level in [L3, L4]` → PR requires a designated reviewer.
- `rollback.overall_mode == 3` → a named approver must appear in `residual_risks.accepted_by`.

The reference implementation of these gates lives under [`reference-implementations/`](../reference-implementations/) (see its [`INVENTORY.md`](../reference-implementations/INVENTORY.md) for the runtime-glue / documentation classification). The full algorithm is specified in [`automation-contract-algorithm.md`](automation-contract-algorithm.md).

---

## Modes of AI use of the manifest

### Mode A: generation (AI produces the manifest)

During Phase 1 / 2 (investigate / plan), AI reads the requirement → produces a **draft manifest**. That draft is AI's **declared understanding** of the change; humans calibrate against it faster than they would against prose.

### Mode B: validation (AI checks an existing manifest)

During Phase 4 / 5 (implement / review), AI compares the manifest against the real diff:

- For the surfaces the diff actually touched, is each one recorded in the manifest?
- Manifest claims `rollback.overall_mode: 1`, but the diff includes an irreversible migration?
- Manifest has no `playtest`, but the diff touches experience-related UI?

### Mode C: hand-off (between agents)

An upstream agent (e.g. an investigate / Planner agent) produces a draft manifest. A downstream agent (Implementer / Reviewer) uses that manifest as both context and a contract constraint. The Planner / Implementer / Reviewer envelope is specified in [`multi-agent-handoff.md`](multi-agent-handoff.md); the role-permission matrix is enforced by the `role-consistency` CI job.

---

## Mission-shaped manifests

Some changes are *exploratory* — the Implementer does not know up front which approach will satisfy the requirement, only that the requirement carries a measurable acceptance bar. A typical example: "cut /search p95 latency from 850ms to <200ms with zero ranking drift on the golden corpus." The implementation path is unknown; what is known is the contract under which any candidate fix is accepted.

This shape sometimes goes by names like "mission" or "evaluator contract" in other systems. In agent-protocol it is **not a separate artifact category** — it is a Change Manifest whose acceptance bar happens to be numeric and whose verification rows are tagged `evidence_plan[*].tier: critical`. No new schema fields are involved.

**Authoring conventions for a mission-shaped manifest:**

1. **Acceptance criteria as critical evidence.** Every measurable acceptance criterion (latency, accuracy, coverage, error budget, parity check, etc.) becomes one `evidence_plan[*]` row with `tier: critical` and a numeric pass threshold stated in the row's `summary`. Per [`automation-contract.md`](automation-contract.md) §Evidence tier and [`automation-contract-algorithm.md`](automation-contract-algorithm.md) §Rule 2.11, missing or rejected critical evidence blocks Phase 6 sign-off.
2. **Hypotheses in `assumptions`.** The hypotheses the exploration starts from go in the `assumptions` array with explicit `confidence` and `validation_plan`. Each one is an explicit prediction about the cause of the problem, not a vague background statement.
3. **Invalidations in `implementation_notes`.** As the Implementer profiles and iterates, hypotheses confirmed or refuted are recorded as `implementation_notes[*].type: assumption_validated` / `assumption_invalidated`. The audit trail captures *what was tried and ruled out*, not only *what shipped* — this is what distinguishes governed exploratory work from undocumented thrashing.
4. **Residual risk for unexplored regions.** A numeric evaluator contract pins a corner of the space; the regions it does not pin are still risk. `residual_risks` enumerates them honestly rather than treating the contract as proof of complete coverage. Self-set acceptance bars are not the same as exhaustive verification — a mission-shaped manifest that lists no residual risk is a misuse signal.
5. **Rollback discipline still applies.** Exploratory framing does not relax `rollback`; the rollback mode is judged by what the change does in production, not by how it was discovered.

**What `tier` does and does not allow:**

- `tier: critical` makes a single evidence row a hard ship gate. It does not make the manifest itself "mission-shaped"; a CRUD change with one regulatory critical evidence row is not a mission. The shape is determined by *exploratory framing + numeric acceptance bar* — multiple critical rows mapped to acceptance criteria, hypotheses in `assumptions`, invalidations in `implementation_notes`.
- `tier` is not a way to express progress, importance, or urgency. Use it strictly for "missing this evidence blocks ship."

**Why this is not a separate artifact category.** Adding a parallel "mission" artifact would split the source of truth — exploratory and non-exploratory work would record different things in different places, and the audit trail would lose its single shape. The Change Manifest is rich enough to express both: the schema's `tier`, `assumptions`, `implementation_notes` types, and `residual_risks` are exactly the slots a mission needs. Use them.

**Worked example:** [`skills/engineering-workflow/templates/manifests/change-manifest.example-mission-evaluator.yaml`](../skills/engineering-workflow/templates/manifests/change-manifest.example-mission-evaluator.yaml) shows a /search-latency mission with three critical evidence rows (load-test threshold, golden-corpus parity, canary p95), three hypotheses (one validated, one invalidated), and three residual risks naming the unexplored regions.

---

## Example tour

The 6 templates under [`skills/engineering-workflow/templates/manifests/`](../skills/engineering-workflow/templates/manifests/) cover the most-asked manifest shapes. Read the one closest to your change before drafting.

- [`change-manifest.example-crud.yaml`](../skills/engineering-workflow/templates/manifests/change-manifest.example-crud.yaml)
  - Simple CRUD (new field).
  - SoT patterns 1 + 3 + 4, breaking L0, rollback mode 1.
  - Demonstrates the **minimum skeleton** manifest.

- [`change-manifest.example-mobile-offline.yaml`](../skills/engineering-workflow/templates/manifests/change-manifest.example-mobile-offline.yaml)
  - Mobile offline-edit sync.
  - SoT patterns 7 + 8 + 10, breaking L1, rollback mode 2.
  - Demonstrates temporal-local, codegen, host-lifecycle, uncontrolled_interfaces, escalations.

- [`change-manifest.example-game-gacha.yaml`](../skills/engineering-workflow/templates/manifests/change-manifest.example-game-gacha.yaml)
  - Game live-ops gacha drop-rate adjustment.
  - experience + real_world + compliance surfaces.
  - SoT patterns 2 + 9, breaking L1, rollback mode 3.
  - Demonstrates playtest, post_delivery, rollback_mode_3 escalation, compensation_plan.

- [`change-manifest.example-mission-evaluator.yaml`](../skills/engineering-workflow/templates/manifests/change-manifest.example-mission-evaluator.yaml)
  - Search-latency mission with measurable evaluator contract.
  - SoT patterns 1 + 4, breaking L0, rollback mode 1.
  - Demonstrates `evidence_plan[*].tier: critical` mapped to acceptance criteria, `assumptions` carrying exploratory hypotheses, `implementation_notes` recording validations and invalidations, `residual_risks` naming unexplored regions.

- [`change-manifest.example-multi-agent-handoff.yaml`](../skills/engineering-workflow/templates/manifests/change-manifest.example-multi-agent-handoff.yaml)
  - Planner → Implementer → Reviewer progression of one manifest, encoded as multi-document YAML.
  - Demonstrates field-write ownership across phases, anti-collusion identity recording, and the Reviewer-only `approvals` block.

- [`change-manifest.example-security-sensitive.yaml`](../skills/engineering-workflow/templates/manifests/change-manifest.example-security-sensitive.yaml)
  - JWT signing-key rotation: SoT pattern 8 (Dual-Representation), L1 breaking change escalated to L2 structurally because long-tail consumers cannot refresh synchronously, mode-3 compensation-only rollback because issued tokens cannot be recalled.
  - Demonstrates `cross_cutting.security` with `pii_access_added` / `supply_chain_review_needed` rationales, mixed `per_surface_modes`, and two resolved `escalations`.

---

## Where this cookbook fits

This file lives next to the [`change-manifest-spec.md`](change-manifest-spec.md) and is **non-normative**: nothing here introduces a new rule. If a recipe in this cookbook contradicts the spec, the spec wins and the cookbook should be edited. If you find yourself wanting to write a new normative rule, put it in the spec; the cookbook stays for applied material that helps users adopt the spec without growing it.
