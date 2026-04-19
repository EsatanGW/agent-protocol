# Worked Example: Save-data format migration for a new progression system in a Unity game

> The in-methodology examples `game-dev-example.md` (in-game shop) and `game-liveops-example.md` (limited-time event) cover gameplay and live-ops in Unity.
> This example covers the **third Unity-specific load-bearing scenario** that the Unity bridge calls out but neither existing example exercises:
>
> - **Save-data schema versioning** (SoT pattern 1 + forward-only migration chain).
> - **Editor-asset ↔ runtime-object dual representation** (SoT pattern 8 — the canonical Unity case).
> - **IL2CPP / AOT build-time risk** (reflection-dependent code silently stripped unless declared in `link.xml`).
> - **Shipped-binary mode-2 rollback while Addressables + server config stay mode-1** — Unity's three-track rollback asymmetry.
>
> All names, paths, and data structures are fictitious.

---

## Requirement

The game currently stores player progress in a single monolithic JSON save file with no version stamp. Product asks:

> "Add a new 'Mastery Track' progression system alongside the existing character-level system. Existing players' saves must load; new saves carry both systems; missing fields default to the Mastery Track at level 0."

Constraints:

- Save-data format must be version-stamped going forward (it currently is not — this is the compounding tech-debt moment).
- Old saves from any shipped version in the last 18 months must load cleanly.
- Mastery Track definitions live in ScriptableObject assets; runtime state lives in the save.
- Target platforms: iOS, Android, Steam PC (so IL2CPP is in play on iOS + Android; Mono on PC).

---

## Phase 0 — Clarify

### Surfaces used on this project

Core surfaces:
- [x] User — new Mastery Track tab in the character screen, progress bars, reward popup.
- [x] System-interface — save / load path; optional cloud-save adapter (out of scope for this ticket — tracked as a follow-up).
- [x] Information — new save schema v2 (version stamp, Mastery Track block), migration chain v1 → v2.
- [x] Operational — analytics events `mastery_leveled`, `save_migrated`; crash breadcrumb around migration step.

Extension surfaces (Unity-specific):
- [x] Asset — Mastery Track definitions as ScriptableObject (`MasteryTrackDefinitionSO`), reward icons, new tab UI prefab.
- [x] Experience — level-up VFX / SFX feedback.
- [x] Performance-budget — character screen draw-call budget must not regress.

### Affected surfaces

| Surface | Items affected |
|---------|----------------|
| User | Character screen gains a Mastery Track tab and level-up popup. |
| System-interface | Save/load path gains a version-read step and migration dispatcher. |
| Information | Save schema v2 (version field, `mastery_tracks: []`), migration functions `Migrate_V1_to_V2`. |
| Operational | Two new analytics events; migration observability; Crashlytics tag `save_version`. |
| Asset | One new ScriptableObject asset type + concrete assets per track; one new prefab. |
| Experience | Level-up VFX; needs playtest sign-off. |
| Performance-budget | Character screen draw calls must stay ≤ current budget (measured on low-end target device). |

### Change boundaries

- Do **not** change the character-level system.
- Do **not** silently drop unknown fields on load — log them and surface in support tooling.
- Do **not** introduce reflection-based save parsing — explicit serialization only (IL2CPP-safe).

### Public behavior impact

YES — users see a new feature and their save files are rewritten on first load post-update.

---

## Phase 1 — Investigate

### Source-of-truth map

| Information | SoT | Consumers | Sync mechanism | Desync risk |
|---|---|---|---|---|
| Mastery Track definitions | `MasteryTrackDefinitionSO` assets | Runtime systems, UI, analytics schema | Loaded on game boot | Low — SOs are cached at boot |
| Save schema | The `SaveDataV2` C# class + version constant | Serializer, migration functions, support tooling | `SaveSchemaVersion.CURRENT` constant | **High** — the C# class and the on-disk JSON must agree; an accidental `[SerializeField]` on a new field without a migration produces truncated saves |
| Player runtime state | `SaveDataV2` runtime instance | Every gameplay system | Single repository `SaveService` | Medium — bypass risk if a system writes directly |
| IL2CPP reflection surface | `link.xml` | IL2CPP build toolchain | Manual edits | **High** — adding a reflection call without a `<preserve>` entry strips the call target silently in release |

### Risks identified

1. **Unversioned legacy saves.** Current saves have no version stamp. The load path must detect "no version field present = v1" and migrate implicitly; this rule must survive the next schema change.
2. **IL2CPP stripping of new serializer paths.** If the save serializer uses `Newtonsoft.Json`'s `[JsonConstructor]` or equivalent reflection, IL2CPP may strip the constructor; release builds on iOS / Android silently produce null fields.
3. **Asset import drift.** Adding a new `MasteryTrackDefinitionSO` asset in one branch while another branch renames the class → GUIDs mismatch → asset breaks silently.
4. **Shipped binary cannot downgrade.** Once a player opens the game on the new version, the save is rewritten to v2. A forward-fix binary must also read v2 (or re-migrate) — it cannot regress to "only read v1".
5. **Character screen draw calls.** The new tab with dynamic track rows may add 5–15 draw calls; on the low-end target device, that may push past the budget.

---

## Phase 2 — Plan

### Change plan (in dependency order)

1. **Information surface (schema + migration):**
   - Introduce `SaveSchemaVersion` constant; v1 = legacy (implicit: no version field present), v2 = current.
   - Define `SaveDataV2` with a `version` field and the Mastery Track block.
   - Write `Migrate_V1_to_V2(SaveDataV1 old) -> SaveDataV2 new` as a pure function, idempotent, with a unit test.
   - Update `SaveService.Load` to: read version → run migration chain up to `CURRENT` → return.
   - Update `SaveService.Save` to always write `CURRENT`.
2. **Information (asset):** define `MasteryTrackDefinitionSO` with `id`, `displayName`, `maxLevel`, `xpCurve`, `rewards`. Author three initial track assets.
3. **System-interface (serialization):** use explicit serializer (no reflection constructors); add each new type to the serializer's registered-types list if the serializer requires one.
4. **Build-time risk (IL2CPP):**
   - Add `link.xml` `<preserve>` entries for any new type referenced only via `GetType(string)` (prefer not to introduce any — the design calls for explicit serialization).
   - Add a CI job that runs one IL2CPP build per release branch (not just Mono editor tests).
5. **User surface:** add the Mastery Track tab prefab + UI Toolkit layout; screen reader / input binding pass.
6. **Experience surface:** add level-up VFX + SFX — playtest clip required.
7. **Performance-budget surface:** profile character screen on the low-end target device before and after; draw-call delta recorded in evidence.
8. **Operational surface:** register `mastery_leveled` and `save_migrated` in the event registry; add Crashlytics tag `save_version`; add a support-tool read path for dumping a save's version + track list.

### Cross-cutting

- **Rollback modes (three-track asymmetry):**
  - Server config / feature flag gating the UI entry = **mode 1**.
  - Addressables catalog for the new UI prefab + track definitions = **mode 1 or 2** (corrective remote catalog within hours if needed).
  - Shipped binary (App Store / Play Store / Steam) = **mode 2** (forward-fix only).
  - Save file already migrated to v2 on a player's device = **irreversible** (no mode-0 downgrade); must be treated as part of the shipped-binary contract.
- **Security:** player save tampering is in the threat model already; the migration must reject clearly invalid inputs without crashing.
- **Supply chain:** no new third-party packages — the serializer is existing.

---

## Phase 3 — Test Plan

| TC# | Surface | Test case | Evidence |
|---|---|---|---|
| TC-01 | Information | Legacy save from 18 months ago loads and migrates; all character-level fields preserved | Test output + save diff |
| TC-02 | Information | `Migrate_V1_to_V2` is idempotent (running twice yields same result) | Unit test |
| TC-03 | Information | Unknown-field save is logged, not dropped silently | Log capture |
| TC-04 | Asset | ScriptableObject asset meta-files intact after reimport; no duplicate GUIDs | `git diff` of `.meta` files + GUID scan |
| TC-05 | System-interface / build | IL2CPP release build on iOS + Android loads a v1 save correctly (no silent null) | Device log + screenshot |
| TC-06 | User | Mastery Track tab renders, progress bars animate, reward popup fires | Screen recording |
| TC-07 | Experience | Level-up VFX/SFX timing feels correct per playtest rubric | Playtest clip + observer report |
| TC-08 | Performance-budget | Character screen draw calls ≤ budget on low-end target device | Profiler capture before/after |
| TC-09 | Operational | `save_migrated` event fires exactly once per save per migration | Analytics debug view |
| TC-10 | Regression | Existing character-level XP / rewards unaffected | Existing smoke test |

---

## Phase 4 — Implement

Execute in plan order. Gates:

- After task 1, run the migration unit tests on a corpus of real player saves (legal-approved, anonymized) covering every shipped version of the past 18 months.
- After task 4, run one full IL2CPP build in CI; do not merge if the release build produces any null fields on v1 load.
- After task 7, measure draw calls on the actual low-end target device, not the editor.

---

## Phase 5 — Review

Review checks beyond "the tab works":

- Does the load path **always** route through the migration chain, or are there direct `File.ReadAllText` + `JsonUtility.FromJson<SaveDataV2>` calls that bypass version detection? Grep for `JsonUtility.FromJson<SaveData` — only one call site should remain.
- Does the migration function handle the "save has no version field" case the same way it would handle any future "save has version field < current" case? A bespoke legacy branch is a future-trap.
- Is there an IL2CPP build artifact in the evidence plan, not just editor/Mono test results?
- Are `link.xml` entries minimal (only what the runtime path actually needs), not blanket `preserve="all"`?
- Is the Addressables catalog corrective-patch plan documented (mode-1 / mode-2 track), separate from the binary mode-2 plan?
- Have low-end-device draw-call measurements been captured, not just editor-stat estimates?

---

## Phase 6 — Sign-off

- All TCs passed; TC-05 (IL2CPP) on physical iOS + Android devices; TC-07 (playtest) with a recorded observer report; TC-08 (performance) on the declared low-end target.
- `link.xml` diff reviewed — shrink-only or justified-add entries only.
- Uncontrolled-external register updated: the Unity editor version + IL2CPP toolchain version are pinned for the release.
- Rollback plan documented per track: server flag (mode 1), Addressables (mode 1/2), binary (mode 2), save-file (irreversible).

---

## Phase 7 — Deliver

Completion-report summary:

- Capability: Mastery Track progression added; save-data format v2 with forward-only migration chain is the foundation going forward.
- Surface coverage: four core + asset + experience + performance-budget.
- Verification: TC-01..10 passed with evidence; IL2CPP build ran on every release branch.
- Rollback plan per track: UI feature flag (mode 1), Addressables catalog (mode 1/2), shipped binary (mode 2), save-data on-disk (irreversible — forward-only).
- Observation window: 14 days post-rollout; watch `save_migrated` failure rate and Crashlytics with `save_version` tag.

Follow-ups (recorded):

- Cloud-save adapter (separate ticket).
- XP-curve tuning (game-design iteration, not a save-format concern).
- Migration chain test corpus automation (CI gate for future v3 migration).

---

## What this example is meant to show

1. **The Unity editor view of an asset, the on-disk YAML, the generated metadata, and the runtime object are four representations of one source of truth.** Any change to one must update the others; `.meta` GUID preservation is the glue.
2. **Save-data versioning is a compounding debt.** The first time you add a version field is the easiest; the tenth time you deserialize a field that disappeared in v7 is the hardest. Stamp versions now, write forward-only migration chains, and keep a real-save corpus for regression.
3. **IL2CPP and Mono are two different runtimes.** Editor / Mono tests passing is not evidence of IL2CPP correctness. At least one IL2CPP build per release branch, on physical target devices, is the floor.
4. **Unity ships with three rollback tracks simultaneously.** Server config (mode 1), Addressables catalog (mode 1 or 2), shipped binary (mode 2). A fourth "track" is the player's local save — once migrated, it is irreversible. A single "rollback mode" field on a Unity change is a category error.
