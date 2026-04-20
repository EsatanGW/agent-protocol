---
name: Bug report
about: Report a concrete failure of a script, schema, hook, or validator in this repo
title: "[bug] "
labels: ["type:bug", "triage"]
---

<!--
Use this template when something in THIS repository is broken.

If your question is "the methodology doesn't fit my situation," use the
Documentation / methodology feedback template instead.

Before opening: confirm you are on the latest release. See CHANGELOG.md.
-->

## What broke

<!-- 1–2 sentences. What did you do, and what went wrong? -->

## Component

<!-- Which file / area of the repo owns the bug. Check all that apply. -->

- [ ] Schema (`schemas/change-manifest.schema.yaml`)
- [ ] Template (`templates/change-manifest.example-*.yaml`)
- [ ] Reference validator (`reference-implementations/validator-*`)
- [ ] Reference hook bundle (`reference-implementations/hooks-*`)
- [ ] CI workflow or script (`.github/workflows/*`, `.github/scripts/*`)
- [ ] Skill content (`skills/engineering-workflow/**`)
- [ ] Documentation (`docs/**`) — if **factual / link / code-example** failure. For methodology disagreement, use the doc template instead.
- [ ] Starter-repo example (`examples/starter-repo/**`)

## Environment

- Version of this repo (tag or commit SHA): 
- Agent runtime (if relevant — e.g. Claude Code 1.x, Cursor, Gemini CLI): 
- OS: 
- Relevant tool versions (`yq --version`, `python3 --version`, `git --version`): 

## Reproduction

<!-- Minimal steps. Paste commands verbatim. -->

```
$ …
```

## Expected behavior

<!-- What should have happened. Reference the line or section of the spec/doc
     that specifies the expected behavior if you know it. -->

## Actual behavior

<!-- What actually happened. Paste full error output. -->

```
…
```

## Additional context

<!-- Logs, screenshots, manifest snippet, hook event payload — whatever helps.
     Redact secrets. Attach files > 5 KB rather than inlining. -->
