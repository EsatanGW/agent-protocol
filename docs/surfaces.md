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

## Common confusion — surface vs layer

A recurring question after reading external write-ups about agent-driven engineering (e.g. layered domain architectures of the form *Types → Config → Repo → Service → Runtime → UI; Providers; Utils*): **isn't a surface just a layer?** No — they sit on different axes, regulate different things, and prevent different failure modes. Conflating them collapses the methodology.

### The two are orthogonal, not interchangeable

| Dimension | Layer | Surface |
|---|---|---|
| What it slices | Code structure inside one codebase | A change's perception by external parties |
| Direction of cut | Vertical — abstraction altitude | Horizontal — who experiences the change |
| Question it answers | "Which layer does this code belong in?" | "Who sees this change? Who depends on it?" |
| Typical members | Types / Config / Repo / Service / Runtime / UI; Providers; Utils | User / System interface / Information / Operational |
| Lives in | A single product's codebase | Every change in any product, including non-code traces |
| Owned by | The product's architect | The methodology — applies regardless of stack |
| Failure mode it prevents | Cyclic dependencies, cross-layer leaks, inverted import direction | "Code is done but docs / consumers / contracts / alerts are not" |
| Survives stack swap | No — layer names are stack-flavoured | Yes — perception axes are stack-neutral |

A layer rule like "Service must not import UI" is a **within-codebase static dependency invariant**. A surface rule like "every change identifies which surfaces it touches and collects evidence per surface" is an **across-change verification invariant**. They do not address the same problem.

### Why agent-protocol does not promote layered architecture to normative

Three reasons, drawn directly from existing rules:

1. **Stack-flavoured names violate `principles.md` Principle 9 + `CLAUDE.md §2`.** The labels `Service`, `Repo`, `Provider`, `Runtime` are JS/TS/Node-flavoured; the same concepts go by different names in JVM, Rust, Go, Python, embedded, ML, and data-pipeline stacks. Promoting them into normative content would bind the methodology to one ecosystem.
2. **Most change types in this repo's worked examples do not fit the layer template.** A data pipeline (`docs/examples/data-pipeline-example.md`), an OTA firmware rollout (`docs/examples/embedded-firmware-example.md`), an ML retrain (`docs/examples/ml-model-training-example.md`), and a live-ops gacha event (`docs/examples/game-liveops-example.md`) each have rich operational and information surfaces, but their codebases do not split into a Service / Runtime / UI hierarchy. Surface-first analysis covers all four; layer-first forces them into a shape that does not exist.
3. **`principles.md` Principle 2 is derived, not preferred.** The Derivation section ("Cross-layer seams end up with no owner, which turns them into desync hotspots by default. End users, partners, and operators do not care about your layering — they perceive the system through their own surfaces.") names the failure mode that surface-first prevents. Replacing it with layer-first as the primary axis would re-introduce that failure mode without offsetting evidence.

### How the two coexist (in different layers of the system)

The layer model is **not wrong** — it is wrong as a *methodology-level* normative claim. It can legitimately live one level down:

| Level | Discipline | Mechanism |
|---|---|---|
| Methodology (this repo) | How a change is verified | Surface-first (mandatory) |
| Consumer-product architecture | How that product's code is organised | Free choice — layered, hexagonal, clean, port-and-adapter, etc. |

A consumer adopting agent-protocol may write `ARCHITECTURE.md` (per `docs/examples/consumer-docs-scaffolding.md`) declaring its own layered architecture. The methodology does not object — it only asks that *every change* go through the four-surface verification regardless of which architecture style the codebase uses internally. Layer rules become invariants the consumer's own custom lints enforce (per `docs/mechanical-enforcement-discipline.md`'s architecture-invariants axis), not invariants the methodology mandates.

### When a consumer's layer model "maps onto" surfaces

Common mappings consumers find useful when documenting in their `ARCHITECTURE.md`:

| Layer (e.g. of the Types→…→UI shape) | Surfaces typically touched |
|---|---|
| Types | Information surface (data shape, validation, enums) |
| Config | Information surface + Operational surface (feature flags, env wiring) |
| Repo | Information surface + System interface surface (data access boundary) |
| Service | System interface surface + Operational surface (business rules + side effects) |
| Runtime | Operational surface (startup, lifecycle, bootstrapping) |
| UI | User surface |
| Providers / Utils | Cross-cutting (any surface the consumer of the provider touches) |

The mapping is **descriptive, not prescriptive** — different consumer architectures map differently, and the four surfaces stay invariant across all of them. This is exactly why surfaces, not layers, are the methodology-level slice.

### Anti-patterns this section rejects

- *"We use a layered architecture so we don't need surface analysis."* The two are orthogonal; declaring one does not satisfy the other. A change that respects all layer rules can still ship with broken consumer contracts, missing migration evidence, or undisclosed operational impact.
- *"We do surface analysis so we don't need layer rules."* A consumer's codebase still benefits from layer rules to keep its internal structure clean. Surface analysis governs change discipline; layer rules govern code organisation. Both can hold.
- *Reading the layer model as a methodology recommendation from this repo.* The layer model is a popular consumer-side architecture pattern; it is documented here only to clarify the surface / layer distinction. The methodology's only normative claim about code organisation is "decisions live in the consumer's `ARCHITECTURE.md`, governed by mechanical-enforcement-discipline." See `docs/examples/consumer-docs-scaffolding.md`.

---

## See also

- `docs/source-of-truth-patterns.md` — where the authoritative version of each informational asset lives
- `docs/cross-cutting-concerns.md` — the six concerns applied per-surface
- `docs/breaking-change-framework.md` — consumer classification and severity matrix
- `docs/rollback-asymmetry.md` — per-surface rollback modes
- `docs/bridges/` — stack-specific surface mappings
