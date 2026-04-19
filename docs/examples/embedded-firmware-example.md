# Worked Example: Embedded / Firmware OTA Update

> **English TL;DR**
> An embedded / IoT device firmware update walked through the methodology: hardware-interface surface as first-class, OTA as a rollout-asymmetry case (rollback is partial and slow), real-world side effects (already-opened locks, already-triggered sensors) as mode-3 compensation. Domain-neutral: no chipset, RTOS, or cloud vendor names.

---

## Scenario

A fleet of already-shipped devices (tens of thousands) needs a firmware update:
- Add a new sensor-calibration algorithm.
- The installed base spans three hardware revisions, each needing a different calibration curve.
- The update requires a device-side reboot.
- A small fraction of devices have been offline for more than 7 days and may miss this rollout entirely.

---

## Phase 0 — Clarify

### Task type
Feature + rollout-sensitive + cross-hardware-revision + **real-world side effect**.

### Surfaces

| Surface | Role | Description |
|---------|------|-------------|
| **Hardware-interface surface** (extension) | primary | Sensor driver, calibration algorithm. |
| System-interface | primary | Device ↔ cloud payload. |
| Information | primary | Calibration parameter schema, device-version map. |
| Operational | primary | OTA scheduling, rollback strategy, offline-device handling. |
| User | consumer | Sensor values displayed in the app may shift. |
| **Real-world surface** (extension) | primary | Physical actions triggered by sensors (alarms, actuation, logging) cannot be recalled. |

---

## Phase 1 — Investigate

### SoT Map

| Information | SoT | Pattern | Consumers |
|-------------|-----|---------|-----------|
| Calibration algorithm | Firmware source + version | Dual-Representation (pattern 8, editor ↔ binary) | Each device revision |
| Hardware revision map | Manufacturing DB | Config-Defined (pattern 2) | OTA dispatcher |
| OTA rollout ratio | Flag service | Config-Defined (pattern 2) | Dispatcher |
| Current device version | Device itself + cloud registry | Temporal-Local (pattern 7) | Dispatcher, customer support |

**Key point:** when a device is offline, the device itself is authoritative (pattern 7) — the central system may not know its current state.

### Consumer classification

- Hardware revisions A / B / C (internal asynchronous — each upgrades at its own cadence).
- App (can upgrade in lockstep).
- Customer-support system (SOPs that record device state).
- Analytics pipeline (downstream of sensor data).

---

## Phase 2 — Plan

### Breaking-change level

| Item | Level | Reason |
|------|-------|--------|
| Calibration algorithm change | L1 | Same input produces different output (schema unchanged). |
| Hardware-revision branch logic | L0 | Each revision is additive on its own. |
| Offline devices skip this round | L1 | Extends the long-tail version-coexistence window. |

### Rollback modes

| Component | Mode | Notes |
|-----------|------|-------|
| OTA dispatcher stops pushing | Mode 1 | Turn off the flag. |
| Firmware on already-updated devices | **Mode 2 forward-fix** | Cannot force a downgrade; only the next release can fix it. |
| Already-triggered physical actions (alarms, actuation) | **Mode 3 compensation** | Irreversible — recovery must be manual or handled by a business process. |

### Long-tail device handling

- Offline > 30 days: device enters degraded mode; the app prompts the user to update.
- Offline > 180 days: flagged as "needs on-site handling" and moved into the deprecation queue.
- Always keep **the last two versions + one LTS version** available, not just the latest.

### Threat-modeling focus

- **Tampering:** OTA packages must be signed; devices verify on arrival.
- **Identity spoofing:** a fake dispatcher → signature + rollback-version protection.
- **Denial of service:** malicious packages that brick devices → preserve a factory fallback.

---

## Phase 3 — Test Plan

| Acceptance criterion | Verification | Evidence |
|----------------------|--------------|----------|
| All three hardware revisions calibrate correctly | Physical-device tests (≥ 3 units per revision) | Before / after calibration data |
| OTA does not brick devices | Simulated power loss, network loss, low battery | Recovery-rate report |
| Devices resume the flow after coming back online | Long-offline simulation | Device logs |
| Devices that cannot upgrade still operate | Parallel-version verification | Dual-version coexistence test |
| Signature verification | Attack test (tampered package, altered version number) | Rejection log |

---

## Phase 4 — Implement

- Canary: roll out to 1% of devices first (a small batch from each of the three revisions).
- Observe crash rate, recovery rate, and sensor-data distribution for 48 hours.
- Gradually widen the rollout.

**AI discipline:**
- Do not unilaterally raise the canary ratio (rollback modes 2/3 coexist — a human must approve).
- Stop the rollout immediately if sensor-data anomalies appear.
- Do not skip per-revision independent verification even if only 1% of the fleet remains on a given revision.

---

## Phases 5–7

- Review: evidence must be complete for all three hardware revisions (not just the majority revision).
- Sign-off: hardware QA sign-off is required.
- Deliver: completion report includes the rollout timeline + explicit "downgrade not available" statement + offline-device handling plan.

---

## Phase 8 — Post-delivery observation

This is where Phase 8 matters most in this example — the hardware long tail lasts for months.

- T+24h: crash rate, OTA success rate (broken down by revision).
- T+7d: calibration-data distribution stability, customer-support feedback.
- T+30d: upgrade ratio among long-tail devices.
- T+90d: execution status of the handling plan for still-not-upgraded devices.
- T+180d: decide whether to force retirement.

---

## Common pitfalls

- Treating "OTA succeeded" as "we're done" → physical actions that already fired (alarms, actuation) are irreversible side effects.
- Forgetting the hardware-revision branching → applying the version A curve to a version B device gives wrong sensor readings.
- No fallback preserved → bricked devices have no recovery path.
- Assuming "all devices can be upgraded" → the long tail is permanent.
- Customer-support SOP not updated → support sees new sensor values and mistakes them for faults.

---

## Linkbacks to `docs/`

- `surfaces.md` — hardware-interface surface + real-world surface.
- `source-of-truth-patterns.md` — pattern 7 (temporal-local) + pattern 8 (dual-representation).
- `rollback-asymmetry.md` — the canonical case of modes 1 + 2 + 3 coexisting.
- `breaking-change-framework.md` — long-tail consumer handling.
- `security-supply-chain-disciplines.md` — firmware signing / hardware trust chain.
- `post-delivery-observation.md` — long-horizon observation is mandatory for embedded.
