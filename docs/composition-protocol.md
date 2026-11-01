# Composition protocol

## Status and terminology

**Recommended specification, 2026-11-01.** This makes the [architecture](architecture.md) more precise; it does not implement new APIs. The [validation matrix](validation-and-milestones.md) distinguishes existing local behavior from proposed cloud behavior.

| Term | Meaning |
|---|---|
| Standalone mode | An application composition containing a feature and its explicitly permitted default providers |
| Standalone entry point | The command/program building that composition; importing the reusable feature never invokes it |
| Standalone provider | A declared dependency implementation selected under that composition's default policy |
| Configuration manager | The authorized backend managing property values/bindings; deployment ownership determines its scope |
| Registered offering | An offering owned by a feature included in the application's resolved composition |
| Engine | Shared planning/orchestration used by CLI, CI and admin; Pulumi remains the cloud executor |

Standalone mode does not prescribe a separate process, account or stack. Isolation follows the environment and ownership manifest. Suppressing a feature's panel does not remove its required backend.

## 1. Explicit feature registration and provenance

Begin with application-selected, dependency-locked packages. No internet-wide discovery or automatic repository cloning is required. The application assigns stable feature-instance IDs; a package may have several instances.

A future data-only feature manifest records schema version, package identity/version/digest, declaration entry point, contract identities/versions, offered fields/capabilities, requirements, permissible defaults, configuration inventory, adapter requirements and source provenance. Secret values and live credentials never belong in it. Validate manifest structure before executing declaration code; installing/importing a Python feature still executes trusted code and is not sandboxed merely because a manifest is data-only.

Use normal package dependency locks plus recorded feature/contract digests. Verify source provenance and approved publishers according to the deployment profile. A future remote registry may supply candidates, but cannot authorize package installation, identity changes or runtime fallback. Contract definitions live in a neutral versioned package/schema. Behavioral compatibility needs a conformance suite; labels or a shared field name do not prove it.

The current prototype uses in-process objects and explicit feature lists; separate publication, verified manifests and package discovery are future work.

## 2. Deterministic resolution

Resolution consumes a frozen environment/profile, package lock, registered feature instances, explicit injections, and default policy. Iteration order is never a provider-selection rule.

1. Include application-selected features and the owners of explicit injections. Reject duplicate instance IDs and conflicting ownership.
2. For each requirement, validate an explicit binding first. Invalid explicit selection fails; it cannot silently fall back.
3. Otherwise filter registered offerings by contract identity, supported version rules, required fields/types and capabilities, selecting labels, environment/account/region constraints and supported sensitivity requirements. Evaluate production policy on the selection without silently hiding prohibited providers.
4. Exactly one eligible candidate resolves the requirement. Several produce ambiguity with candidate identities and rejection/selection reasons. None permits a declared default only when that requirement and composition profile enable it.
5. Expand permitted defaults and their requirements in deterministic rounds until the feature set stops growing. Recompute candidates against the final set; a newly introduced provider can create ambiguity. Bound expansion and report cycles or excessive growth with origins.
6. Validate every selected binding and offering; resolve forwarded references to concrete literals or resource outputs. A forwarding cycle has its own diagnostic.
7. Freeze exact selections, origins and policy/schema versions in the resolved plan/lock. Unselected defaults create no resources.

A prohibited test provider is an error, not an excuse to hide it and select a different provider. No automatic downgrade follows a runtime timeout, access denial or failed readiness probe. Optional requirements need an explicit absent-state contract.

**Current supported compatibility:** exact capability ID and positive contract major; required scalar fields have identical types and selecting labels match. The prototype also forbids selected test-only offerings in production. Additional capability/scope checks are proposed extensions, not existing guarantees.

**Version ranges:** feature package versions, capability contracts, public API versions and client builds remain independent axes. The initial resolver does not promise a general SemVer solver. Until a versioned range grammar and tests exist, unsupported ranges must fail explicitly. A future range resolver must select only application-approved locked candidates, report unsatisfied constraints and never resolve ambiguity by choosing the highest release. Adapting contract v2 behind public API v1 requires an explicit tested adapter; numerical equality across those axes is unnecessary.

## 3. Resource and operation graphs

Resolve capability references before constructing creation edges. Include explicit prerequisites and output references nested in maps/lists, with edge reason, input path and source location. Keep runtime-call edges separate.

Validate unknown targets, duplicate owners and self-edges; run deterministic topological traversal or iterative DFS/SCC analysis on the expanded creation graph. A cycle diagnostic returns a closed path and every edge's reason/origin. Stable traversal order helps reproducibility without requiring independent operations to run serially. The algorithm need not enumerate every possible cycle to identify blocking components.

For example, Auth.handler → Email.handler → Auth.store is a valid creation chain even if the features call each other at runtime. Auth.handler → Email.handler → Auth.handler blocks creation. A forwarding-only cycle can fail before either graph is built.

Future execution graphs also include binding, readiness and activation operations. Validate their dependencies and cross-stack prerequisites too. Arbitrary hooks or provider-discovered dependencies outside the model are explicitly outside preflight guarantees; unsupported hooks cannot claim validated ordering. Pulumi retains its own dependency/provider checks.

## 4. Foundation bootstrap

Declaration collection stays free of deployment mutations. Insert a foundation stage before feature execution:

1. Resolve the target account/region, operator identity, backend/secrets-provider references and independently usable recovery route.
2. Inspect existing foundation resources or produce a separate bootstrap plan for missing state storage, encryption access and control-plane prerequisites. In a combined deployment, collect and validate the logical feature composition first, representing foundation outputs symbolically; invalid contracts/cycles block both executors.
3. Validate and execute that authorized bootstrap plan; checkpoint resource identities in a protected local journal until shared state is usable.
4. Verify ownership, decryption and backend access, then freeze/revalidate the feature plan against the actual foundation outputs.
5. Deploy features and publish discovery only after their readiness gates.

Bootstrap and feature execution retain separate plan/job boundaries. A separately requested bootstrap may run without features. Each invalid plan causes no mutations by its executor, but successful bootstrap effects may already exist if later native feature validation fails; diagnostics must report them rather than saying no deployment started.

An existing foundation can be adopted only with ownership/access checks. DNS authority may be externally provided; the admin UI is not required to exist before its own deployment. Initial bootstrap cannot depend on outputs from a previous installation. Interrupted bootstrap resumes by inspection and adoption, not blind recreation. A bootstrap failure does not justify deleting state locks or creating replacement keys silently.

## 5. Bounded readiness contract

Illustrative future data shape, not a supported Python API:

```json
{
  "schema_version": 1,
  "id": "api.tls_ready",
  "adapter": "https.tls",
  "target_binding": "application.api",
  "depends_on": ["api.domain_binding"],
  "interval_seconds": 5,
  "timeout_seconds": 300,
  "attempt_timeout_seconds": 4,
  "success": {"hostname_matches": true, "status": 200},
  "gates": ["release.activation"]
}
```

Targets resolve through trusted bindings; never accept arbitrary URLs, shell commands, expressions or credential-bearing probe payloads from the browser. Adapter-specific schemas define allowed success conditions and read permissions. Native status, DNS observations and actual TLS/application readiness are separate checks.

Persist an absolute deadline, attempts and last safe observations in the job. Use bounded backoff/jitter; restarting a worker does not restart the deadline. Distinguish pending, timeout, denied access and terminal incompatibility. Cancellation stops future probes but does not remove already created resources. Recheck gates before activation if observations have expired; a successful historical probe is not permanent readiness.

## 6. Plan and execution boundary

Keep logical output references, secret metadata, ownership, operation dependencies and target context in the core plan. The Pulumi adapter translates them into native Outputs, secret values and resource options without flattening unknowns. A generic plan must not invent guarantees that a provider cannot enforce.

A proposed adapter reports capabilities, previews a target-bound plan, executes/resumes a durable job, and observes native state. The preview records package/code/configuration/policy identities and relevant state fingerprints. Replan when these change; a plan digest is not proof that credentials or cloud state remain valid.

The prototype already has an immutable simulator-oriented Plan. It lacks typed secret values, cloud preview, persistence and readiness. Extending that boundary is preferable to requiring Terraform/Crossplane support now. Resource updates, replacements, secret propagation and state recovery remain Pulumi-specific until another independently tested adapter exists.
