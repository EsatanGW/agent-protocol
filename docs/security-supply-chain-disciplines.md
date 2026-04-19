# Security & Supply Chain Disciplines

> **English TL;DR**
> Promotes security from a "cross-cutting checklist" to a first-class discipline on par with rollback-asymmetry and breaking-change frameworks. Covers surface-first threat modeling, supply-chain as uncontrolled interface, dependency SoT, secret lifecycle, compliance integration, and incident response — all tool-agnostic.

The security checklist in `cross-cutting-concerns.md` is a review aid.
But once a change enters finance, healthcare, regulated data, authN/Z, PII, or the company's **crown-jewel data**,
checklist density is not enough. This document promotes security and supply chain to a dedicated discipline on par with rollback and breaking-change.

**This document does not name any specific tool, scanner, cloud service, or commercial compliance product.**
Tool mappings are left to each stack bridge.

---

## Why security needs a dedicated document

Compared to rollback and breaking-change:

- Rollback has "modes 1–3 + the asymmetry table."
- Breaking change has "L0–L4 severity matrix + consumer classification + migration-path decision tree."
- Security has only a checklist.

As a result, most teams treat security as "something to glance at during review" rather than "a structured analysis starting in Phase 0/1/2."

Real security discipline, like the two documents above, is a **structured analysis method**, not a tick-box.

---

## Step 1: surface-oriented threat modeling

A common failure of threat modeling is "build it once, drop it in the wiki, nobody reads it."
This methodology's approach: **anchor threat modeling to the four surfaces** so it is naturally embedded in the Phase 0/1 analysis.

### Six threat classes, mapped to the four surfaces

Using the industry-standard six categories (identity spoofing, tampering, repudiation, information disclosure, denial of service, elevation of privilege), each class has a typical form per surface:

| Threat class | User surface | System-interface surface | Information surface | Operational surface |
|--------------|--------------|--------------------------|---------------------|---------------------|
| Spoofing | Session hijack, phishing | API-key theft, unverified webhook | Forged-identity writes | Stolen ops account |
| Tampering | Client-side state mutation | Modified request / payload | Unauthorized writes to data | Log / audit mutation |
| Repudiation | "I didn't do that action" | No request trace | No audit trail | No operational record |
| Information disclosure | UI leaks another user's data | Response includes extra fields | Unencrypted DB at rest | Logs contain PII / secrets |
| Denial of service | Client resource exhaustion | API flooded | DB table locks | Logs fill disk |
| Elevation of privilege | UI exposes over-privileged features | Privilege-escalating call | Row-level security bypass | sudo / admin leak |

### How to use

After the Phase 1 SoT map is written, ask one extra question:
> "On this surface, which of the six threat classes have **material risk** for this change?"

Not every class × surface cell needs assessment. Ask only: **does this change alter the risk face of this cell?**
If yes → add to the Phase 2 security verification items. If no → leave a one-line note explaining why it was skipped.

---

## Step 2: supply chain = uncontrolled interface

The "uncontrolled interface" sub-category in `surfaces.md` already identifies the essence of third-party dependencies.
Supply-chain discipline expands that requirement **into an executable process.**

### Four categories of supply-chain dependency

| Category | Example | Typical risk |
|----------|---------|--------------|
| Direct dependencies | Packages / SDKs / libraries you explicitly pulled in | Their own vulnerabilities, hostile takeovers, license violations |
| Transitive dependencies | Dependencies of your dependencies | Invisible vulnerabilities, version conflicts |
| Runtime dependencies | Runtime, interpreter, container base image, package manager, OS | Base-image vulnerabilities, runtime injection |
| Build-time dependencies | Compilers, bundlers, codegen, CI runners, secret providers | Build-time compromise (a classic supply-chain-attack vector) |

The most commonly overlooked category is **build-time dependencies** — code review does not see them, but they can reach the artifact.

### Supply chain as a source of truth

**Key observation:** the **version number** of every external dependency you use is itself an SoT.
If it is not registered in the manifest's `sot_map`, you have no discipline over that SoT.

Recommended: use a dedicated pattern in `sot_map`: **`supply-chain-defined`**
(the schema allows declaration via `custom_name`), recording:

- Where the authoritative version is pinned (lockfile, manifest, base-image tag, checksum).
- Any known deprecation timeline.
- Whether an advisory subscription channel exists (subscribe-once, not look-up-after-incident).

### Three minimum requirements

Any project claiming "supply-chain discipline" must have at minimum:

1. **Dependency list is enumerable** — can answer "which direct + transitive dependencies am I using, at which versions, right now."
2. **Vulnerability scanning is automated** — does not rely on a human checking advisories; has a scheduled (at least weekly) automated scan channel.
3. **Decision record when introducing a new dependency** — when adding a non-trivial dependency, the manifest has at least one sentence on "why this one, what alternatives were considered."

Without all three, supply-chain security is lip service.

---

## Step 3: secret lifecycle

Secrets (API keys, DB passwords, signing keys, OAuth secrets) **cannot be managed by human discipline alone**.
They must have an explicit lifecycle contract.

### Five stages

```
Generate → Distribute → Use → Rotate → Revoke
```

Minimum requirements per stage:

| Stage | Minimum requirement |
|-------|---------------------|
| Generate | Generated by a secret-management system, not human-chosen (avoid weak secrets). |
| Distribute | Delivered via env vars / mounted secrets / just-in-time injection; never in repo, never in CI log, never in error messages. |
| Use | Consumer does not cache to disk, does not print to logs (log redaction is an operational-surface obligation). |
| Rotate | Explicit period (high-sensitivity ≤ 90 days; low-sensitivity ≤ 1 year); rotation must not cause outage (dual-key coexistence during transition). |
| Revoke | On departure / leak / suspected compromise, revokable system-wide in < 1 hour with observability over residual usage. |

### Incident criteria for secret leakage

**Treat any of the below as a P0 incident, not P2:**

- Secret appears in git history (even after a force-push).
- Secret appears in CI logs or build artifacts.
- Secret appears in error messages or crash reports.
- Secret appears in a user-visible surface (UI / API response).

Incident handling is covered in Step 5.

---

## Step 4: compliance as its own surface

`surfaces.md` already lists the compliance surface as a composable surface.
This section defines when it **must** be activated, rather than optional.

### When compliance becomes primary

If any of the following is true → compliance surface must appear in `surfaces_touched` with at least one `role: primary`:

- Change involves PII / PHI / financial data / biometric data.
- Change alters retention periods or cross-border transfer paths.
- Change affects audit-trail content or retention.
- Change involves user consent / scope of authorization.
- Change involves legally mandated reporting / disclosure obligations.
- Jurisdictional regulator has active ongoing compliance oversight.

### Compliance SoT forms

A compliance SoT is typically **not code or schema**, but:

- Regulatory text / regulator interpretations.
- Contract clauses (with customers / partners).
- Internal policy docs (signed off by compliance / legal).

The manifest's `sot_map` must be able to point at these external documents (via URL, document version, or internal doc ID).
If the external document updates, the automation layer (tier 3 drift detection in `automation-contract.md`) should detect and flag it.

---

## Step 5: incident response as an operational surface

Phase 8 handles "post-launch observation."
Incident response is one branch of that, with its own discipline.

### Four incident stages

| Stage | Goal | Anti-pattern |
|-------|------|--------------|
| Detect | Shortest possible time from signal to "this is an incident" | Wait for customer complaints |
| Contain | Stop-the-bleeding: isolate, pause, rate-limit, rollback | Investigate and repair at the same time (risks widening damage) |
| Remediate | Return to normal operation | Bypass tests and ship directly |
| Learn | Produce a blameless post-mortem, update the methodology | Hunt individuals for blame |

### Post-mortem as a manifest derivative

An incident-fix change **itself** needs a manifest (like any change).
But it additionally produces an **incident post-mortem** with fields:

- Timeline (detection, containment, remediation, recovery).
- Root cause (not just symptom).
- SoTs and consumers involved (retrofill the missing `sot_map` entries).
- Methodology failure point (which step should have caught it and did not).
- Methodology improvement proposals (what should this methodology learn from this incident).

The last item is **feedback** into `docs/` to let the methodology evolve. Without it, incidents recur.

---

## Merging into existing phases

This discipline **adds no new phase**. It folds into existing phases:

- **Phase 0 Clarify:** decide if the compliance surface is primary; decide which of the six threat classes are relevant.
- **Phase 1 Investigate:** register supply-chain dependencies in `sot_map`; enumerate secrets involved.
- **Phase 2 Plan:** define verification for each relevant threat class; secret rotation / revocation plan (if applicable).
- **Phase 3 Test Plan:** threat-mapped negative tests (unauthorized calls, privilege escalation, injection).
- **Phase 4 Implement:** follow the secret five-stage contract; new dependencies require an ADR.
- **Phase 5 Review:** run the security checklist in `cross-cutting-concerns.md` + the structured analysis in this document.
- **Phase 8 Observe:** watch for anomalous logins, anomalous API calls, secret-usage trails.

---

## Anti-patterns

- **Mindless checklist ticks:** every item checked but nothing actually verified.
- **Security outsourcing:** assuming "the security team will catch it" and skipping surface-first threat modeling in engineering.
- **One-shot scanning:** running vulnerability scans only before release; nothing blocking at dependency introduction.
- **Paper secret rotation:** policy exists but no actual rotation (check the last-rotated timestamp).
- **Post-mortem as blame doc:** post-mortems turned into accountability documents; team stops admitting mistakes.
- **Compliance as reporting:** compliance requirements treated as after-the-fact reports, not design-stage constraints.

---

## Relationship to other documents

- `cross-cutting-concerns.md` — security / performance checklists (this document is the upstream discipline of that checklist).
- `surfaces.md` — compliance surface, uncontrolled-interface sub-category.
- `source-of-truth-patterns.md` — this document proposes the `supply-chain-defined` SoT pattern.
- `breaking-change-framework.md` — breaking-change assessment for the supply chain still goes through that framework.
- `rollback-asymmetry.md` — incident rollback choices go through that framework.
- `post-delivery-observation.md` — Phase 8 links to incident response.
- `ai-operating-contract.md` §5 — AI must escalate when touching security / PII / auth paths.
