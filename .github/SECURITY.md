# Security policy

The `agent-protocol` repository ships **documentation, schemas, templates, skills, and reference hook scripts**. It does not ship a long-running service, a network-facing component, or an installable package that handles user data. The threat surface is accordingly narrow, but still real: reference hooks execute on contributor machines, and a malicious schema or template could mislead a downstream validator.

This policy applies to every file under this repository.

## Supported versions

Only the **latest released version** (`main` branch + most recent tag in [`CHANGELOG.md`](../CHANGELOG.md)) receives security fixes. The methodology is versioned using semantic versioning per [`VERSIONING.md`](../VERSIONING.md); older versions are frozen historical artifacts.

| Version range | Status |
|---|---|
| Latest tagged release | Supported |
| Older tagged releases | Not supported — upgrade before reporting |

## What's in scope

- **Reference hook scripts** under `reference-implementations/hooks-*/hooks/` — command injection, argument injection, unsafe expansion, side effects that escape the hook's advisory role.
- **CI workflow** `.github/workflows/validate.yml` — untrusted-input injection (e.g. `github.event.*`), privilege escalation, cache poisoning.
- **Validation scripts** `.github/scripts/*` — YAML/JSON parsing pitfalls, path traversal when resolving artifact locations, evaluation of untrusted content.
- **Schemas / templates** — a malicious template claiming to be a valid manifest could trick a downstream validator into approving a change. Report structural issues that bypass intended checks.
- **Installable artifacts** — the `.claude-plugin/plugin.json` manifest and any file consumed verbatim by an agent runtime (e.g. `settings.example.json`). Report if any instruction could cause a runtime to exfiltrate data, escalate privileges, or execute unintended code.

## What's explicitly out of scope

- **Third-party agent runtimes** (Claude Code, Cursor, Gemini CLI, Windsurf, Codex, Aider, OpenCode) — report those to their respective vendors.
- **Third-party tools invoked by our hooks** (`yq`, `git`, `curl`) — report upstream.
- **User stacks** that adopt this methodology — the methodology is advisory; security of the adopting codebase is the adopter's responsibility.
- **Opinionated disagreements** with methodology choices (e.g. "Lean mode allows too much") — those are normal issues, not security reports.

## How to report a vulnerability

**Preferred path — GitHub private vulnerability reporting.**

1. Navigate to this repository on GitHub.
2. Open the **Security** tab → **Report a vulnerability**.
3. Provide: a clear description, reproduction steps, affected files / versions, and your proposed severity.

This keeps the discussion private until a fix ships.

**Fallback path — email.**

If GitHub private reporting is unavailable to you, email `abel0615@gmail.com` with subject prefix `[agent-protocol SECURITY]`. Expect a first response within **7 calendar days**. If no response arrives in 14 days, you may escalate via a public issue referencing the silent private report.

**Do not** open a public issue or PR that demonstrates an unpatched vulnerability. The repo preaches "evidence before completion" — a vulnerability report is a contract between reporter and maintainer to ship a fix before evidence becomes weaponizable.

## Disclosure timeline

| Day | Milestone |
|---|---|
| 0 | Report received (private). |
| ≤ 7 | First response from maintainer: acknowledgment + triage verdict (accept / out-of-scope / need-more-info). |
| ≤ 30 | Fix shipped on `main` for accepted in-scope vulnerabilities, or a revised timeline communicated to the reporter with justification. |
| Fix + 7 | Public advisory published (CVE when applicable), reporter credited unless anonymity requested. |

For critical-severity issues affecting the reference hook bundle or CI workflow, the maintainer may ship a patch release (e.g. `1.x.y + 1`) ahead of the 30-day window.

## Safe-harbor for good-faith research

Good-faith security research on this repository — meaning: researching without exfiltrating contributor data, without disrupting other contributors' work, without public disclosure before a fix lands — is welcome. Report clearly, and you will be credited.

---

See also:
- [`CONTRIBUTING.md`](../CONTRIBUTING.md) — contribution rules.
- [`docs/security-supply-chain-disciplines.md`](../docs/security-supply-chain-disciplines.md) — the methodology's own security discipline (what adopting teams should do, not how to report issues here).
