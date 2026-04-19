# Automation Contract

> **English TL;DR**
> `ci-cd-integration-hooks.md` describes *where* automation can plug in; this document defines *what* an automated validator must guarantee, as a capability contract, independent of any CI platform or programming language.
> Each runtime / stack bridge is expected to provide an executable that fulfils this contract. The methodology itself never ships a specific implementation.

This document defines what the methodology's automation layer must look like at the capability-contract level,
upgrading the grep-level pseudocode in `ci-cd-integration-hooks.md` into a formal contract any CI platform can implement.

**This document binds no tool and contains no source code in any language.**
Example implementations are left to each stack bridge (see `docs/bridges/`).

---

## Why this contract exists

Without a formal contract, the automation layer degrades along three paths:

- Each stack invents its own rules; they do not interoperate, so manifests cannot flow across agents.
- Validation only checks syntax (a valid schema is a green light), not semantic consistency.
- Discipline degrades to "hooks installed but nobody reads the warnings."

The contract locks down "what validators must at least do" while leaving "what validators are written in" to each bridge.

---

## Four automation tiers

On adoption, pick a tier — not "automation yes/no."

| Tier | Behavior | Failure consequence | When to use |
|------|----------|---------------------|-------------|
| L0 None | Manual checking | Relies on self-discipline | ≤ 2 people, prototype |
| L1 Advisory | Automated scan, advisory annotations | Does not block merge | Early adoption; discipline just landing |
| L2 Required | Failure must have an override record | Blocks merge but authorized bypass allowed | Default once the methodology has stabilized |
| L3 Blocking | Cannot be bypassed; fix-and-retry only | Fully blocks | Finance / healthcare / compliance-sensitive |

Within a single repo, **different checkpoints can be at different tiers** (e.g. secret scanning L3, manifest schema L2, evidence links L1).

---

## Three mandatory checking tiers

The automation layer must at minimum be able to answer three questions. Each tier is an **independent capability.**

### Tier 1: structural validity

**Question:** is the manifest's shape correct?

**Capability contract:**

- Can run schema validation on a single manifest file.
- Error reports must include: field path, expected value, actual value, link to the corresponding methodology section.
- Supports batch mode (validate many manifests at once).
- Supports `--strict` / `--lenient` modes (strict rejects unknown fields; lenient only warns).

**Minimum output format (platform-agnostic):**

```
<pass|fail> <manifest_path> <rule_id> <severity> <message> [<doc_ref>]
```

`rule_id` must be stable (different runtime implementations must use the same ID), so that when a manifest flows across agents, an upstream `waived_rules` entry remains interpretable downstream.

### Tier 2: cross-reference consistency

**Question:** do the facts the manifest claims match reality elsewhere in the repo?

**Capability contract (each bridge must implement at least one):**

- The surfaces declared in `surfaces_touched` — does the diff actually touch the corresponding region?
- The SoT file paths declared in `sot_map` — do they actually exist?
- The evidence paths declared in `evidence_plan.artifacts` — are they locatable?
- The third parties declared in `uncontrolled_interfaces` — are they in the dependency list?
- If the declared breaking-change level is ≥ L2, does a corresponding migration document path exist?

Implementations at this tier **may** use stack-specific tooling (e.g. a bridge can use that language's AST parser to determine whether SoT files were actually modified) — because it compares against real code.
But the **output format** still follows tier 1's uniform format.

### Tier 3: drift detection

**Question:** after time passes and other changes land, is the manifest still true?

**Capability contract:**

- Can detect `phase` / `last_updated` inconsistency (e.g. `phase: deliver` but `last_updated` is a month old → suspicious).
- Can detect later commits to SoT files in the manifest without any subsequent manifest declaring ownership (called **dangling SoT**).
- Can detect cycles or gaps in the `supersedes` chain.
- Can compare a `delivered` manifest against Phase 8 observation presence (if the manifest declared it needed observation).

This is the most expensive tier; it is recommended to run it only periodically on `main`, not on every PR.

---

## Waiver protocol

**An L2/L3 automation layer without a waiver mechanism will be bypassed.**
Rather than let people bypass silently, let bypasses leave a trace.

### Minimum waiver fields

For any automation failure to be allowed through, the manifest must include:

```yaml
waivers:
  - rule_id: <stable ID, matching tier-1 output>
    reason: <one sentence on why bypass is warranted this time>
    approver: <human identifier>
    expires_at: <ISO 8601 date, max 30 days>
```

- After `expires_at`, the waiver expires; the next check blocks again.
- `approver` cannot be an AI agent (AI cannot self-authorize bypass).
- Bypass without a waiver → check fails, and escalates (reported as if L3).

### Prohibited waiver patterns

- Global permanent waivers (`expires_at: never`).
- Vague reasons ("not applicable" / "known issue" are not valid).
- Approver is the change initiator (require a third party).

---

## Offline operability

The automation layer **must not** require network or cloud service.
All three tiers must be executable under:

- No outbound internet.
- No third-party API keys.
- Only repo files + manifest available.

This keeps the discipline usable on disconnected, offline CI runners, and restricted environments.
Checks that genuinely require network (e.g. remote contract-registry lookup) must **degrade to advisory**, not block.

---

## Non-functional requirements

- **Execution time:** tier 1 on a single manifest < 1 second; tier 2 on a PR diff < 30 seconds; tier 3 may be slower but must support background execution.
- **Reproducibility:** same input → same output (no dependence on time, randomness, or network state).
- **No side effects:** must not modify manifests, write files, or send notifications (notifications are the CI platform's responsibility).
- **Exit codes:** strictly follow `0 = pass`, `1 = rule violations`, `2 = tool / input error`; do not mix.

---

## Requirements on stack bridges

Each stack bridge must provide or point to:

1. **Tier-1 implementation** — schema validator (in whichever language the stack prefers).
2. **Tier-2 implementation** — at least one cross-reference check (typically the most error-prone one).
3. **Waiver-protocol mapping** — how the stack's CI platform records waivers.
4. **Execution command example** — an actually copy-pasteable one-liner.

Bridge-level implementations **may** name specific tools (that is precisely why bridges exist); but their interface still follows this contract.

---

## Anti-patterns

- **Over-automation:** 200 rules per PR → everyone rubber-stamps green → pick ≤ 10 genuinely important rules.
- **Silent skipping:** checks fail but CI logs are collapsed → at minimum post `rule_id` to the PR comment.
- **False-positive fatigue:** rules too strict, too frequent misfires → do not tough it out; downgrade to L1 or remove.
- **Covert bypass:** `[skip ci]` / `--no-verify` used routinely → immediately add to counter-metric monitoring (see `adoption-strategy.md`).
- **AI self-waivers:** AI sees red, adds a waiver, merges → violates `ai-operating-contract.md` §5; must escalate to a human.

---

## Relationship to other documents

- `ci-cd-integration-hooks.md` — describes hook points and triggers (this document is their semantic spec).
- `schemas/change-manifest.schema.yaml` — the actual tier-1 schema.
- `ai-operating-contract.md` §5 — escalation protocol when AI hits an L3 failure.
- `adoption-strategy.md` — counter-metric monitoring (bypass rate, waiver expiration rate, etc.).
- `docs/bridges/*-stack-bridge.md` — actual executable implementations.
