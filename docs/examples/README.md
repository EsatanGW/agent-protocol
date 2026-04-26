# `docs/examples/` — Worked Examples Index

Each file walks one realistic change through the methodology. Use this index to pick the example closest to your current change before reading more than one. Examples are non-normative — they illustrate how the canonical rules in [`../`](../) apply to a concrete situation.

> **Routing aid.** If you only read one, start with [`worked-example.md`](worked-example.md) (admin batch-resend invoices) — it touches the four core surfaces without a stack-specific bridge layer.

---

## By scenario type (read first if pattern matters more than stack)

| Example | Scenario |
|---------|----------|
| [`worked-example.md`](worked-example.md) | Generic feature: batch-resend invoices in an admin console. Four surfaces, no stack-specific bridge. |
| [`bugfix-example.md`](bugfix-example.md) | Bug fix that "looks like a UI problem but is actually a contract + state alignment problem". |
| [`refactor-example.md`](refactor-example.md) | Contract-alignment refactor: align order-status names across consumers. |
| [`migration-rollout-example.md`](migration-rollout-example.md) | Schema migration with backfill, dual-read, and rollout staging. |
| [`mobile-offline-feature-example.md`](mobile-offline-feature-example.md) | Offline-capable expense entry — sync conflict, partial connectivity, queue replay. |

## By domain (read first if domain dynamics matter most)

| Example | Domain |
|---------|--------|
| [`game-dev-example.md`](game-dev-example.md) | Virtual-currency purchase flow in an in-game shop. |
| [`game-liveops-example.md`](game-liveops-example.md) | Live-ops "Seven-Day Daily-Check-in Gacha" — virtual-asset irreversibility, asset/config/binary split. |
| [`ml-model-training-example.md`](ml-model-training-example.md) | ML retrain / rollout with dataset + weights + config SoT. |
| [`data-pipeline-example.md`](data-pipeline-example.md) | Schema extension with warehouse / feature store / compliance consumers. |
| [`embedded-firmware-example.md`](embedded-firmware-example.md) | OTA across HW versions, long-tail offline devices, three-mode rollback coexistence. |

## By stack (read first if you need stack-specific surface mapping)

Each row pairs the example with the canonical stack bridge it fleshes out (under [`../bridges/`](../bridges/)).

| Example | Stack bridge |
|---------|---------------|
| [`flutter-app-example.md`](flutter-app-example.md) | [`flutter-stack-bridge.md`](../bridges/flutter-stack-bridge.md) — multi-platform "Save & Share" with platform-channel two-sided contract. |
| [`android-kotlin-example.md`](android-kotlin-example.md) | [`android-kotlin-stack-bridge.md`](../bridges/android-kotlin-stack-bridge.md) — offline draft-saving with Room migration + WorkManager + ViewBinding. |
| [`ios-swift-app-example.md`](ios-swift-app-example.md) | [`ios-swift-stack-bridge.md`](../bridges/ios-swift-stack-bridge.md) — CloudKit-synced tag feature + Widget, private/public CloudKit rollback asymmetry. |
| [`react-nextjs-app-example.md`](react-nextjs-app-example.md) | [`react-nextjs-stack-bridge.md`](../bridges/react-nextjs-stack-bridge.md) — App Router migration with Server Action, ISR cache tags, Prisma additive migration. |
| [`ktor-server-example.md`](ktor-server-example.md) | [`ktor-stack-bridge.md`](../bridges/ktor-stack-bridge.md) — order-lifecycle enum addition with migration + plugin install order + mixed rollback modes. |
| [`unity-game-example.md`](unity-game-example.md) | [`unity-stack-bridge.md`](../bridges/unity-stack-bridge.md) — save-data format migration for a new progression system. |

---

## Worked-example manifests (machine-readable counterparts)

The narrative examples above are paired with structured `change-manifest.example-*.yaml` files under [`../../skills/engineering-workflow/templates/manifests/`](../../skills/engineering-workflow/templates/manifests/) — useful when the question is "what does the manifest look like for this kind of change?":

- `change-manifest.example-crud.yaml` — simple CRUD
- `change-manifest.example-mobile-offline.yaml` — offline-first mobile
- `change-manifest.example-game-gacha.yaml` — live-ops game
- `change-manifest.example-multi-agent-handoff.yaml` — Planner → Implementer → Reviewer progression of one manifest
- `change-manifest.example-security-sensitive.yaml` — JWT signing-key rotation (SoT pattern 8, L1 breaking change, mode-3 compensation-only rollback)
- `change-manifest.example-mission-evaluator.yaml` — mission-shaped manifest for an evaluator role

---

## How to extend this index

When adding a new `*-example.md` to this directory:

1. Pick its primary axis (scenario / domain / stack) and add a row in the matching table.
2. Keep the one-line description aligned with the existing tables' style.
3. If the example fleshes out a stack bridge, link the bridge in the same row.
4. If it primarily illustrates a manifest pattern, also add a row under "Worked-example manifests" (or, for narrative-only examples, omit that section).

Renaming an example is a breaking change for cross-references (see [`../change-manifest-spec.md`](../change-manifest-spec.md) and the file-naming rule in [`../../CONTRIBUTING.md`](../../CONTRIBUTING.md)) — update this index in the same change.
