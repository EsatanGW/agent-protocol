# React / Next.js Stack Bridge

> Maps the tool-agnostic methodology to a React app built on **Next.js App Router**.
> This bridge treats "React + Next.js App Router" as one stack because the
> RSC / client-component / Server Action split is what defines most of the
> surface and SoT work — a pure-SPA React bridge would omit half of it.

---

## Scope

**Applies to:** TypeScript codebases using React 18+ and Next.js 14+ with the
App Router (`app/` directory), using React Server Components (RSC), Server
Actions, and the built-in fetch-based data layer. Covers edge + node runtimes,
Middleware, and ISR / `revalidate*` cache control.

**Not in scope for this bridge (use a project-local overlay):**

- **Pages Router (`pages/`)** apps — most patterns translate, but the
  RSC / Server Action sections do not. Treat an existing Pages Router
  codebase as a project-local deviation, or migrate app-by-app and flip
  the bridge when `app/` becomes the majority.
- **Pure SPA React** (Vite, CRA, Remix-in-SPA-mode) with no server
  component boundary — a thinner bridge would suit better; the
  RSC / Server-Action / cache-tag sections are N/A.
- **React Native** — the mobile render target, native modules, and OTA
  update story require a separate bridge.

---

## Surface mapping

> Machine-consumable surface → file-glob mapping lives in
> [`react-nextjs-surface-map.yaml`](./react-nextjs-surface-map.yaml) and is
> consumed by validator rule 3.2 (surface ↔ file-pattern drift).

### User surface

| Concept | Concrete implementation |
|---|---|
| routes | `app/**/page.tsx`, `app/**/layout.tsx`, `app/**/template.tsx`, dynamic segments `app/[slug]/page.tsx`, parallel routes `app/@modal/`, route groups `app/(marketing)/` |
| loading / error / not-found | `loading.tsx`, `error.tsx`, `not-found.tsx`, `global-error.tsx` — each is part of the user-surface contract |
| client components | files with a `"use client"` directive; interactive UI, hooks, event handlers |
| server components | default in `app/` — render-only, no hooks, no event handlers |
| reusable UI | `components/ui/**`, design-system packages, headless primitives (Radix, etc.) |
| styling | Tailwind classes in TSX, CSS Modules (`*.module.css`), `app/globals.css`, Vanilla Extract, or styled-components (with a client-component boundary) |
| copy / i18n | `messages/*.json` + `next-intl` / `react-intl`, or `app/[locale]/` routing, depending on framework choice |
| a11y | semantic HTML + ARIA attributes in JSX; axe/pa11y tests on rendered output |
| navigation | `next/link`, `useRouter()`, `redirect()` (server), `notFound()` — string-based route paths are a Pattern 3 enum |

**Verification surface:**

- `vitest` / `jest` for pure component / hook unit tests
- Testing Library (`@testing-library/react`) for DOM-assertion component tests
- Playwright / Cypress for end-to-end flows against `next dev` or `next start`
- Storybook stories are an editor aid, **not** a verification artifact unless
  paired with a visual-regression runner (Chromatic, Loki).

### System interface surface

| Concept | Concrete implementation |
|---|---|
| HTTP clients | `fetch()` in server components with Next.js cache semantics, or client-side libraries (`@tanstack/react-query`, `swr`) for hydrated data |
| Route Handlers | `app/**/route.ts` — the stack's equivalent of controller endpoints; each exports `GET`, `POST`, etc. |
| Server Actions | `"use server"` functions — a POST-with-`$ACTION_REF`-over-multipart RPC; the closest Next has to a typed RPC boundary |
| Middleware | `middleware.ts` at project root — runs on the edge runtime by default, inspects every matching request |
| Auth / session | NextAuth (`app/api/auth/[...nextauth]/route.ts`), Clerk, Supabase, or custom cookie-session logic under `lib/auth/` |
| External webhooks | Route handlers under `app/api/**/route.ts`, usually pinned to `export const runtime = "nodejs"` when they need Node APIs |
| Feature flags | LaunchDarkly / GrowthBook / Statsig / Vercel Edge Config — resolved in middleware or RSC |
| Third-party SDKs | Typically imported under `lib/` and surfaced either via server actions or route handlers |
| Deployment target | Vercel, self-hosted Node, Docker, or edge runtimes — the `runtime` export on each handler selects per-route |

**Pipeline-order warning:** `middleware.ts` runs **before** route handlers and
server components. Adding middleware that rewrites URLs, injects cookies, or
short-circuits with a `NextResponse.redirect` is a Pattern 4a change — see the
pipeline-order section below.

### Information surface

| Concept | Concrete implementation |
|---|---|
| schema / types | TypeScript types, Zod / Valibot / ArkType schemas, Prisma / Drizzle ORM schemas |
| DB migrations | Prisma `migrations/**`, Drizzle `drizzle/**`, raw SQL `migrations/*.sql` — schema-defined SoT per Pattern 1 |
| server-state cache | Next.js fetch cache + `revalidateTag` / `revalidatePath` — tag names are a Pattern 3 enum catalog |
| client cache | `@tanstack/react-query` query keys — same Pattern 3 enum discipline |
| form state | `react-hook-form` + Zod resolver, or the new `useFormState` / `useActionState` hooks binding to Server Actions |
| config | `.env*` files, Vercel project env, `next.config.js` `env` block, Edge Config stores |
| feature-flag values | Flag provider SDK values — resolved at request time, not build time |
| enum catalogs | TypeScript `const` unions, Zod enums, generated from DB types |

**Dual-representation hotspot:** DB schema (`prisma/schema.prisma` or Drizzle
schema) ↔ TypeScript types derived from it. These are the same data; keep the
generated type as the downstream of the schema, never edit it by hand (Pattern 8).

### Operational surface

| Concept | Concrete implementation |
|---|---|
| build | `next build`, Turbopack (dev), webpack (default prod), output modes (`standalone`, `export`) |
| dependency pins | `package.json`, `pnpm-lock.yaml` / `yarn.lock` / `package-lock.json`, `.nvmrc`, `engines` field |
| lint / format / types | `eslint.config.mjs`, `.eslintrc`, `prettier` config, `tsconfig.json`, `next.config.js` (`typedRoutes`, `experimental` flags) |
| CI | `.github/workflows/**`, `.gitlab-ci.yml`, Vercel project settings |
| deploy | `vercel.json`, Dockerfile, `next.config.js` `output`, infra as code (Terraform, Pulumi) |
| observability | Vercel Analytics, OpenTelemetry via `instrumentation.ts`, Sentry `sentry.*.config.ts`, Datadog RUM |
| error boundaries | `error.tsx` and `global-error.tsx` are **user-surface** (the UI contract), but their Sentry wiring is operational |
| release channels | Vercel preview deploys, promoted previews, branch deploys, canary / A-B via middleware |

---

## SoT pattern bindings

| Pattern | Next.js / React instance |
|---|---|
| 1 Schema-Defined | Prisma / Drizzle schema → generated TS types; Zod schemas for request / response validation |
| 2 Config-Defined | `next.config.js`, `middleware.ts` matcher config, Edge Config, env-var contracts |
| 3 Enum/Status | TS literal unions, Zod enums, **route path catalog**, **`revalidateTag` name catalog**, **react-query key catalog** |
| 4 Contract-Defined | Route Handler request / response shape; Server Action argument types; Middleware redirect contracts |
| **4a Pipeline-Order** | **`middleware.ts` → RSC tree render → Route Handlers → client hydration → Server Actions.** Order is fixed by the framework; reshaping it (adding middleware, changing `runtime`) is a pipeline-order change |
| **4a Pipeline-Order** | **React hook call order** — React's rules of hooks; linted but runtime-fatal if violated |
| **4a Pipeline-Order** | **Next.js cache layers** — Data Cache → Full Route Cache → Router Cache → Browser cache; adding `revalidatePath` / `revalidateTag` in a new place changes the effective invalidation order |
| 5 Process-Defined | Server Action flows that must complete in a specific order across a multi-step form; API-route orchestration |
| 6 Transition-Defined | `loading.tsx` → `page.tsx` → `error.tsx` lifecycle; `<Suspense>` fallback → resolved → error; form state machines via `useActionState` |
| 7 Temporal-Local | Optimistic updates via `useOptimistic`; `revalidate` timestamps on cache entries; ISR `revalidate` windows |
| **8 Dual-Representation** | **DB schema ↔ generated TS types** (Prisma client, Drizzle inferred types); **Zod schema ↔ TS type** (via `z.infer`); **OpenAPI spec ↔ route handler** if present; **server-rendered HTML ↔ client hydrated DOM** — a mismatch throws a hydration warning that is a Pattern 8 signal |
| 9 Interaction-Defined | Parent component → child props contract; render-prop / children-as-function APIs |
| 10 Spec-Defined | Web Platform APIs (Fetch, Streams, FormData) used in Route Handlers and edge Middleware — the platform spec is the SoT |
| supply-chain (extension) | npm registry; lockfile is the verifiable pin; `pnpm audit` / `npm audit` / Dependabot / Renovate as drift monitors |

---

## Next.js-specific pipeline-order discipline

### Request pipeline

```
incoming request
  → middleware.ts (edge runtime, runs per matched path)
  → route resolution (static vs dynamic vs catch-all)
  → [route handler]   OR   [RSC tree render → streamed HTML]
  → client hydration (runs React on the browser)
  → server actions (triggered by form submission or rpc-style call)
  → revalidate / redirect response
```

Rules:

- `middleware.ts` is a Pattern 4a contract. A new redirect / rewrite inserted
  upstream of existing middleware can shadow later logic; order within a single
  `middleware.ts` is explicit (top-to-bottom), but splitting middleware via
  route-group matchers introduces implicit order.
- `runtime = "edge"` vs `runtime = "nodejs"` per route handler is a
  **capability contract** — edge cannot use Node APIs, Node cannot run on
  every Vercel edge region. Changing this export is a surface change.
- Server Actions run **after** the RSC render has committed; treating them as
  "another API call" misses the fact that they trigger an automatic
  router-cache invalidation for the page they were called from. A Server
  Action that writes data without `revalidatePath` / `revalidateTag` leaves
  stale UI on the next navigation.

### Cache invalidation order

Next.js has four cache layers. When multiple fire on the same request, the
effective order matters:

| Layer | Scope | Invalidators |
|---|---|---|
| Data Cache | per-fetch, durable on the server | `revalidateTag`, `revalidatePath`, `{ next: { revalidate: N } }`, explicit `cache: 'no-store'` |
| Full Route Cache | per-route, durable | `revalidatePath`, dynamic APIs (`cookies()`, `headers()`, `searchParams`), `export const dynamic = 'force-dynamic'` |
| Router Cache | per-client, in-memory | navigation, `router.refresh()`, Server Action return |
| Browser / CDN | platform-specific | `Cache-Control` headers on Route Handlers, Vercel Data Cache |

A Server Action that calls `revalidateTag('posts')` invalidates Data + Full
Route at once; the Router Cache on the originating client is separately
refreshed by the action's return. A Server Action that does **not** call
either leaves the Data Cache stale and a user who navigates away and back
will see the old data until the next revalidate window. Treat the tag
catalog as a Pattern 3 enum — centralize it.

### React hook order

React's rules of hooks (`react-hooks/rules-of-hooks`) enforce a static hook
call order per component render. Conditionals around hooks are a runtime
crash; `eslint-plugin-react-hooks` catches the easy cases, but patterns like
calling a hook inside a `try / catch` or after an early return are not always
flagged and must be reviewed as Pattern 4a issues.

---

## Dual-representation hotspots

1. **DB schema ↔ TypeScript types.** Schema is upstream; generated types are
   downstream. Edit only the schema and re-run `prisma generate` /
   `drizzle-kit push`. Hand-edited types that drift are a classic Pattern 8
   bug.
2. **Zod schema ↔ TS type.** Use `z.infer<typeof schema>` to derive the type
   from the schema; do not write both by hand.
3. **Server-rendered HTML ↔ client hydrated DOM.** If the server render
   depends on data the client cannot reproduce (e.g. `Date.now()`, locale,
   `window`), hydration mismatch is the result. Treat any
   "Text content did not match" warning as a Pattern 8 drift signal.
4. **OpenAPI / tRPC / GraphQL schema ↔ route handler or RSC fetch.** If the
   project uses any of these, the schema is upstream; the route handler is
   the implementation of that contract. Handler drift vs schema is a
   Pattern 8 + Pattern 4 issue.
5. **URL path ↔ `app/` folder structure.** The folder structure *is* the
   route. The `typedRoutes` experimental flag makes this explicit;
   without it, a rename of `app/posts/` to `app/articles/` silently breaks
   every `<Link href="/posts/...">`.

---

## Rollback mode defaults

| Change type | Default mode | Reason |
|---|---|---|
| Client-component-only change (styling, local state) | Mode 2 (forward-only) | Previews are isolated per-PR on Vercel; rollback = redeploy previous commit |
| Route Handler behavior change (same request/response shape) | Mode 2 | As above |
| Server Action shape change (new required field) | Mode 3 (compensation) | Clients may call the old shape until they reload; add forward-compat field handling or gate behind a version header |
| DB migration adding a non-null column | Mode 3 | Split into additive-then-backfill-then-constrain; never a single destructive migration |
| Middleware matcher change that short-circuits routes | Mode 3 | Users who navigate during deploy may see the new redirect unexpectedly; coordinate with cache invalidation |
| `revalidateTag` name change | Mode 3 | The old tag remains bound to cached entries; plan a cutover window |
| Server Component → Client Component conversion (or reverse) | Mode 2 with visual-regression gate | Hydration / rendering semantics differ; visual + behavioral test required |
| Full route migration (Pages Router → App Router) | Mode 3 | Stage per-route behind a middleware-level route flag; never flip the whole app at once |

Environment rollback (Vercel preview promotion, blue/green) is a separate
axis. A preview deploy that never promotes to production is zero-risk; the
modes above apply once a deployment is serving real users.

---

## Build-time risk

### Toolchain contracts

- `next` version, `react` / `react-dom` versions, and the matching `@types/*`
  packages are a coupled version pin. A minor `next` bump can subtly change
  RSC serialization rules.
- `node` engine (`.nvmrc`, `engines.node`) is the runtime SoT for local + CI
  + self-hosted; Vercel's edge runtime is a separate constraint.
- `typescript` version — `next build` runs the TS check; bumping TS can
  surface latent type errors that were previously silently accepted.
- `next.config.js` `experimental` flags (`ppr`, `dynamicIO`, etc.) are
  build-time risk magnets; each must be called out in the manifest.

### Manifest fields to mark

- `cross_cutting.build_time_risk.toolchain_change: true` for `next`,
  `react`, `node`, `typescript`, or `eslint-config-next` bumps.
- `cross_cutting.build_time_risk.minification_rules_touched: true` if the
  change adds dynamic imports, `use server` / `use client` directives in
  unusual places, or modifies the output config (`standalone`, `export`).
- `cross_cutting.build_time_risk.bundle_size_verified: true` — any new
  large dependency or a Client Component promotion from a Server Component
  needs a bundle-analyzer read (`@next/bundle-analyzer` or Vercel's built-in).

---

## Uncontrollable external surface

Items outside the team's control that still shape behavior:

- **Runtime differences.** Vercel edge (limited APIs, region-local),
  Node serverless (cold starts), self-hosted Node (persistent), each behave
  differently. A handler tested locally on Node may fail on edge for using
  `Buffer`, `crypto.randomBytes`, or a Node-only npm package.
- **Upstream npm churn.** React canary features, Next.js release cadence,
  third-party component libraries; `pnpm-lock.yaml` is the SoT.
- **CDN / ISR behavior.** Vercel's Data Cache, Cloudflare, Fastly — each has
  its own invalidation semantics layered on top of Next.js caches.
- **Browser runtime variance.** Safari / Firefox / Chrome diverge on
  `<form>` behavior, `popstate`, Intersection Observer; client-component
  code runs in all three.
- **Third-party script injection.** Tag managers, analytics SDKs, chat
  widgets — loaded via `next/script` — can break hydration or CSP without
  any Next.js code change.

---

## Automation-contract implementation

### Layer 1 — structural validity

- `tsc --noEmit` passes; `next build` passes.
- `eslint` with `eslint-config-next` passes, including `react-hooks/*` rules.
- Zod / Prisma / Drizzle schemas compile; `prisma validate` / `drizzle-kit check` pass.

### Layer 2 — cross-reference consistency

React/Next-specific drift checks to ship in bridge CI:

1. **Route catalog check.** Enumerate every `app/**/page.tsx` and compare
   against every `<Link href="...">`, `router.push("...")`, `redirect("...")`
   call site. Typos in dynamic-segment paths are silent. The `typedRoutes`
   experimental flag is the preferred mitigation; a CI grep is the fallback.
2. **`revalidateTag` / `revalidatePath` name catalog.** Treat the tags as a
   Pattern 3 enum. Every `fetch(..., { next: { tags: [T] } })` tag must be
   referenced by at least one `revalidateTag(T)` and vice versa.
3. **`"use client"` / `"use server"` boundary audit.** Server Components
   cannot import Client Components' hook code; Client Components cannot
   directly import server-only modules (`server-only` package helps enforce).
   CI should fail on any `server-only` import leaking into a client subtree.
4. **Env-var shape drift.** `.env.example` enumerates every required var; a
   CI check that every `process.env.X` in the codebase is present in
   `.env.example` catches the "works on my machine" class of bug.
5. **DB-schema / generated-type drift.** After the schema changes, CI must
   re-run the generator and fail if the checked-in generated file diverges.
6. **API-contract / route-handler drift.** If OpenAPI, tRPC, or a shared
   Zod contract package defines the request / response shape, CI must
   re-derive handler types and fail on drift.

### Layer 3 — drift detection

- `next` / `react` / `node` / `typescript` / `eslint-config-next` version
  matrix against a known-good pairing; flag untested combinations.
- Dependency updates via Dependabot / Renovate — each bump reviewed against
  the surface it can touch (a `react-dom` patch is system-interface /
  information because of hydration rules).
- Stale env-var detection: a var defined in `.env.example` but not
  referenced in the codebase is either dead config or a missed rename.

---

## Multi-agent handoff conventions

- **Planner** drafts the Change Manifest, enumerates which surfaces are
  touched (often user + system-interface for a Server Action change; user +
  information for a new form), and explicitly lists the route paths and
  cache tags that will be introduced or invalidated.
- **Implementer** writes the code, keeps the `"use client"` / `"use server"`
  boundary intact, and updates the tag / route catalogs in the same PR. If
  the implementer needs a runtime change (`edge` ↔ `nodejs`), flag it to
  the planner as a Pattern 4 contract change.
- **Reviewer** runs the self-test, re-verifies the boundary audit, and
  confirms the rollback mode matches the risk profile.

---

## Typical workflow per task type

| Task | Mode | Minimum artifacts |
|---|---|---|
| Copy / styling change in an existing component | Zero ceremony | PR diff + visual check in Vercel preview |
| New Client Component in an existing route | Lean | Testing Library test + Storybook / visual-regression snapshot if part of design system |
| New Server Action | Lean → Full if it mutates DB | Zod schema for inputs + route-revalidation plan + form-integration test |
| New Route Handler (`route.ts`) | Lean → Full if public-facing | request/response Zod schemas + integration test + auth check |
| New route (`app/**/page.tsx`) | Lean → Full if deep-linked | loading / error / not-found siblings + route catalog update + e2e happy-path |
| Middleware change (matcher, redirect, cookie) | Full | pipeline-order review + per-runtime test (edge vs node) + rollback plan |
| `next` / `react` major version bump | Full | matrix test + bundle-size diff + RSC/hydration spot checks + CHANGELOG of framework-level behavior changes |
| DB migration (Prisma / Drizzle) | Full | forward + reverse migration verified + mode-3 split if destructive |
| Pages Router → App Router migration (per-route) | Full | behind a flag; parity test vs old route; rollback via middleware |

---

## Reference worked example

See [`../examples/react-nextjs-app-example.md`](../examples/react-nextjs-app-example.md)
for an end-to-end walk-through of a Server Action migration that crosses
user + system-interface + information + operational surfaces and exercises
the cache-tag invalidation contract.

---

## Validating this bridge against your project

### Self-test checklist

- [ ] **Route catalog check** — every `<Link>` / `router.push` / `redirect`
      target resolves to an `app/**/page.tsx` or static asset.
- [ ] **Cache-tag catalog audit** — every `tags: [...]` fetch is matched by
      at least one `revalidateTag` call; every `revalidateTag` call references
      a tag that at least one fetch uses.
- [ ] **Boundary audit** — no `server-only` modules leak into client
      components; no client-only hooks accidentally executed in server
      components.
- [ ] **Env-var parity** — every `process.env.X` reference is declared in
      `.env.example` (or equivalent).
- [ ] **Schema / type parity** — `prisma generate` / `drizzle-kit push` are
      up to date with the committed schema; no hand-edited generated files.
- [ ] **Hydration warnings** — a clean dev-server boot followed by every
      top-level route load shows zero "Text content did not match" warnings
      in the console.
- [ ] **Runtime declarations** — each Route Handler explicitly sets
      `export const runtime = 'edge' | 'nodejs'`; implicit defaults are a
      latent bug.
- [ ] **`loading` / `error` siblings** — every `page.tsx` at least two
      levels deep has a `loading.tsx` and `error.tsx` sibling (or inherited
      from an ancestor).
- [ ] **Middleware matcher audit** — `middleware.ts` `config.matcher` is
      explicit; the `/((?!api|_next|.*\..*).*)` catch-all is justified, not
      copy-pasted.

### Known limitations of this bridge

- **Pages Router (`pages/`)** — only partially applies; use a project-local
  overlay for Pages-Router specifics (data fetching via `getServerSideProps`
  / `getStaticProps`, API routes under `pages/api/`, different cache model).
- **Pure SPA React** — the RSC / Server Action / middleware sections do not
  apply; most of the user-surface and operational-surface guidance still
  holds.
- **Remix, Astro, TanStack Start, Waku, React Router 7 in Data Mode** — each
  has its own framework contract; cross-reference this bridge's React-only
  sections but treat framework-specific pieces as needing their own bridge.
- **React Native** — separate bridge (UIKit-style native layer, OTA update
  via CodePush / EAS Update, App Store review), not this one.
- **Partial Prerendering (PPR), `dynamicIO`, and other experimental flags** —
  their contracts are unstable across `next` minor versions; treat each as a
  project-local deviation and pin a specific `next` version until stable.
- **Monorepo with multiple Next.js apps** — the surface map applies per-app;
  cross-app code sharing via a workspace package is normal, but the bridge
  does not cover monorepo-level release orchestration (Nx, Turbo, Moon).

For the project-local overlay pattern (Pages Router addenda, Remix/Astro
adapters, PPR / `dynamicIO` experimental-flag pinning, monorepo release
orchestration), see
[`../bridges-local-deviations-template.md`](../bridges-local-deviations-template.md)
and the end-to-end walk-through in
[`../bridges-local-deviations-howto.md`](../bridges-local-deviations-howto.md).

---

## What this bridge does NOT override

- Four core surfaces, extension surfaces, Change Manifest schema, operating
  contract — unchanged.
- Framework-specific experimental flags (PPR, `dynamicIO`, `after`, etc.) —
  this bridge documents the stable App Router contract; experimental flags
  live in project-local addenda until they stabilize.
- Pure SPA React without a server-component boundary — the bridge assumes
  App Router as the defining feature; SPA-only apps need a thinner bridge.
