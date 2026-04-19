# Worked Example: Game Live-Ops "Seven-Day Daily-Check-in Gacha"

> This example walks a game live-ops change through the full methodology:
> - Asset / config / binary split across independent tracks (rollback asymmetry).
> - Player virtual assets are irreversible (rollback mode 3).
> - Subjective verification on the experience surface (playtest).
> - Third-party platform dependencies (iOS / Android stores, push services).
>
> All names, paths, and data structures are fictitious.

---

## Requirement

A live card-collecting mobile game is launching a 7-day Lunar-New-Year event:
- Daily login grants one ticket.
- Collect enough tickets to pull from a limited-character gacha (includes an SSR).
- The event has a fixed start / end window.
- The contents (rewards, drop rates, visuals) change every year, but the event framework is reused.

---

## Phase 0 — Clarify

### Surfaces used on this project

Core surfaces:
- [x] User surface — event entry, login-reward popup, gacha UI, result animation.
- [x] System-interface — claim API, gacha API, player-reward inventory.
- [x] Information — event config (timing, rewards, drop rates), player-progress schema.
- [x] Operational — gacha audit log (compliance-mandated), drop-rate compliance proof, customer-support lookup tools.

Extension surfaces:
- [x] Asset — UI sprites, gacha animation, SSR character art, sound effects.
- [x] Experience — gacha anticipation, the payoff when an SSR appears, the consolation feel when nothing hits.
- [x] Performance-budget — animation draw calls, memory (players idle in the event screen for long periods).
- [x] Uncontrollable external dependencies — App Store policy (loot-box disclosure), push-token TTL, regional compliance (China / Korea / Japan mandatory drop-rate publication).

### Affected surfaces

| Surface | Items affected |
|---------|----------------|
| User | Event banner, login popup, gacha main UI, SSR reveal animation. |
| System-interface | `POST /event/checkin`, `POST /event/draw`, integration with existing inventory API. |
| Information | Server config (event window, reward pool, drop-rate table), `player_event_progress` schema. |
| Operational | Gacha audit log, drop-rate compliance dashboard, player-dispute lookup tool. |
| Asset | SSR character art, UI sprites, gacha animation prefab, voice / sound effects. |
| Experience | Tension before the pull, audiovisual payoff when an SSR drops, pity-feedback design. |
| Performance-budget | Draw-call peak during the animation, SSR art streaming, long-idle memory. |
| Uncontrollable external | iOS App Store "real-time random items" disclosure (post-14.0), regional drop-rate publication laws. |

### Source of truth — multi-pattern combination

| Information | SoT pattern | Notes |
|-------------|-------------|-------|
| Event config (timing, rewards, drop rates) | **Pattern 2 (Config-Defined Truth)** | Server-driven, hot-updatable. |
| Player progress | Pattern 1 (Schema-Defined) | Server DB. |
| Gacha result (already pulled) | **Pattern 6 (Transition-Defined)** | Once `drawn`, immutable. |
| Drop-rate compliance disclosure | Pattern 4 (Contract-Defined) | Facing players and regulators. |
| UI / animation / sound | Pattern 5 (UI-Defined Truth) | Figma + art prefabs. |

### Public behavior impact
- Yes: players directly see the event, receive rewards, and pull characters.
- Acceptance criteria and evidence are not optional.
- **Note:** drop-rate disclosure is a compliance requirement, not a nice-to-have.

### Open questions
- ⛔ Are the drop-rate disclosure copies complete for all regional versions? (CN / JP / KR mandate this.)
- ⛔ Pity mechanic: "SSR guaranteed within N pulls" — where is N defined, and is it identical across regions?
- ⚠️ What happens to unused tickets at event end?
- ⚠️ Is progress shipped in the main binary, or purely via server config?

---

## Phase 1 — Investigate

### Source-of-truth map

| Information | SoT | Consumers | Sync mechanism | Desync risk |
|-------------|-----|-----------|----------------|-------------|
| Event config | Server config service | Client (fetch at startup), server gacha logic, support tooling | Startup fetch + remote-config push | Medium — client caches may expire |
| Player progress | Server DB | Client UI, push service, customer support | API + push | Low |
| Gacha result | Server DB | Client animation trigger, audit log, support lookup | Synchronous API | **Must be zero desync** (compliance) |
| Drop-rate disclosure | Config + legal documents | Client disclosure page, official site, store description | Manual sync | High — this is a compliance risk |

### Uncontrollable external-dependency inventory

| Dependency | Risk | Mitigation |
|------------|------|------------|
| iOS App Store random-item disclosure | Non-compliance can delist the app | Legal reviews the disclosure copy + store description. |
| Regional drop-rate publication laws | Fines for non-compliance | Region-specific configs separated + legal-sign-off flow. |
| Push tokens | Seasonal expiration | Raise sync frequency + do not depend on push to trigger gacha. |
| Art asset delivery schedule | SSR art is a hard blocker | Task ordering in Phase 2 puts art first. |

### Irreversible side-effect inventory

- [x] Characters already pulled — fully irreversible (once given, they're given).
- [x] Tickets already spent — irreversible (a pull consumes a ticket).
- [x] Gacha records written to audit log — compliance-immutable.
- [x] Push notifications already sent — not recallable.
- [x] Client binaries already downloaded to player devices — mobile constraint.
- [x] App Store / Play Store descriptions — a compliance sync point.

---

## Phase 2 — Plan

### Asset / config / binary three-track strategy

Key design: **nothing in this event's variable surface is baked into the main binary.**

| Volatility | Content | Carrier | Rollback speed |
|------------|---------|---------|----------------|
| High | Event window, reward pool, drop rates, copy | Server config | Minutes |
| Medium | UI sprites, character art, animation prefabs, sound | Asset bundle (CDN) | Hours |
| Low | Gacha logic framework, UI container, event tracking | Client binary | Days to weeks |

**Why this split:**
- Drop rates in the binary → rebalancing waits for store review.
- Character art in the binary → bloated build + can't add characters within a release.
- Event window in the binary → delaying the event becomes a disaster.

### Change map

| Surface | Main change |
|---------|-------------|
| User | Event entry, gacha UI, results screen, drop-rate disclosure page. |
| System-interface | Claim / gacha APIs with idempotency keys. |
| Information | Event V2 fields in server config schema, `player_event_progress` table. |
| Operational | Gacha audit log, compliance dashboard, support tooling. |
| Asset | Art delivers SSR character art, gacha animation prefab, SSR reveal sound. |
| Experience | Pacing design (build-up, sudden SSR reveal, consolation for misses). |
| Performance-budget | Animation must meet frame budget (30fps / 60fps modes). |

### State machine (player progress, Transition-Defined)

```
   ┌──────────────────┐
   │ event_eligible   │  ← event started and player qualifies
   └────────┬─────────┘
            ▼
   ┌──────────────────┐
   │  daily_checkin   │  ← daily ticket claim (up to 7)
   └────────┬─────────┘
            ▼
   ┌──────────────────┐         ┌──────────────────┐
   │ has_draw_tickets │────────▶│      drawn       │
   └──────────────────┘         └──────────────────┘
                                         │
                                         ▼
                               ┌──────────────────┐
                               │  reward_granted  │
                               └──────────────────┘
```

**Forbidden transitions:**
- Any state → `drawn` without passing through `has_draw_tickets` (free-ride exploit).
- `drawn` → `reward_granted` breaking in the middle (player pulled but didn't receive the character).

### Breaking-change assessment

| Change | Level | Path |
|--------|-------|------|
| Add event config V2 schema | L0 (additive) | Merge directly; old clients are unaffected. |
| Add idempotency key to gacha API | L1 (behavioral) | Gray rollout. |
| Add SSR character to the pool | L0 (additive) | Server push is sufficient. |
| Modify the existing pity logic | L4 (semantic reversal) | **Forbidden** — use a new name + new endpoint and keep the old logic intact. |

### Rollback plan (per `rollback-asymmetry.md`)

**Primary mode: mode 3 (compensation rollback).**

Reasons:
- Characters players already pulled are irreversible → mode 1 is out.
- The main binary cannot be force-downgraded → mode 1 is out.
- But most volatile parts can be hot-updated via config / assets → mode 2 is the main tool.
- A compensation flow is mandatory for serious incidents → mode 3 is the backstop.

**Forward-fix path (preferred):**
- Server config can change drop rates, copy, and the event window in real time.
- Asset bundles can be swapped via a new CDN manifest.
- The server can reject requests from binaries below version X.

**Compensation path (backstop):**
- Drop-rate misconfig causes over-issuance of SSRs → do not claw back; publish a notice + apologize/compensate all players.
- Drop-rate misconfig causes too few SSRs → grant compensation tickets to all affected players.
- Gacha result fails to write (ticket consumed but no character granted) → per-case support handling + reconciliation script.

**Containment:**
- Staged rollout: 5% of players first, observe 1 hour, then 25%, then 100%.
- Kill switch: one-tap disable of the gacha entry (ticket claims continue).
- Monitoring: gacha API success rate, SSR drop rate (vs published), ticket-consumed-but-no-reward anomaly rate.

### Cross-cutting impact

| Dimension | Focus |
|-----------|-------|
| Security | Gacha results decided server-side, client untrusted; audit log tamper-resistant. |
| Performance | No frame drops during animation, SSR art streamed, event entry doesn't hurt home-screen FPS. |
| Observability | Every pull carries a trace ID, real-time drop-rate distribution dashboard, disputes are resolvable in seconds. |
| Testability | Drop-rate tests (100k simulated pulls verifying distribution), UI tests for every result animation. |
| **Error handling** | Classify gacha failures (network / balance / server bug / risk control), player-understandable error messages, reconciliation for "ticket consumed, no character granted." |

### Experience-surface discipline

Experience cannot be judged by automated tests — a playtest flow is required:

- Art + design + QA jointly review the prefab.
- At least 5 testers play 10 gacha sequences each and record their subjective reactions.
- "Payoff" rating when an SSR appears (1-5).
- "Frustration" rating on misses (lower is better).
- Pacing (too long → boring? too short → no anticipation?).

### Tasks (in dependency order)

1. Legal reviews the drop-rate disclosure copy + regional config structures.
2. Art delivers SSR character art, gacha animation prefab, and sound.
3. Server config schema design + push mechanism.
4. Server gacha logic (with idempotency + audit log).
5. Client UI framework (event entry, ticket claim, gacha UI).
6. Client animation / sound integration (asset surface).
7. Experience playtest + tuning.
8. Performance profiling and optimization.
9. Support tooling, monitoring dashboard, kill switch.
10. Staged rollout plan.

---

## Phase 3 — Test Plan

| TC# | Surface | Test case | Evidence |
|-----|---------|-----------|----------|
| TC-01 | Information + System-interface | 100k simulated pulls, SSR rate matches the published rate (error < 0.1%) | Statistics report |
| TC-02 | System-interface | Gacha API idempotency: repeated calls with the same key consume one ticket and grant one character | Integration test |
| TC-03 | User | All result types (common / high / SSR) render correctly | Screenshot matrix |
| TC-04 | Experience | Playtest: subjective-rating targets hit across 5 testers | Rating sheet + recording |
| TC-05 | Performance-budget | Animation holds 60fps on high-end / 30fps on low-end | Profiler screenshots |
| TC-06 | Asset | SSR art renders correctly at all resolutions with no visual glitches | Screenshots |
| TC-07 | Operational | Audit log records every pull in full (trace ID, player ID, result, timestamp) | Log samples |
| TC-08 | Cross-cutting (compliance) | Drop-rate disclosure page renders correctly in every regional build | Screenshot matrix |
| TC-09 | Cross-cutting (error handling) | Every failure scenario produces a player-understandable message + a support-diagnosable trace | Screenshots + logs |
| TC-10 | Cross-cutting (rollback) | Kill switch disables the gacha entry immediately; config hot-update takes effect | Operation evidence |
| TC-11 | State machine | Illegal transitions (pull without a ticket, double-pull) are rejected | Unit test |
| TC-12 | Regression | Existing gacha events are unaffected | End-to-end suite |

---

## Phase 4 — Implement

Build in task order. Key rules:
- Drop-rate logic lives on the server only; the client receives the result and plays the animation.
- Audit-log write failure = gacha failure (don't let a pull succeed with a missing log entry).
- Asset bundles decouple from the binary; the binary does not assume specific assets exist.

---

## Phase 5 — Review

**Review focus:**

- [ ] Drop-rate disclosure copy is legally signed off (sign-off record attached).
- [ ] State-machine guards are enforced on the server (not just client UI).
- [ ] Audit-log write is atomic with the gacha result (same transaction).
- [ ] Kill switch has been drilled; support SOP is written.
- [ ] Experience playtest passed (ratings attached).
- [ ] Regional configs match the published disclosure (cross-check).
- [ ] Both the forward-fix and the compensation path have owners who can execute them.

---

## Phase 6 — Sign-off

- All test cases pass.
- Legal sign-off complete.
- Art / design / QA three-party review passed.
- On-call has drilled the kill switch.
- Support team onboarding complete.

---

## Phase 7 — Deliver

- Staged rollout: 5% → 25% → 100%.
- Monitoring dashboard watched live.
- Announcements / push notifications sent.
- Support team on standby.

---

## Phase 8 — Post-delivery observation

| Time | Focus |
|------|-------|
| T+1h | Gacha success rate ≥ 99.9%, SSR rate matches disclosure, no crash spike. |
| T+24h | Player-dispute volume, support-ticket categorization, community sentiment (external surface). |
| T+72h | Event participation rate, ARPU change, cumulative SSR distribution converges toward the published rate. |
| T+7d | Post-event compensation flow (unused tickets), feedback calibrates next event's design. |

**Feedback goals:**
- Calibrate the event-framework reusability (can next year's Lunar New Year reuse this directly?).
- Collect playtest conclusions vs actual player reaction — measure the gap.
- Evaluate the real TTM of the forward-fix path.

---

## What this example demonstrates

1. **The three-track strategy (binary / asset / config) is the core design for game live-ops** — rollback asymmetry forces volatility down to the lower layers.
2. **The irreversible side-effect inventory is usually long** — player virtual assets, spent tickets, audit logs, push notifications — each is irreversible.
3. **The experience surface needs an independent verification flow** — a playtest cannot be replaced by a unit test.
4. **Uncontrollable external dependencies are a compliance life-or-death line** — store policy and regional law are not nice-to-have; violations mean delisting.
5. **Compensation rollback is the backstop, not the first choice** — maximize forward-fix capability via config / asset hot-updates, but the compensation flow must be prepared in advance.
6. **Cross-surface SoT combinations** — patterns 2 (config) + 6 (transition) + 4 (contract) + 5 (UI) operate simultaneously.
