# Authoring a project-local bridge deviation — end-to-end walk-through

> **Audience.** Engineering teams that consume an upstream bridge from
> `docs/bridges/` but need to document a niche overlay on top of it
> that is **not** a candidate for upstreaming. This page walks through
> the full authoring path for one such overlay — a Flame (Flutter game
> engine) overlay on top of the Flutter bridge — so the pattern is
> concrete and copyable.
>
> **Template.** See [`bridges-local-deviations-template.md`](./bridges-local-deviations-template.md)
> for the canonical section skeleton. This how-to fills it in.

---

## Scenario

A team ships a casual-puzzle game built with Flutter + Flame. The
Flutter bridge (`docs/bridges/flutter-stack-bridge.md`) covers the UI
shell, platform channels, state-management surfaces, and rollback
semantics for a typical Flutter app. It does **not** cover:

- the `FlameGame` lifecycle (`onLoad` / `onMount` / `onRemove`) as a
  Pattern 4a pipeline-order SoT,
- per-frame logic inside `update(double dt)` versus Flutter widget
  rebuilds — they have opposite correctness criteria,
- shader-variant count as an asset-surface drift signal,
- sprite-sheet + audio-bank versioning as a cross-representation
  concern between code (`Sprite.load('enemy.png')`) and assets
  (`pubspec.yaml:flutter.assets`).

None of that belongs in the upstream Flutter bridge: it is irrelevant
to 95 % of Flutter apps. It is exactly what a project-local overlay is
for.

---

## Step 1 — Create the overlay file in the consumer repo

In the consumer project (not this repo), create:

```
docs/bridges-local-deviations.md
```

Copy the section headings from
[`bridges-local-deviations-template.md`](./bridges-local-deviations-template.md).
Fill them in as shown below.

---

## Step 2 — Declare the parent bridge

```markdown
## Parent bridge

- Parent bridge: [`docs/bridges/flutter-stack-bridge.md`](https://github.com/esatangw/agent-protocol/blob/v1.3.0/docs/bridges/flutter-stack-bridge.md)
- Upstream version: `v1.3.0`
- Review cadence: on every upstream version bump; minimum quarterly.
```

Pin the upstream version tag. An overlay is only valid against the
bridge version it was written for; if you bump the upstream version,
re-review the overlay.

---

## Step 3 — Name the overlay and state when it applies

```markdown
## Overlay name + purpose

Overlay: flame
Purpose: extend the Flutter bridge to cover Flame game-engine surfaces
         and per-frame pipeline-order semantics that the widget-tree
         bridge does not address.
Applies when: a Flutter app imports the `flame:` package and runs a
         `FlameGame` subclass at any entry point.
```

The "Applies when" clause is the trigger a reviewer uses to decide
whether this overlay is in scope for a given change. Keep it
mechanically checkable (imports, declared base classes, config flags).

---

## Step 4 — Surface mapping

The Flutter bridge already defines the canonical four surfaces plus
asset / performance-budget extensions. This overlay reuses all of
them and introduces one new surface:

```markdown
## Surface mapping

Reused from the Flutter bridge:
- `user_surface` — widget tree under `lib/ui/**`.
- `system_interface_surface` — platform channels under
  `lib/platform/**`.
- `information_surface` — `lib/models/**`, `lib/data/**`.
- `operational_surface` — `pubspec.yaml`, CI config, build config.
- `asset_surface` (stack extension) — `assets/**`.

Added by this overlay:
- `experience_surface` — `lib/game/**/*.dart`. Any file that extends
  `FlameGame`, `Component`, `HasGameRef<T>`, or implements an
  `update(double dt)` / `render(Canvas c)` contract. Drives timed
  feedback loops, not declarative UI.
```

This matches the shape of
[`docs/bridges/<stack>-surface-map.yaml`](./bridges/) — when a
consumer-side validator (such as
`reference-implementations/validator-python/`) is pointed at this
overlay, it will treat `experience_surface` globs with the same
semantics as the canonical four.

---

## Step 5 — SoT mapping

```markdown
## SoT mapping

- Pattern 4a pipeline-order (new under this overlay):
  `FlameGame.onLoad` / `onMount` / `onRemove` sequence. Source:
  game entry-point file (`lib/game/<name>_game.dart`).
  Consumers: every `Component` that depends on the game having a
  fully-constructed world tree.
- Pattern 1 dual-representation (new under this overlay):
  sprite-sheet ↔ animation JSON. Source: `assets/sprites/*.json`.
  Mirrored into generated Dart code under `lib/generated/sprites.g.dart`.
  Consumers: anything that references a sprite ID.
- Pattern 3 enum (new under this overlay): game-state machine states
  (`Loading`, `Playing`, `Paused`, `GameOver`). Source: a single
  sealed class under `lib/game/game_state.dart`.
```

---

## Step 6 — Rollback mapping

```markdown
## Rollback mapping

- UI widget changes: mode 1 (code push via the hosting Flutter app's
  code-push provider — inherits the parent bridge's answer).
- `FlameGame` per-frame logic changes: mode 2. A broken `update(dt)`
  can corrupt per-save-file state; fix-forward with a new save-schema
  version, do not rewind players who have already played the bad
  build.
- Asset-only changes (sprite swap, audio re-master): mode 1 if the
  asset pipeline supports hot reload of assets; mode 2 if assets are
  AOT-compiled into the app binary.
- Save-data schema changes: mode 3 — old saves must stay readable
  indefinitely; you cannot roll back a schema migration that a player
  has already triggered.
```

The interesting deviation from the parent Flutter bridge is that this
overlay forces **mode 2 on per-frame game-loop code** even though the
parent bridge's UI-code rollback default is mode 1. That asymmetry is
the reason this overlay exists.

---

## Step 7 — Drift signals

```markdown
## Drift signals

- Shader variant count increased without a corresponding entry in the
  performance-budget SoT.
- `FlameGame.onMount` / `onRemove` pair mismatch — a subclass that
  overrides one but not the other is almost always a bug; reviewers
  must request justification.
- A `lib/game/**` file that imports `package:flutter/material.dart`
  for anything other than theming constants — widget tree inside
  game-loop code is the anti-pattern.
- Sprite ID referenced in code but not declared in
  `pubspec.yaml:flutter.assets` (or vice versa).
- Save-schema version bump without a migration test fixture under
  `test/game/migrations/`.
```

Each of these is a one-grep or one-AST-walk check; they are the
concrete things a reviewer or a hook actually runs. If you can not
reduce a drift signal to that, it is probably too vague to be
enforceable.

---

## Step 8 — Anti-patterns

```markdown
## Anti-patterns

- Using the Flutter widget tree for per-frame logic. The parent bridge
  allows widget rebuilds for UI surfaces; this overlay forbids them
  inside game-loop code because widget lifecycle and game-loop timing
  do not align.
- Treating `assets/sprites/*.json` as editable by gameplay engineers
  only. Art + code share the asset SoT; changes touch both sides.
- Rolling back a save-schema migration. Mode 3 is absolute under this
  overlay — any proposed rollback plan for a schema change must be
  rewritten as a forward-compensation plan before review can proceed.
```

---

## Step 9 — Review + retirement

```markdown
## Review + retirement

This overlay is retired when:
- a second unrelated adopter writes a compatible Flame overlay (the
  promotion-to-upstream condition), **or**
- the project stops shipping a `FlameGame`, **or**
- the parent Flutter bridge adds a first-class game-engine section
  that subsumes this overlay.

Removal process: delete this section from
`docs/bridges-local-deviations.md`, record the removal in the
consumer project's `CHANGELOG.md`, and run the drift-signal sweep one
last time to confirm nothing still relies on the retired rules.
```

---

## Step 10 — Wire the overlay into the consumer's review + automation path

Three concrete steps; all live in the consumer repo.

1. **Link it from the consumer's own `README.md`** under a "Methodology
   overlays" heading. Reviewers should hit this file within one click
   of the repo root.
2. **Point the validator at the overlay's surface map** if you run
   `reference-implementations/validator-python/`. Extend the existing
   `docs/bridges/flutter-surface-map.yaml` with an `experience_surface`
   entry via a local override file, or publish a
   `docs/bridges/flutter+flame-surface-map.yaml` under the consumer
   repo. Rule 3.2 then covers the new surface automatically.
3. **Write a minimal runtime hook** that enforces one or two of the
   drift signals (the `FlameGame.onMount` / `onRemove` pair check is a
   good first target because it is a single grep). Base it on
   `reference-implementations/hooks-claude-code/hooks/sot-drift-check.sh`
   — copy the category-C exit-code contract (`exit 2` advisory, never
   `exit 1` blocking) so the hook can not become a ship-stopper for
   unrelated work.

---

## What not to do

- **Do not copy the parent bridge into the overlay.** The overlay is
  a delta. If you find yourself restating a Flutter bridge rule, link
  to it instead.
- **Do not fork the parent bridge.** Forks drift; overlays compose.
- **Do not escalate an overlay rule to blocking severity during initial
  adoption.** Start advisory (`exit 2`), observe for one or two review
  cycles, then tighten to blocking only after the team has internalized
  the rule.
- **Do not promote an overlay to upstream before a second adopter
  exists.** Single-adopter content is project-local by definition;
  premature upstreaming bloats the mainstream bridges for everyone
  else.

---

## See also

- [`bridges-local-deviations-template.md`](./bridges-local-deviations-template.md) — canonical section skeleton.
- [`stack-bridge-template.md`](./stack-bridge-template.md) — template for upstream bridges; reuse the parts that fit.
- [`bridges/flutter-stack-bridge.md`](./bridges/flutter-stack-bridge.md) — the parent bridge this worked example attaches to.
- [`surfaces.md`](./surfaces.md) — canonical surface taxonomy including the `experience` extension.
- [`source-of-truth-patterns.md`](./source-of-truth-patterns.md) — the ten SoT patterns the overlay's SoT mapping draws from.
