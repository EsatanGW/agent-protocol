# Change Surfaces

> **Canonical definition of the four-surface model.** Other documents should reference this file rather than redefine surfaces locally.

## Core concept

Every system change leaves traces on one or more **surfaces**. A surface is not a technical layer (frontend / backend / DB); it is a **dimension through which the change is perceived**.

Identifying which surfaces a change touches is the first step of the entire methodology.

---

## The four core surfaces

### 1. User surface

What a real human user sees, clicks, waits for, errors on, and interprets.

| Element | Meaning |
|---------|---------|
| route / page / component | Page structure and UI components |
| interaction | Clicks, drags, gestures |
| copy / i18n | Text and translations |
| validation / loading / empty / error states | State feedback |
| accessibility (a11y) | Accessibility support |

### 2. System interface surface

How the system talks to other systems, services, or modules.

| Element | Meaning |
|---------|---------|
| API (REST / GraphQL / RPC) | External or internal APIs |
| event / message | Events, message queues |
| job / task | Scheduled or background work |
| webhook / callback | External callbacks |
| external integration | Third-party integrations |
| outward contracts | SDKs, public schemas, shared types |
| **uncontrolled external dependencies** | Third-party SDK upgrades, platform OS / store policy changes, upstream API deprecation |

**Sub-categorization: controlled vs uncontrolled**

The system interface surface splits into two subtypes with different handling:

| Subtype | Definition | Upgrade-cadence control | Examples |
|---------|------------|--------------------------|----------|
| **Controlled interface** | Contract / interface for which this team / project is the primary implementer + primary consumer | This side decides | In-house API between services, shared internal types / enums / protos, in-house SDK |
| **Uncontrolled interface** | Contract / interface defined by an external party; this project is a consumer | Counter-party decides | Third-party SDK, OS / browser / platform policy, app store rules, upstream API deprecation, shared modules provided by other teams |

**Why the distinction matters:**
- Controlled interface changes can be paced — same PR can update both sides; breaking changes can be merged atomically.
- Uncontrolled interface changes cannot be paced. You can only: (a) observe they are coming (b) stay in sync before they break you.
- Different risk-management strategies apply to each.

### 3. Information surface

What data is described, stored, passed, and validated.

| Element | Meaning |
|---------|---------|
| schema / field / type | Data structure |
| enum / status | Discrete status classifications |
| validation rules | Validation rules |
| config / feature flag | Configuration and switches |
| source of truth | Authoritative source for a piece of information |

### 4. Operational surface

Evidence left after the change ships; what operators, on-call responders, and compliance auditors use.

| Element | Meaning |
|---------|---------|
| log / audit trail | Logs, audit records |
| metrics / telemetry | Metrics, telemetry |
| changelog / migration note | Change history, migration instructions |
| docs / README | Developer-facing documentation |
| rollout / rollback plan | Deployment and rollback plans |
| alert / dashboard | Monitoring alerts, dashboards |

---

## Composable extension surfaces

The four core surfaces cover most technical systems. For specialized domains, one or more **extension surfaces** are frequently necessary. Extensions do not replace the core four — they sit alongside them.

### Asset surface (commonly needed in game / media / graphics domains)

What non-code artifacts the change touches.

| Element | Examples |
|---------|----------|
| art / texture / 3D model | Sprites, textures, meshes |
| audio / music / sound effect | BGM, SFX |
| animation / particle / VFX | Animations, particles, visual effects |
| font / shader | Fonts, shaders |
| level / scene / prefab | Scene data |
| localized audio | Localized voice |

### Experience surface (commonly needed in game / consumer app domains)

How the change affects the **felt experience** — not the same as the user-interaction surface.

| Element | Examples |
|---------|----------|
| pacing / flow | Pacing, flow |
| feedback juice | Hit feedback, impact |
| difficulty / balance | Difficulty, balance |
| reward cadence | Reward cadence |
| retention / engagement | Engagement metrics |
| emotion / tone | Atmosphere, tone |

### Performance-budget surface (required in real-time interactive / high-load domains)

Whether the change fits within the system's performance envelope.

| Element | Examples |
|---------|----------|
| frame rate / latency | Target framerate, response latency |
| memory / CPU / GPU | Memory, CPU, GPU budgets |
| bandwidth / network | Network throughput |
| storage / I/O | Disk I/O |
| load capacity / concurrency | Throughput, concurrency |
| battery / thermal | Battery, thermal |
| cost per operation | Cost per unit of work |

### Data-quality surface (essential in data / analytics / ML domains)

Whether the change affects the **accuracy, completeness, or freshness** of data flowing through the system.

| Element | Examples |
|---------|----------|
| schema-level invariants | Uniqueness, referential integrity, enum closure |
| freshness / lag | Event-stream lag, ETL SLA |
| completeness | Rate of missing / null fields |
| lineage | Which upstream does this downstream depend on |
| backfill / correction policy | How bad data is repaired |
| dimensional consistency | Same entity across datasets |

### Hardware interface surface (essential in embedded / IoT / robotics domains)

How the change talks to physical devices or sensors.

| Element | Examples |
|---------|----------|
| device drivers / bus protocols | Driver code, bus protocol interfaces |
| firmware / OTA payload | Firmware updates |
| calibration data | Calibration values |
| sensor / actuator timing contracts | Hard real-time timing constraints |

### Model surface (essential in ML / AI domains)

The learned-artifact layer of the system.

| Element | Examples |
|---------|----------|
| model weights / checkpoints | Model files |
| training dataset | Training data version |
| hyperparameters / training config | Hyperparameters |
| evaluation metric contracts | "A model is acceptable when..." |
| inference runtime / quantization | Runtime, quantization |

### Compliance / regulation surface (essential in finance / healthcare / regulated domains)

Legal or regulatory requirements the change touches.

| Element | Examples |
|---------|----------|
| data-retention / deletion rules | Retention, right-to-be-forgotten |
| consent capture | User consent |
| audit-report content / format | Audit requirements |
| jurisdiction-specific behavior | Region-specific legal handling |

### Process / human-workflow surface (any domain)

The human operational workflows the change affects.

| Element | Examples |
|---------|----------|
| customer support SOP | Support playbooks |
| on-call runbook | On-call procedures |
| editor / operator workflow | Back-office workflows |
| training / certification requirements | Staff training |

### Real-world effect surface (required wherever the change reaches outside the system)

When the change reaches **things that happen in the real world and cannot be rolled back**.

| Element | Examples |
|---------|----------|
| payment / charge / transfer | Payments, refunds |
| push / email / SMS delivery | Outbound notifications |
| physical shipment / print | Physical goods, print runs |
| on-chain transactions | Blockchain state |
| external signals (voice to a platform) | Any outward signal |

---

## Cross-cutting concerns — not surfaces, but checks across every surface

Six concerns must be evaluated for every surface a change touches. They are not themselves surfaces:

1. **Security** — auth, authorization, PII, secret handling, threat model
2. **Performance** — latency, throughput, resource budgets
3. **Observability** — metrics, logs, traces, alerts
4. **Testability** — what test levels exist, can this be tested at all
5. **Error handling** — classification, propagation, recovery
6. **Build-time risk** — codegen drift, shrinking / minification, AOT compile, asset pipeline, determinism

See `docs/cross-cutting-concerns.md`.

---

## Using the model

### 60-second opener

For every change, answer in order:

1. Which **core surfaces** does this touch?
2. Does the domain need any **extension surfaces**? Map them to a core first, then declare the extension.
3. For each surface touched: is it **primary** (SoT lives here), **consumer** (will re-sync because of primary), or **incidental** (touched but not load-bearing)?
4. Which **cross-cutting concerns** apply per-surface?
5. Which **consumer** category does each affected party fall into (see `breaking-change-framework.md`)?

### When "only one surface" sounds convenient

Claiming "this only touches the system-interface surface" is almost always a tell that you haven't checked. Every API change has matching documentation (operational), validation rules (information), and at least downstream dashboards (operational). Surface-one-only is the exception, not the rule.

### Escape hatch

If your domain genuinely doesn't fit any extension, declare a `custom` surface in the manifest and cite the `docs/bridges/*-stack-bridge.md` where the custom surface is defined. Never invent surfaces at the per-change level — always register them in a bridge first.

---

## See also

- `docs/source-of-truth-patterns.md` — where the authoritative version of each informational asset lives
- `docs/cross-cutting-concerns.md` — the six concerns applied per-surface
- `docs/breaking-change-framework.md` — consumer classification and severity matrix
- `docs/rollback-asymmetry.md` — per-surface rollback modes
- `docs/bridges/` — stack-specific surface mappings
