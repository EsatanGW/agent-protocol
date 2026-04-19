# Worked Example: Add a Virtual-Currency Purchase Flow to the In-Game Shop

> This example demonstrates applying the composable-surface system to a game-development change.
> Beyond the four core surfaces, it also uses the asset surface, the experience surface, and the performance-budget surface.

---

## Requirement

Add a "buy gold with gems" feature to the in-game shop of a mobile RPG.

The player selects a gold pack on the shop page, taps Purchase, gems are deducted and gold is added,
and a success animation + sound effect plays.

---

## Phase 0 — Clarify

### Surfaces used on this project

Core surfaces (mandatory):
- [x] User surface
- [x] System-interface surface
- [x] Information surface
- [x] Operational surface

Extension surfaces:
- [x] Asset surface — UI sprite, animation, sound effect.
- [x] Experience surface — purchase feedback animation, button feel.
- [x] Performance-budget surface — draw calls and memory on the shop page.

### Affected surfaces

| Surface | Items affected |
|---------|----------------|
| User | Shop UI adds a gold-pack section, purchase button, balance display. |
| System-interface | Calls the server API to deduct gems / add gold and validate the transaction. |
| Information | Pack definitions (ScriptableObject), local cached balance, server balance. |
| Operational | Purchase-event analytics, transaction-failure logs, server-side audit. |
| Asset | Gold icon sprite, purchase-success particle-effect prefab, sound-effect clip. |
| Experience | Button press-and-release animation, gold-fly-in animation on success, sound timing. |
| Performance-budget | The shop page adds a new ScrollView section, plus draw calls for particle effects. |

### Public behavior impact
- Yes: users will see the new shop section and can make purchases.
- Acceptance criteria and evidence are not optional.

### Source of truth
- Pack definitions: server config (pushed to the client).
- Gem / gold balance: **the server** is the truth, the client is a consumer (anti-cheat).
- UI assets: the Figma design is the truth, the Unity prefab is the consumer.

---

## Phase 1 — Investigate

### Source-of-truth map

| Information | SoT | Consumers | Sync mechanism | Desync risk |
|-------------|-----|-----------|----------------|-------------|
| Pack list | Server config API | Client ScriptableObject cache | Fetched at startup | Low — refreshed every app launch |
| Gem balance | Server DB | Client UI | API response | Medium — can lag briefly during a purchase |
| Gold balance | Server DB | Client UI | API response | Same as above |
| Purchase success state | Server API response | Client animation trigger | Synchronous callback | High — network latency directly hits player experience |

### Risks identified
1. If the purchase API times out, the client doesn't know whether the transaction succeeded → needs an idempotent design.
2. Particle effects may drop frames on low-end devices → need a tiering strategy.

---

## Phase 2 — Plan

### Change plan (in dependency order)

1. **Information surface:** create the pack ScriptableObject + the matching server endpoint.
2. **Asset surface:** produce UI sprites, particle-effect prefabs, and sound clips → import after art team hands off.
3. **System-interface surface:** implement the purchase API call (with an idempotency token).
4. **User surface:** add the gold-pack section to the shop UI.
5. **Experience surface:** purchase-success animation (gold fly-in + particles + sound).
6. **Performance-budget surface:** profile the shop page and confirm draw-call budget.
7. **Operational surface:** analytics events, transaction logs.

### Cross-cutting
- Security: the purchase API must be validated server-side; the client cannot be trusted.
- Performance: particle effects need LOD — on low-end devices, downgrade to a simple scale animation.

---

## Phase 3 — Test Plan

| Verification item | Surface | Method | Evidence |
|-------------------|---------|--------|----------|
| Packs render correctly | User + Information | Screenshot | Shop-page screenshot |
| Purchase deducts gems / adds gold | System-interface + Information | API log + UI comparison | Before / after balance screenshots + server log |
| Purchase blocked on insufficient balance | User + System-interface | Manual test | Greyed-button screenshot + API rejection log |
| Purchase animation runs smoothly | Experience + Performance-budget | 60fps recording + Profiler | Recording + profiler screenshot |
| Particle-effect draw calls | Performance-budget | Unity Profiler | Draw-call before / after comparison |
| Low-end device fallback | Experience + Performance-budget | On-device low-end test | Low-end-device recording |
| Purchase-event instrumentation | Operational | Analytics dashboard | Event-fired screenshot |
| Timeout / failure handling | System-interface + User | Simulated network loss | Error-prompt screenshot + retry log |

---

## Phases 4–7: implement → deliver

(Same as the standard flow; details elided. The point of this example is the surface-mapping mindset.)

### Key lessons

1. **The asset surface is an independent dependency chain** — UI sprites and particle effects are delivered by the art team with their own review and approval process; do not assume they land in sync with code.
2. **The experience surface needs subjective verification** — "does the animation feel right" can't be judged by automated tests; playtest recordings are the evidence.
3. **The performance-budget surface is a gate** — if draw calls exceed budget, the feature cannot ship even if the logic is correct.

---

## What the composable-surface system is worth here

If you only had the four core surfaces:
- Asset management would be crammed into "information," but a sprite is not a schema.
- Animation feel would be crammed into "user," but a playtest is not form validation.
- Draw-call budget would be crammed into "operational," but performance is a functional requirement, not ops.

Extension surfaces give every concern its own source of truth, its own consumers, and its own verification method,
instead of being shoehorned into a core surface and then quietly ignored.
