# Recommended additions, acceptance criteria, and open decisions

## Status

This is a proposed implementation sequence, not a claim that implementation exists or that every technical choice is settled. It includes the additional ideas suggested during the design discussion.

## 1. Priority additions

| Area | Required design work | Why |
|---|---|---|
| Ownership | One owner per resource/property; shared/environment/release lifecycle; external-resource references | Safe composition and cleanup |
| Release manifest | Immutable artifacts/hashes, resolved bindings, migrations, config schemas | Reproducible promotion and rollback |
| Durable execution | Persistent jobs/checkpoints, idempotency, locks, retries/cancellation | Recover from crashes and browser closure |
| Activation | Health/readiness checks and consistent routing publication | Do not advertise incomplete deployments |
| Data evolution | Backward-compatible migrations, backfills, destructive-change gates | Concurrent old/new releases must work |
| Admin security | Scoped roles, audit trail, bootstrap/recovery, workload identity | Manage the system without circular lockout |
| Runtime configuration | Typed schemas, revisions, affected-release validation, refresh guarantees | Safe live changes |
| Async work | Event schema versions, compatible consumers, idempotency, draining | Queues outlive deployments |
| Client protocol | Shared SDK/spec for discovery, version, notices, cutoff, recovery | Consistent forced-update behavior |
| Observability | Logs/metrics/traces by app/environment/feature/release; health and usage | Diagnose failures and inform retirement |
| Disaster recovery | State/metadata/artifact/secret backup, restore procedures, recovery drills | Local vault loss must not erase system knowledge |
| CI/CD | Same engine as CLI/admin, noninteractive config, scoped identities | Reproducible automated operations |
| Drift | Compare desired/observed state and reconcile intentionally | Avoid overwriting emergency changes blindly |

## 2. Deployment execution recommendations

Use one engine from CLI, CI, and admin. Model plan, preview, deploy, verify, activate, deprecate, and retire as distinct operations with durable status.

Before mutation, display target account, region, environment, stack/backend, selected releases, providers/defaults, and intended changes. Never log credential values.

Build artifacts once, hash inputs and outputs, reuse unchanged builds, and parallelize independent work. Infrastructure change detection remains Pulumi's responsibility; an unchanged source hash alone does not prove infrastructure/configuration is unchanged.

Coordinate operations across resource state, release inventory, configuration, and routes. Persist desired and observed generations; reject stale edits. Make safe retries idempotent and define compensation rather than claiming a distributed deployment is atomic.

Pulumi already supplies per-stack state locking/history. Preserve those protections and add coordination for operations outside or across stacks. Diagnose stale locks before clearing them; never delete an active lock automatically.

For DNS, certificates, email identities, and similar eventual readiness, expose bounded checks and actionable timeout diagnostics.

## 3. Bootstrap and recovery recommendations

The system must be installable into an empty account/environment without a previous deployment's outputs.

Document how initial state storage, encryption keys, DNS delegation/records, admin identity, and control-plane services are provisioned. Separate these foundation dependencies from feature runtime composition.

Provide recovery access independent of the authentication feature being upgraded. Define credential/key rotation and revocation, emergency access auditing, and restoration of the control plane from durable records.

Do not store production secret values in this repository or use deployment-worker credentials in the browser. Decide explicitly which records are public discovery information.

## 4. Suggested delivery order

1. **Core contracts and declarations:** neutral contract schemas, source metadata, injection, resource ownership, environment context.
2. **Resolver and diagnostics:** provider selection/defaults, resource graph expansion, cycle detection, structured errors, frozen plan.
3. **Standalone reference features:** minimal authentication/email examples and controlled test providers; no accidental package-import deployment.
4. **Pulumi execution adapter and memory:** preview/materialization, vault, readiness, idempotent jobs, durable state, headless operation.
5. **Release registry and data lifecycle:** immutable manifests/artifacts, coexistence, activation, migration/rollback rules, retirement.
6. **Client discovery/update protocol:** policy schema, enforcement middleware, client adapters, deadline and offline behavior.
7. **Admin/index control plane:** independent deployment/versioning, typed configuration UI, access scopes, audit trail, durable job UI.
8. **Operational hardening:** promotion pipeline, contract suites, recovery drills, drift handling, observability and retention policies.

This sequence is a recommendation. Agree the detailed design of each implementation stage before building it.

## 5. Acceptance criteria

### Composition and diagnostics

- A and B remain independently packaged; neither imports the other.
- C injects contract references in both directions without constructing cloud resources early.
- Valid mutual runtime references materialize to an acyclic resource graph.
- Self-cycle, mutual cycle, and longer cycles fail before deployment mutation.
- A cycle diagnostic names the path, reasons, and exact declaration origins.
- Missing/ambiguous/incompatible providers and duplicate ownership have stable error codes and clear fixes.
- Defaults are resolved recursively and cannot bypass scope/version/cycle checks.
- Implicit input dependencies are represented; unsupported opaque hooks are reported.
- Human CLI and JSON outputs agree and redact secrets.

### Standalone and environments

- The same feature implementation runs standalone or under C.
- Standalone tests exercise real feature inputs/outputs with contract-compatible dependencies.
- Production cannot silently activate a test substitute.
- Dev, QA, prod, and custom environments resolve separate intended contexts.
- Identical explicit cloud names across contexts are caught or deliberately scoped.
- Deployment summary identifies the actual cloud account and state target.

### Memory and execution

- A second invocation reuses saved settings without repeating questions.
- Expired credentials trigger service-specific renewal rather than reconfiguration of unrelated settings.
- A vault write interrupted midway cannot silently destroy the last valid vault.
- Secrets remain encrypted at rest and redacted in logs/diagnostics.
- CI can execute without access to a developer's personal vault.
- A failed job resumes/reconciles safely without duplicate resources or premature activation.
- Concurrent changes are serialized or rejected with a useful conflict message.

### Releases and clients

- Deploying 1.0.1 preserves explicitly supported 1.0.0 routes and dependencies.
- Exact pins and movable compatible channels have distinct documented behavior.
- QA-to-prod promotion uses the same artifact hashes.
- A release/configuration incompatible with an active consumer is rejected.
- Old/new releases can share data safely during the supported window.
- Update policies can be announced, revised, canceled, and enforced per environment/platform.
- Store availability gates a scheduled mobile cutoff.
- Clients missing the notice still receive an actionable update-required response.
- Policy/update endpoints remain accessible during lockdown.
- Web update verifies the new build without losing drafts or entering a reload loop.
- Retirement refuses removal of required shared resources, live bindings, or undrained work.

### Control plane

- Admin/index can be deployed/versioned separately from feature backends.
- Discovery never silently crosses environment or API-major boundaries.
- Runtime changes are validated, audited, revisioned, and applied with a documented refresh guarantee.
- Pulumi redeployment does not reset administrator-owned live configuration.
- Closing the admin browser does not terminate a submitted deployment.
- Recovery remains possible when the managed authentication feature is unavailable.

## 6. Open decisions

| Decision | Current direction / constraint |
|---|---|
| Implementation language and packaging | Python examples; final language and distribution not selected |
| Stack boundaries | One graph where practical; split by lifecycle/ownership when justified |
| Contract distribution | Neutral shared package/schema; choose schema/type tooling |
| Graph API | Explicit resource/input edges with source provenance; exact API open |
| Vault | Authenticated encryption; choose library, OS integration, recovery and portability |
| Cloud baseline | AWS/Pulumi discussed; exact products, account boundaries, and hosting open |
| State backend and secrets provider | Durable shared state required; S3/KMS versus other providers not finalized here |
| Shared metadata/artifact stores | Durable authority and versioning required; service selection open |
| Standalone providers | Decide real isolated AWS resources versus emulators/substitutes per contract |
| Admin tenancy | Single admin across environments versus isolated control planes |
| Admin authentication | Bootstrap/recovery independence required; identity provider and roles open |
| Runtime config refresh | Define staleness bounds, caching, push/poll, and failure behavior |
| Version convention | Public API major synchronization; confirm independent internal feature versions |
| Pre-1.0 compatibility | Define stability promises and migration expectations |
| Client wire protocol | Header names, status code, policy schema, unknown-client handling |
| Lockdown/offline behavior | Scope, cached-policy expiry, in-flight work, draft preservation, recovery |
| Store rollout gate | Define availability evidence and staged/cohort rollout handling |
| Release support window | Retention, rollback, security exceptions, retirement criteria |
| Domain convention | Admin/index hosts fixed in intent; environment/API paths and subdomains open |
| Repository governance | License, contribution rules, release publishing, review/merge policies |

## 7. Scope boundaries

The current deliverable is documentation. It does not deploy infrastructure, create credentials, schedule update deadlines, publish client applications, or implement the illustrated SDK.

Future implementation should keep a short decision log, schema/protocol examples, developer onboarding, and operator runbooks alongside these documents. Update the design when a decision changes rather than treating conversation examples as permanent contracts.
