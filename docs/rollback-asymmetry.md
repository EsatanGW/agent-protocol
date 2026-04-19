# Rollback Asymmetry

> **English TL;DR**
> "Rollback" is not a uniform concept. Three modes coexist on any non-trivial change: **Mode 1 Reversible** (as if nothing happened — stateless server with blue/green, a feature flag off; seconds), **Mode 2 Forward-Fix** (cannot truly return to the past but can push a patch quickly — shipped binary, migrated DB schema; hours-to-days), **Mode 3 Compensation-Only** (unrecoverable side effect has already reached the world; payment sent, push delivered, on-chain transaction written — only compensation is possible). A single change can mix modes across surfaces (the code is mode 1 while the notification it sent is mode 3). Documents per-surface default modes, long-lived-client handling (mobile binaries, game clients, distributed agents; rollback takes days-to-weeks with a long tail of devices that never update), and the explicit irreversible-side-effect list that must be enumerated in every manifest's `rollback` block. Treating every change as "just roll back" is the canonical way to manufacture incidents.

> "Rollback" is not a uniform concept.
> The feasibility, speed, and cost of rollback vary enormously across stacks and surfaces.
> This document faces that asymmetry head-on and answers: **"When rollback is impossible, what does a rollback plan actually look like?"**

---

## Why this document exists

Many methodologies treat rollback as "press a button, return to the previous version." That assumption holds approximately for **server-side web** and breaks down in every scenario below:

| Environment | Real rollback difficulty |
|-------------|--------------------------|
| Web backend (single-tenant SaaS) | Seconds — switch blue/green |
| Web frontend | Minutes — CDN version swap |
| Mobile app (iOS App Store) | About a week, and older versions stay in use |
| Mobile app (Android Play Store) | Days; can be accelerated but cannot force-downgrade already-installed users |
| Desktop application (signed installer) | Cannot force-downgrade at all; only a new version can fix the bug |
| Shipped game binary | Same as mobile, with more severe version fragmentation |
| Game asset / hot fix | Minutes to hours (depends on patch system) |
| Schema migration (already backfilled) | Usually irreversible |
| Sent push notification / email | Cannot be recalled |
| Records written to a blockchain / immutable ledger | Fully irreversible |
| Real-world state already changed (payment captured, shipment sent, lock released) | Only compensation is possible — not rollback |

**Conclusion: rollback is a spectrum, not a button.**
The Phase 2 plan must place the change somewhere on that spectrum.

---

## The rollback spectrum

```
             Reversible ←──────────────────────────────────────────→ Irreversible

[blue/green]  [feature flag]  [config revert]  [CDN revert]
                                               │
[DB repair script]   [compensating txn]   [hotfix release]
                                               │
                                               ▼
                                      [mobile force-update]
                                               │
                                               ▼
                                      [asset hot patch]
                                               │
                                               ▼
                                      [already-sent push notification]
                                               │
                                               ▼
                                      [real-world action already executed]
```

Every arrow points in the direction in which rollback looks less like rollback and more like forward-fix or compensation.

---

## The three rollback modes

### Mode 1: Reversible rollback (rollback in the literal sense)

Return to the pre-change world **as if nothing had happened**.

**Preconditions:**

- The change does not touch persisted data (or can be fully restored).
- No consumer has already taken an irreversible action based on the new version.
- No outward-facing signal has been emitted.

**Typical examples:**

- Backend deploy under blue/green — switch back.
- Feature flag off.
- CDN rollback to the previous HTML / JS build.

**Checklist:**

- [ ] The change touches only stateless code (no schema change, no new data).
- [ ] After release, no data was written in a format only the new version can interpret.
- [ ] No third party was notified or has made decisions based on the new behavior.
- [ ] After rollback, the system immediately accepts arbitrary traffic.

### Mode 2: Forward-fix rollback (semantic rollback, not literal)

You cannot truly "go back in time," but you can quickly ship a fix that resolves the problem. From the user's perspective it looks like a rollback; from the system's perspective it is another deploy.

**Preconditions:**

- Schema migration has already run, new data has been written, consumers have been updated, **but** a patch can be released in a short window.

**Typical examples:**

- Schema migrated → new version adds a backward-compatible view.
- API contract changed → new version supports both old and new contracts.
- Mobile app bug → expedited review + minimum-supported-version enforcement.

**Checklist:**

- [ ] The hotfix code / process template is pre-prepared.
- [ ] The fix path does not depend on the broken version (avoid chicken-and-egg).
- [ ] A "minimum supported version" mechanism can block old clients from calling the API.
- [ ] On-call knows the forward-fix SLA (hours? days?).

### Mode 3: Compensation (not rollback)

The change has already caused irreversible effects. The only recourse is a compensating action inside the system.

**Preconditions:**

- Money has been charged, shipments have gone out, messages have been sent, external side effects have executed.
- "Pretending it didn't happen" would leave an inconsistency behind.

**Typical examples:**

- Overcharge → issue a refund transaction.
- Wrong coupon issued → case-by-case support intervention + future guardrails.
- Bug spammed push notifications → follow with an apology notification + in-app announcement.
- Incorrect on-chain transaction → post an offsetting transaction (the original still exists forever).

**Checklist:**

- [ ] Which side effects are irreversible has been enumerated.
- [ ] Every irreversible side effect has a corresponding compensation action.
- [ ] Support, legal, and PR response procedures are in place.
- [ ] The compensation action itself does not introduce another round of irreversible problems.

---

## Non-rollback-able vs rollback-able surfaces

A single change crosses multiple surfaces, and **each surface may have a different rollback mode**.

| Surface | Default rollback mode | When it escalates |
|---------|-----------------------|-------------------|
| User surface (web) | Mode 1 | i18n key removed / API contract changed → Mode 2 |
| User surface (mobile) | Mode 2 | Push delivered / local schema changed → Mode 3 |
| System interface (internal API) | Mode 1 | Outward contract signed → Mode 2/3 |
| System interface (public API) | Mode 2 | Third-party has acted on the new behavior → Mode 3 |
| Information surface (DB schema) | Mode 2 (migration down) | Once backfilled / new columns written → Mode 2/3 |
| Information surface (feature flag) | Mode 1 | Business decisions depend on the new state (orders placed, money charged) → Mode 3 |
| Operational surface (logs / metrics) | Mode 1 | Usually always rollback-able |
| Experience surface (game / mobile) | Mode 2 | Players already earned rewards under the new rule → Mode 3 |
| Asset surface (game) | Mode 1 (CDN manifest swap) | Old client has already downloaded the new asset → Mode 2 |

> **Rule: the overall mode is the mode of the most irreversible surface in the chain.**
> The plan for the whole change must be at least that mode.

---

## Special handling for mobile and games

These two environments are ground zero for rollback asymmetry and need dedicated handling.

### Mobile: version fragmentation is the default

**Facts:**

- App Store expedited review is ~24h; normal review is 1–3 days.
- Play Store review is hours to 1 day.
- But **versions already installed on user devices are out of your control.**
- Forced updates can only request "update on next launch" — a currently-running session cannot be forced.

**Plan requirements:**

1. **Minimum supported version mechanism** — the server can reject clients older than X, but the API must be designed for it up-front.
2. **Local schema migration must be forward-only** — users may skip versions when upgrading.
3. **Remote feature-flag config** — avoid requiring a review round for every small tweak.
4. **Rollout-percentage control** — both iOS and Play Store support staged rollout; **use it**.
5. **Crash reports + auto-disable** — severe crashes trigger an automatic kill switch.

**Anti-patterns:**

- "Ship X; if it's broken, ship X+1." — by the time X+1 lands, X is the current version on 30% of users.
- Hard-coding client behavior turns a bug into something sitting in the user's pocket for six months.

### Games: the dual-track live-ops world

Rollback in games usually splits into two tracks:

| Track | Rollback speed | Constraint |
|-------|----------------|------------|
| **Main binary (client binary)** | Same as mobile; weeks | App store review, users who don't update, version fragmentation |
| **Asset / numerical config (asset / config)** | Minutes to hours via CDN / patch system | Changes must be digestible by the main binary |

**Design principles:**

- **Move anything that might need a hotfix down to the asset / config layer.**
- The main binary is a "framework for running rules" — it does not encode the rules themselves.
- Example: level-boss HP, drop rates, event timing → all in config, not in the binary.
- Example: UI copy, tutorial steps, shop prices → all in server-driven config.

**Anti-patterns:**

- Hard-coding an event's start date in the client → a schedule change must wait for review.
- Putting reward drop rates in the client → balance changes are blocked on a new version.
- Putting PvE boss behavior trees in the client → combat balance changes are blocked on a new version.

### "A rollback plan when rollback is impossible"

For irreversible mobile / game changes, the rollback plan is **not a rollback** — it is:

```markdown
## Rollback Plan (change is irreversible; forward-fix + compensation strategy)

### Forward-fix
- Hotfix path: [remote config / asset patch / expedited review]
- Expected TTM: [duration]
- Users still affected after the fix: [estimate]

### Compensation
- Irreversible side-effect inventory:
  - [e.g. users already received X incorrect rewards]
  - [e.g. entry fees of Y already deducted]
- Compensation actions:
  - [e.g. grant the correct reward delta + send an in-app apology]
  - [e.g. full refund of entry fee + additional compensation bundle]
- Support SOP: [link]
- Does legal / PR need to be in the loop: [yes / no]

### Containment
- How is blast radius reduced: [kill switch / feature flag / rate-limit]
- Monitoring metrics: [error rate / support-ticket volume / community sentiment]
```

---

## Irreversible-side-effect checklist (required in Phase 2)

Every plan must walk through this list and mark which items are triggered:

- [ ] Data already written to durable storage (DB row, blob, log).
- [ ] Email / SMS / push notifications already sent.
- [ ] Payment captured / refunded / transferred.
- [ ] Shipment / physical delivery dispatched.
- [ ] Records written on-chain to an immutable ledger.
- [ ] Records written to a third-party system (CRM, ad platform, analytics).
- [ ] Events dispatched to a webhook or external event bus.
- [ ] Virtual assets / achievements / leaderboard scores granted to players.
- [ ] Client / asset versions already downloaded to user devices.
- [ ] Public announcements / docs / SDK versions already published.

Every checked item forces the rollback mode to **at least Mode 2**, and often Mode 3.

---

## Phase workflow hookup

### Phase 0 (Clarify)

- Ask: "Can this change be rolled back? Which rollback mode applies?"
- If the change crosses mobile, game, third-party, or data-downstream surfaces → mark as "detailed rollback plan required."

### Phase 2 (Plan)

- Fill out the irreversible-side-effect checklist.
- Pick a rollback mode per affected surface.
- The overall rollback plan inherits the most irreversible mode.
- Cross-reference with the migration path in `breaking-change-framework.md`.

### Phase 3 (Test Plan)

- For rollback-able changes, rehearse the rollback flow.
- For forward-fix changes, prepare the hotfix template.
- For compensation changes, prepare compensation scripts / support SOPs.

### Phase 5 (Review)

- The reviewer must check the rollback-mode choice.
- For a combination of L3 / L4 breaking change (see `breaking-change-framework.md`) + irreversible side effects, a second reviewer is required.

### Phase 7 (Deliver)

- Copy the rollback plan into deploy notes / runbook.
- Ensure on-call understands the execution flow.

### Phase 8 (Post-delivery)

- When real problems occur, record "actual rollback mode vs expected."
- Update the examples in this document.

---

## One-page decision cheat sheet

```
To deliver a change, ask:
1. Among all surfaces the change crosses, which is the most irreversible?
2. What is the default rollback mode for that surface?
3. Are any items on the "irreversible side-effect checklist" triggered?
4. Combining the above: which overall mode applies — Mode 1 / 2 / 3?
5. Does the plan contain the required content for that mode?
```
