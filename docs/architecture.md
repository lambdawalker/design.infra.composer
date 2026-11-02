# Architecture

## 1. Intent and status

Build a composition system in which independently maintained repositories declare backend features. An application repository connects them without feature repositories importing one another.

This document records the initial discussion. **Agreed** means explicitly requested or accepted in that discussion. **Recommended** captures additional proposals to carry into design. **Open** means not decided. All Python examples here are pseudocode. An initial local composition/simulation milestone is implemented in [infra.composer.example](https://github.com/lambdawalker/infra.composer.example); it does not yet implement the configuration or cloud adapters in this design.

Pulumi is the initial infrastructure execution model discussed. Python is the selected implementation language for the prototype; porting can be considered after the design is proven. Final package distribution remains open.

## 2. Independent features and contracts — agreed

Example repositories:

| Repository | Responsibility |
|---|---|
| A | Authentication feature |
| B | Email validation or cryptographic signature feature |
| C | Imports feature packages, resolves requirements, and deploys the composition |

A feature declares offerings and requirements. C passes a matching offering to a consumer. A and B understand shared contracts, not one another's implementation classes.

Recommended contract metadata:

- Stable capability identifier, such as `identity.user-store/v1`.
- Contract version/range and typed fields.
- Behavioral guarantees and required operations.
- Environment, feature-instance, tenant/account, and region constraints where relevant.
- Secret classification and ownership.
- Source location and human-readable reason for requirements.
- Whether a requirement is mandatory, optional, or has an allowed default.

Labels help select providers; labels alone do not establish interface compatibility. Contract definitions should live in a neutral shared package or schema so that neither feature must import the other.

Matching should use explicit binding first, then a unique compatible registered provider, then an enabled fallback. Missing, ambiguous, or incompatible matches are errors. Never choose an arbitrary candidate.

## 3. Separate three kinds of relationship — agreed

| Kind | Meaning | Treatment |
|---|---|---|
| Declaration reference | A feature describes another capability it will use | May point forward before resources exist |
| Deployment prerequisite | A resource must exist/be ready before another operation | Must yield an acyclic executable graph |
| Runtime dependency | Deployed services communicate or use each other's capabilities | Cycles can be intentional |

Recommended: model readiness prerequisites explicitly. Successful creation of a DNS record does not establish public DNS propagation; declare a bounded readiness check when a later step requires resolution.

Do not turn every runtime call into a deployment dependency. Conversely, prerequisites implicit in resource input references must be included in validation.

## 4. Composition lifecycle — agreed model, proposed API

```python
a = Authentication()
b = EmailValidation()
c = Application(features=[a, b])

b.inject(c.getDeclarationsForB(a))
a.inject(c.getDeclarationsForA(b))

c.deploy(environment="qa")
```

Constructors and injection collect declarations and references. They do not create cloud resources or make deployment mutations.

Recommended internal stages:

1. Collect declarations, offerings, requirements, and configuration needs.
2. Apply explicit injections and resolve compatible providers.
3. Expand permitted defaults and recursively resolve their requirements.
4. Expand feature declarations into resources, bindings, and readiness operations.
5. Validate contracts, scopes, ownership, and the resource prerequisite graph.
6. Freeze a resolved plan and produce a Pulumi preview.
7. Execute the validated deployment; verify readiness before activation.

Repeated injection into the same input should fail unless replacement is explicit. Freeze the declaration graph before execution so late mutations cannot bypass validation.

Passing real Pulumi Outputs into resource inputs preserves Pulumi dependency and secret tracking. Do not flatten unresolved outputs into ordinary strings.

Inside `pulumi up`, materialization registers desired resources and Pulumi executes the operations. If the application launches deployment itself, use an adapter such as Pulumi Automation API. Exact public method names remain open.

## 5. Cross references and creation cycles — agreed

Feature-level mutual references are allowed. Resource creation cycles are not.

Recommended decomposition:

| Declaration | Dependencies |
|---|---|
| Authentication core: user store, execution role | Shared foundation |
| Email core: challenge store, execution role | Shared foundation |
| Authentication workflow | Required core interfaces |
| Email validation workflow | Required core interfaces |
| Permissions, subscriptions, integrations | Relevant resources on both sides |

Connection methods must declare real independently managed binding resources where supported. They must not silently mutate properties owned by another Pulumi resource.

Declaring resources in phases is not the same as deploying several times. A single acyclic graph can execute in one deployment.

If two actual resources need each other's generated identifiers at creation, splitting Python methods does not solve it. Options include an independent intermediary (queue, event bus, or configuration store), a provider-supported identifier known beforehand, or an explicit staged creation/update plan.

Do not assume deferred references, `apply`, or extra `depends_on` edges eliminate a genuine cycle. Do not use previous deployment outputs as a hidden prerequisite for fresh installation.

## 6. Validation and diagnostics — agreed

Validate the expanded resource graph before deployment mutations. Check self-cycles, two-resource cycles, and longer cycles. Topological sorting can establish a valid order; cycle/SCC analysis should produce a useful path.

Example:

```text
DEPLOYMENT BLOCKED [IC_DEPENDENCY_CYCLE]

Authentication.UserPool
  needs EmailValidation.Handler
  because: verification trigger
  declared at: authentication/resources.py:42

EmailValidation.Handler
  needs Authentication.UserPool
  because: USER_POOL_ID configuration
  declared at: email_validation/resources.py:78

Neither resource can be created first.
Suggestion: separate a binding or introduce an independent interface.
No deployment was started.
```

A self-dependency must name the exact resource and declaration and explain that it cannot require itself to exist.

Every diagnostic should include a stable code, concise explanation, affected feature/resource/input, source locations, dependency reasons, and actionable suggestions when known. State whether deployment started and what changed if failure occurs during execution.

Also diagnose:

- Missing provider and why no fallback applies.
- Ambiguous matches, listing candidates and how to select one.
- Incompatible contract version, fields, or scope.
- Invalid/cyclic defaults and their selection origin.
- Duplicate resource/property ownership.
- Missing credentials, rejected credentials, and unavailable targets distinctly.
- Unsupported active-release/configuration combinations.

Report independent failures together without flooding users with consequences of one root failure. Provide human-readable CLI output, nonzero exit status, and structured JSON diagnostics with the same information. Never include secret values.

Preflight guarantees apply only to dependencies represented in the declaration model. Arbitrary deployment hooks are outside that guarantee unless constrained and modeled. Pulumi/provider validation remains a second line of defense.

## 7. Standalone deployment and default providers — agreed

Each feature repository contains:

| Part | Responsibility |
|---|---|
| Reusable feature | Contracts, resources, outputs, and binding declarations |
| Default providers | Dependencies usable for standalone deployment |
| Standalone entry point | Composes the same feature with defaults and exports test interfaces |

Repo C uses the feature package without invoking the standalone entry point. Importing a package must not deploy anything.

A feature may supply a standalone configuration panel. Inside an application, application-owned configuration is the default and the feature panel is not deployed. Both modes use the same exposed property contracts; application integration does not require mounting feature UI or adopting a common JavaScript framework. See [Configuration and administration](configuration-and-administration.md).

Defaults are selected during composition when an input lacks a provider. A configured provider failing at runtime must not silently switch to a test substitute.

Recommended defaults:

- Prefer explicit `None`/missing detection rather than truthiness to decide whether injection was supplied.
- Identify defaults as production-capable or test-only.
- Disable test-only defaults for production unless explicitly permitted by policy.
- Recursively validate defaults; they can introduce new requirements and cycles.
- Include selected defaults and their origins in preview output.
- Use isolated names/state for standalone resources.
- Have test providers implement the same contract and expose controlled test interfaces.

Example: captured email delivery lets a test request a challenge, inspect the message, submit the code, and verify the result without deploying the complete application.

Open: which dependencies get real isolated cloud implementations, emulators, or substitutes in the first standalone profiles?

## 8. Environments — agreed

Support `dev`, `qa`, `prod`, and custom names. An environment is a deployment destination, distinct from a software release.

Each environment resolves a complete context:

- Cloud account/project, region, and credential binding.
- Pulumi backend, project, and stack identity.
- Domain, naming prefix, and resource isolation.
- Feature configuration, runtime configuration scope, and secret bindings.
- Selected and supported releases, routes, and update policies.
- Deployment history and artifact selection.

A separate stack name does not prevent collisions in explicitly assigned cloud names. Validate account/region/names and cross-environment references.

Show application, environment, account, region, stack/backend, and domains before deployment. Production must not silently fall back to development credentials or settings. Explicitly shared credential bindings are allowed.

Recommended: expose deploy scopes for control plane, selected features, or the complete application, while validating prerequisites and ownership across scopes.

Open: one application stack versus multiple coordinated stacks. Repository boundaries do not require stack boundaries. StackReference reads outputs; it does not deploy the source stack. Multi-stack deployment needs explicit orchestration.

## 9. Encrypted deployment memory — agreed

The deployment app remembers tokens, usernames/passwords where required, region, environment, domains, and other selections. Ask only for missing, changed, or expired information.

Features declare configuration needs with type, description, secret classification, scope, validation, and optional defaults. C deduplicates compatible shared requirements; conflicts are errors.

| Scope | Examples |
|---|---|
| Account | Cloudflare token, AWS profile/account |
| Application | Domain, state backend |
| Environment | Region, prefix, environment-specific secret bindings |
| Feature instance | Sender address or dedicated credentials |

Recommended vault behavior:

- Encrypt persisted configuration and secrets with a maintained authenticated-encryption implementation.
- Keep the unlocking key separate from ciphertext; support OS credential-manager and passphrase-based unlocking.
- Use a maintained password KDF, random salts/nonces, versioned format, and authenticated metadata where appropriate.
- Use restrictive file permissions, atomic writes, and concurrency control.
- Unlock once per session; mask secrets in summaries and redact logs/errors.
- Support update, forget, rotation, encrypted backup/export, import, and recovery procedures.
- Never persist plaintext secrets in Git, manifests, shell history, or CLI arguments.
- Pass secrets to Pulumi as secrets so downstream configuration/state remains protected.
- Detect credential failure separately from network/service failure; avoid unnecessary credential replacement prompts.

For AWS SSO, remember profile/account/region selections and let supported AWS tooling manage sessions, renewal, and login. Do not collect the AWS login password as the normal authentication mechanism.

Local memory is not the shared deployment record. CI and other developers need independently authorized secret sources and durable nonsecret manifests. Prefer workload identity/OIDC for CI where supported.

Open: initial vault backend, cross-machine sharing, recovery model, and headless unlock source. A lost passphrase has no recovery unless an explicit recovery mechanism was configured.

## 10. Admin and index control plane — agreed

| Host | Responsibility |
|---|---|
| `admin.domain.com` | Runtime settings, environments/releases, routing, and update policies |
| `index.domain.com` | Human directory and machine-readable environment/version discovery |

The hostname spellings are normalized from the discussion. These sites have deployment and versioning independent of feature releases. Their public contracts need compatibility independent of UI implementation versions.

Discovery returns only intended public metadata. Clients select an environment and compatible API major; never silently switch QA to production or v1 to v2. Endpoints may point directly to versioned integrations rather than proxying every call through the index.

Configuration ownership is application-controlled by default. Features expose configurable properties and artifact consumers; the application binds sources, initial/default values, read/write operations, and permissions. Optional standalone feature panels are suppressed when the application takes ownership. A shared frontend module framework is not a requirement of this design.

The agreed source-selection priority is security, provider guidance, then cost, after functional constraints are met. This supersedes a blanket environment-variable preference. [Configuration and administration](configuration-and-administration.md) defines these rules and AWS examples.

The dashboard has separate **Application settings** (feature/business behavior) and **Artifact settings** (infrastructure, execution and source bindings). Application editors and infrastructure operators have separate backend-enforced permissions. Category does not imply safety: security-sensitive application properties still require explicit safeguards. See the [dashboard classification rules](configuration-and-administration.md).

Recommended control-plane behavior:

- The application decides the UI for feature-declared properties. Schema-generated controls are an option; mounting feature UI is not required.
- Record sensitivity separately from application mechanism: cached runtime reads, artifact configuration rollouts, and managed-resource updates.
- Validate runtime updates against affected active releases before publishing.
- Store revisions, attribution, timestamps, and change history; support rollback where valid.
- Pulumi owns infrastructure/bootstrap defaults; live configuration has one declared authoritative owner. The deployment adapter and configuration manager coordinate updates so a later deployment does not reset administrator changes.
- Define refresh/consistency behavior; a published value is not instantly applied to every warm process. Environment-backed Lambda updates require new published versions and deliberate alias activation; AppConfig is a reader source, not a universal AWS resource controller.
- Specify whether a setting affects all releases or a selected release.
- Secret controls accept replacement values without returning existing values.
- CLI/admin share validation and deployment logic.
- Admin submits durable jobs to a worker; browser closure does not cancel execution.
- Keep deployment privilege in the worker rather than in browser code.
- Use environment-scoped permissions, audit records, and an independent bootstrap/recovery path.
- Cache discovery with bounded staleness; retain reachable update/recovery endpoints during lockdown.

Open: one admin site managing all environments with scoped permissions versus separate control planes, and which discovery metadata should be public.

## 11. Ownership, persistence, and deployment consistency — recommended

Every resource and configurable property has one owner and a lifecycle classification:

- Application/shared foundation.
- Environment-scoped shared resource.
- Feature-instance resource.
- Release-specific resource.
- Explicitly external resource, referenced but not managed.

Define deletion/retention policy and ownership of connections separately. Retiring a release must not delete a shared database or an external resource.

| Store | Contents |
|---|---|
| Git repository | Code, contracts, schemas, design, nonsecret desired manifests |
| Local encrypted vault | Developer preferences and authorized credential material/references |
| Pulumi backend | Resource state, locks, and infrastructure history |
| Artifact store | Immutable release artifacts and hashes |
| Shared control-plane store | Release inventory, desired/observed activation, discovery, update policies, configuration revisions, and job history |
| Managed secret store | Runtime and CI secrets/references with scoped access |

Adopt one authority per field rather than letting Git, Pulumi, and admin overwrite one another. Use a generation/revision with optimistic concurrency for administrative edits. Publish a consistent discovery snapshot only after target readiness; partial failure must not advertise an unavailable release.

Pulumi locking protects a stack. Cross-stack deployment, activation, and retirement require application-level coordination and durable checkpoints. Retry safe steps idempotently and distinguish desired state from observed state.

## 12. Approaches considered

| Approach | Tradeoff | Direction |
|---|---|---|
| Feature repositories import each other | Simple initially; tightly couples implementations and creates import cycles | Rejected by the requested independence |
| Match cloud tags/labels alone | Easy discovery; insufficient contract/type/ownership guarantees | Use labels only as selection metadata |
| C composes declarations through contracts | Requires resolver and diagnostics; supports independent features and standalone defaults | Agreed direction |
| One stack for composed components | One resource graph and preview; shared deployment boundary | Open |
| Separate stacks per lifecycle boundary | Independent operations; explicit orchestration and output compatibility required | Open |

## 13. References

These describe underlying mechanisms, not an existing infra.composer implementation.

- [Pulumi components](https://www.pulumi.com/docs/iac/concepts/components/)
- [Pulumi inputs and outputs](https://www.pulumi.com/docs/iac/concepts/inputs-outputs/)
- [Pulumi explicit dependencies](https://www.pulumi.com/docs/iac/concepts/resources/options/dependson/)
- [Pulumi stack organization](https://www.pulumi.com/docs/iac/guides/basics/organizing-projects-stacks/)
- [Pulumi secret handling](https://www.pulumi.com/docs/iac/concepts/secrets/)
- [AWS CLI SSO configuration](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-sso.html)

## Resource ownership

Apply the [resource ownership standard](resource-ownership.md) to tags, mutable descriptions and metadata-only inventory, including shared resources and provider limitations. Existing resource identifiers are preserved.
