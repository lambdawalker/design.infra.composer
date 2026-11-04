# Implementing Infra Composer in another language

This specification describes observable behavior at [reference revision ad4cfd2](https://github.com/lambdawalker/go.infra.composer/tree/ad4cfd268616a1ef94b324fe88266f845294f57a). Use idiomatic types, errors and asynchronous primitives in your language. Compare the resulting bindings, order, evidence and failure decisions. A byte-compatible serialization of an SDK's internal objects is unnecessary.

| Layer | Responsibility | First acceptance check |
|---|---|---|
| Core | Validate declarations, resolve contracts, produce an immutable plan | A runtime relationship in both directions can still yield a valid creation order |
| Executor | Consume a locally validated plan and produce outputs or safe partial progress | A validation error invokes zero constructors |
| Configuration | Decide how each artifact reads each logical property | An unavailable secret cannot silently become a default |
| Operator policy | Distinguish an explicit answer, parent cancellation and an approval timeout | A destructive operation waits for a human |
| Provider adapters | Preserve native deferred values, register owned resources, collect evidence | A planned resource has no invented physical ID |
| Report and recovery | Render inventory, preserve evidence, coordinate scoped teardown | A missing parent or a failed check cannot certify absence |

A host owns credentials, CLI flags, repositories, feature factories, provider probes, namespaces and UI authentication. The Attestra app's private snapshot table, byte limits, per-environment access grants and deploy wizard are examples of host policy. Build the library independently of those choices. Configuration editing panels and multi-version release coordination in the [product roadmap](roadmap.md) have a different delivery status from the implemented library below.

## Data model

An application registers feature instances and selects an environment (name, account, region, production flag). Production policy also applies to names equal to prod or production ignoring case. A feature owns local resources, offerings, requirements and runtime-use declarations. Give each resource exactly one owner. Qualify a local name as `feature.localName`. Local identifiers start with an ASCII letter, followed by letters, digits, underscore or hyphen. Contract IDs additionally allow periods.

A resource has an ID, kind, named input expressions, typed outputs, source location and explicit prerequisites with reasons. Expressions may be finite JSON literals, lists, maps, references to a resource output, or references to a required contract field. Sensitivity can wrap a value. Preserve deferred references through nested containers. Reject cyclic values, invalid references and unsupported types before execution.

A contract has an ID, positive major version and named scalar fields (string, integer, number, boolean) with sensitivity. An offering supplies its contract, values for exactly its declared fields, labels and test-only flag. A requirement names the contract fields it needs, selecting labels and an optional default feature/offering. A runtime use names a requirement, source and reason.

## Resolution and validation

1. Register all feature instances. Validate ownership and explicit injections. An injection names the consumer requirement and registered provider offering exactly once. Invalid explicit choices fail.
2. Match contract ID and major exactly. Each required field must exist with the same scalar type. A sensitive requirement needs a sensitive offered field or protected offered value. Each selecting label must match. An offering can declare additional fields.
3. Expand enabled defaults to a fixed point. On each pass, collect defaults only for requirements with zero compatible registered candidates and no explicit binding. Add the supplying features, then resolve **all** requirements again against the final set. Bound expansion (10,000 features in the reference). Registration order cannot decide ambiguity.
4. Choose an explicit compatible binding first. Otherwise one compatible candidate wins. Report missing or ambiguous providers and list alternatives in stable order. Record the origin as explicit, automatic or default. Reject a selected test-only offering in production.
5. Resolve forwarded fields until reaching a literal or resource output. Detect reference forwarding cycles separately from infrastructure dependency cycles. Check every offering value against its declared field type. Track sensitivity through forwarded fields, protected references and nested inputs. Protect originating outputs and the outputs of resources receiving sensitive inputs. Public JSON, formatted diagnostics, plans and simulation results must redact protected values.
6. Every resolved resource input reference adds a creation prerequisite, including nested references. Merge these with declared prerequisites and retain provenance. Runtime uses become a separate relation and do not add creation edges. Sort qualified resource IDs and dependency edges deterministically. The reference visits sorted roots depth first and emits each resource after its prerequisites. Report cycles with a closed path, edge reasons and declaration locations. Long chains must fit without relying on unbounded call-stack recursion.
7. Return diagnostic code, location, message and suggested correction on failure. Useful distinctions include IC_MISSING_PROVIDER, IC_AMBIGUOUS_PROVIDER, IC_INCOMPATIBLE_PROVIDER, IC_TEST_PROVIDER, IC_REFERENCE_CYCLE, IC_UNKNOWN_OUTPUT and IC_DEPENDENCY_CYCLE. A validation failure reports deploymentStarted=false. On success, snapshot declarations and bindings, freeze application injection/default policy and return detached plan views.

The plan exposes application, environment, resources, order, exports, bindings and runtime dependencies. Only the local validator may grant the capability to execute. Public JSON is suitable for inspection and conformance comparison. Deserializing it does not establish validation or restore secrets.

## Execution

A simulator materializes references in plan order. Its synthetic string output is `local://<application>/<environment>/<resource>/<field>`, with zero for integer/number and false for boolean. Preserve output sensitivity. On cancellation or failure, return safe completed operations and the failing stage or resource. Keep arbitrary provider diagnostics out of public errors.

A native adapter resolves kinds through a host-supplied trusted factory registry. Preflight kinds, references, output types and prerequisites before the first registration. Pass native deferred outputs through nested inputs, apply explicit dependencies and secret marking, require factories to return all declared outputs, then register exports. Offline preview can run constructors through mocks with fixture archives and allowlisted region/account lookups. Synthetic identifiers connect mocks internally. Discard them before rendering evidence.

## Configuration binding

Treat application/artifact category and public/confidential sensitivity as separate axes. Every property needs a consumer. Every consumer, including optional properties, needs a binding. A binding specifies artifact, property, initial seed, independent missing policy/default, unavailable policy and eligible source arrangements. A source describes storage, reader, location, key, environment scope, read/write identities, update mechanism, controls, provider rank, cost and applicable freshness bound.

Validate before choosing. Enforce reader support, identities, scope, confidentiality and protected delivery, required controls, and maximum staleness. Remote reads require positive bounded staleness. Reject competing logical owners of environment keys and conflicting writers to shared storage keys. Missing may error, use an explicit default, or omit an optional property. Unavailability or authorization failure stops the read. The initial seed has no effect on missing-value policy.

Explicit binding chooses exactly one valid source. For automatic selection, discard ineligible candidates. Strict supersets of security controls dominate subsets. Incomparable maximal control sets are ambiguous. For equal controls prefer lower provider rank, then lower known cost on a common basis. Ties and unresolved cost comparisons are ambiguous. Preserve protected initial/default values in the detached binding plan. Hosts supply policy rankings and provision readers, storage and permissions. See [configuration and administration](configuration-and-administration.md).

## Approval decision

Manual is the default. Timed mode requires a positive host-selected timeout. The application classifies each operation and supplies a cancellable prompt. Five seconds is Attestra's choice. The policy operates with any supported positive timeout.

| Event | Result |
|---|---|
| User accepts or rejects | Return the explicit decision |
| Timed routine prompt ends solely because its own timer expired | Approve |
| Parent cancelled or its deadline expired, including a race with the routine timer | Stop |
| Abort, terminal error or error combining a timeout with another failure | Stop |
| Sensitive or destructive operation in timed mode | Prompt explicitly without a policy timer |
| Unknown mode/kind, invalid timeout or missing prompt | Reject configuration |

Track timer ownership explicitly. Check parent cancellation before prompting and again before applying the result. A generic timeout exception is insufficient evidence of a routine deadline. Dispose of timers and input readers when the operation ends. Destructive execution retains its [typed confirmation and recovery gates](teardown-and-nuke.md).

## Deployment lifecycle

Install a deployment-local ownership scope before registering resources, derive feature scopes, and propagate them across provider aliases and regions. Follow the [ownership standard](resource-ownership.md) and [report protocol](artifact-reports.md). Between deployments a host may serve cached evidence. During a deployment it should record the attempted checks and publish the human-readable report, including a failed outcome when appropriate.

Keep the destructive recovery journal separate from ordinary artifact reports. Discover every configured application target, inventory before mutation, process environment targets before shared targets, continue independent targets after a failure and gate recovery-key/state cleanup on verified primary cleanup. Persist partial results for restart. A fast check probes only entries previously marked REMAINS and preserves the other results and their timestamps. Implement the exact target scope, status semantics and confirmation boundaries in [teardown and nuke](teardown-and-nuke.md).

Start port verification with the [conformance kit](../conformance/README.md). For native adapters, inject fake constructors, event streams, clocks and provider probes so that the cases can run without credentials.
