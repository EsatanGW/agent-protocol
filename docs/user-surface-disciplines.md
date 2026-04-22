# User Surface Disciplines

> **English TL;DR**
> Per-change checklist for the *user surface* — what a human actually sees, clicks, waits for, and interprets. Five observation axes: **UI flow correctness** (can the user complete the requested journey end-to-end; entry/action/result/feedback/errors stay consistent), **contract alignment** (component data shape matches SoT; loading/empty/error/partial states all handled), **internationalization and copy** (every new or changed string has an i18n key; every supported locale has a matching value), **usability** (keyboard reachable + focus visible + semantic markup correct; color contrast + responsive behavior reasonable), **operational hooks** (critical actions captured by logging/telemetry; dangerous actions gated by explicit confirmation). Applies to route / page / component / form / table / modal / drawer / state store / query layer / i18n / design system changes. Companion to `implementation-disciplines.md` and `operational-disciplines.md`.

This document provides general-purpose review checkpoints for any change that touches the **user surface**.

## When this document applies

Apply this discipline whenever a change touches any of the following:

- route / page / component
- form / table / modal / drawer
- state store / query layer / API client
- i18n / copy
- design system / theme
- a11y / responsive / keyboard / focus
- analytics / telemetry hooks

## Primary observation axes

### UI flow correctness

- The user can complete the full path described in the requirements.
- Entry points, actions, results, feedback, and errors all exist and stay consistent.

### Contract alignment

- The data shape a component reads matches the source of truth.
- Loading / empty / error / partial states are all handled.

### Internationalization and copy

- Every new or changed string has an i18n key.
- Every supported locale has a corresponding value.

### Usability

- Keyboard reachable, focus visible, semantic markup correct.
- Color contrast and responsive behavior are reasonable.

### Operational hooks

- Critical actions are captured by logging / telemetry.
- Dangerous actions have an explicit confirmation flow.

## General review checklist

- [ ] UI flow matches the requirements.
- [ ] component / route / state / API-client wiring is correct.
- [ ] i18n keys are complete across all supported locales.
- [ ] validation / error / empty / loading states are complete.
- [ ] Accessibility is reasonable.
- [ ] No leftover debug / mock / placeholder data.
- [ ] lint / test / build passes.
- [ ] Deliverable visual evidence exists (screenshot, recording, or equivalent).

## Verification methods

Combine as appropriate for the project:

- lint / test / build
- component / integration / e2e tests
- Browser interaction verification
- Screenshot / recording
- Console / network inspection
- a11y checks
