# Project-local bridge deviations — template

> **Scope.** This document is the canonical template for project-local
> *overlays* on top of an upstream bridge in `docs/bridges/`. Consumer
> projects copy this file into their own repo as
> `docs/bridges-local-deviations.md`, fill in the sections, and keep it
> under version control alongside their code.
>
> **Why it exists.** Some methodology overlays are genuinely
> project-local — small audience, niche stack, or a variant that sits
> on top of a mainstream bridge. Upstreaming every such overlay would
> bloat `docs/bridges/` and force cross-cutting updates across the
> `README.md` bridge index, `AGENTS.md`, onboarding, and the
> stack-bridge template. A project-local file keeps the methodology's
> mainstream surface tight while still giving teams a structured place
> to document their deviations.
>
> **When to upstream instead.** If the same overlay is being written
> independently by multiple unrelated adopters, that is the signal to
> promote it to an upstream bridge. Until then: stay local.

---

## Parent bridge

> State which upstream bridge(s) this overlay attaches to, and the
> version tag of the upstream repo at the time of writing.

Example:

- Parent bridge: [`docs/bridges/flutter-stack-bridge.md`](https://github.com/example/agent-protocol/blob/v1.4.0/docs/bridges/flutter-stack-bridge.md)
- Upstream version: `v1.4.0`
- Review cadence: on every upstream version bump; minimum quarterly.

---

## Overlay name + purpose

> One short sentence describing the overlay. A paragraph of context.

```
Overlay: <name>
Purpose: <one sentence>
Applies when: <enumerated conditions>
```

---

## Surface mapping

> Every overlay **must** answer: does it introduce new surfaces, or
> does it reuse the parent bridge's canonical four (user /
> system_interface / information / operational) + the parent bridge's
> stack extensions? If it introduces new surfaces, list them with
> glob patterns against the parent project's file tree — the same
> shape as
> [`docs/bridges/<stack>-surface-map.yaml`](./bridges/).

---

## SoT mapping

> For each new SoT this overlay introduces (or each SoT in the parent
> bridge whose semantics this overlay alters): the one-line SoT
> pattern ID, the source, and the consumers it reaches.

---

## Rollback mapping

> State the overlay's rollback mode (1 / 2 / 3). If different surfaces
> within the overlay have different modes, spell that out — that is a
> rollback-asymmetry signal the parent bridge may or may not already
> flag.

---

## Drift signals

> What specifically counts as drift in this overlay? List the
> project-local checks a reviewer or hook should run on a change that
> touches this overlay.

---

## Anti-patterns

> What should reviewers actively refuse even when it looks correct?
> Overlay-specific mistakes that do not exist in the parent bridge.

---

## Example stubs for common residual items

> Starting points for the overlays most commonly requested but
> deliberately not upstreamed. Delete the ones you do not need; fill
> in the ones you do.

### Flame (Flutter game engine)

- Parent bridge: Flutter.
- Introduces: `experience_surface` (see `docs/surfaces.md` — game
  experience extension) because Flame widgets drive timed feedback
  loops, not declarative UI.
- Asset-surface applies (sprite sheets, audio, animation JSON).
- Drift signals: shader-variant count, `FlameGame` lifecycle
  `onMount` / `onRemove` pair mismatches, `PositionComponent` versus
  `HasGameRef` misuse.
- Anti-pattern: using Flutter widget tree for per-frame logic — the
  parent bridge allows it only for UI surfaces; Flame overlay forbids
  it for game-loop code.

### Unity UaaL (Unity as a Library)

- Parent bridge: Unity + whichever host stack (Flutter, Android
  Kotlin, Android Compose, Ktor, or iOS Swift).
- SoT split: Unity project is one SoT, host project is another; the
  **generated C# plugin surface** is the dual-representation contract
  between them and is not itself an SoT.
- Rollback asymmetry: host app rollback is mode 1 or 2 depending on
  platform; Unity payload rollback is mode 2 when packaged as a
  binary, mode 3 when delivered over the air.
- Drift signals: Unity player version ↔ host-side loader version
  mismatch; IL2CPP build flag drift between CI and local.

### KMM-iOS depth

- Parent bridge: Android Kotlin. The upstream Android bridge already
  sketches KMM at module-boundary granularity; this overlay covers
  iOS-side consumer patterns.
- Introduces: per-target expect/actual drift signal specific to
  iOS-side Swift consumers of shared Kotlin code.
- Anti-pattern: leaking Kotlin-specific exceptions across the Swift
  bridge; Swift consumers see them as `NSError`, losing the SoT
  behavior.

### Visual Scripting

- Parent bridges: Unity Visual Scripting, Unreal Blueprints, any
  graph-based authoring runtime.
- Introduces: `graph_surface` as a parallel representation of logic
  normally held on `information_surface`. SoT split: code-first vs
  graph-first is a per-project decision the overlay must state
  explicitly.
- Drift signals: nodes that call APIs no longer present in the bound
  code surface.

### Event-sourcing

- Parent bridges: Ktor (typical), any service bridge.
- Introduces: `events_surface` as the append-only SoT. Read models are
  consumers, not SoTs. Snapshots are caches, not SoTs.
- Rollback mode: strictly 3 for any change that alters past event
  semantics; 2 for changes that only add new event types.
- Anti-pattern: editing historical events in place — violates the
  immutability invariant that makes event-sourcing correct.

### Vendor-specific APM exporter

- Parent bridges: Ktor, Android Kotlin, Android Compose, Flutter.
- Introduces: `monitoring_channel` strings that map to specific
  vendor dashboards (Datadog, New Relic, Grafana Cloud, etc.).
- Drift signals: channel referenced in manifest but not registered
  with the exporter's config.
- Upstream neutrality: the vendor-specific piece **must** stay in this
  local overlay; the parent bridge only names the category
  `monitoring-channel`, never a vendor.

### iOS Swift sibling bridge

- Parent bridges: none (it is a sibling, not a child). Expect future
  upstream work.
- Introduces: full surface taxonomy for a UIKit / SwiftUI app,
  system-integration glue (widgets, App Intents, Live Activities),
  and store-binary rollback asymmetry similar to Flutter iOS.
- Flag this overlay as "promotion candidate" — if a second adopter
  writes a compatible overlay, upstream becomes the right call.

---

## Review + retirement

> How this overlay gets retired: state the conditions under which the
> overlay is superseded by an upstream bridge (if any), and the
> process for removing it cleanly.

---

## See also

- [`bridges-local-deviations-howto.md`](./bridges-local-deviations-howto.md)
  — walk-through showing a Flame overlay being authored end-to-end.
- [`stack-bridge-template.md`](./stack-bridge-template.md) — the
  template for upstream bridges. Reuse whatever fits; ignore the
  upstream-only obligations (ROADMAP entry, cross-cutting-term sweep,
  methodology-doc index updates).
- Parent bridges: [`bridges/`](./bridges/).
