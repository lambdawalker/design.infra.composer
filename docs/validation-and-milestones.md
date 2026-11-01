# Validation evidence and focused milestones

## Status and evidence rules

**Recommended verification process, 2026-11-01.** Requirements, implementation and verified behavior are separate states. A detailed artifact panel plan is not evidence that its adapter works.

Use section-level status labels or table status columns: **Agreed requirement**, **Recommended design**, **Open choice**, **Implemented**, and **Verified**. Implementation/verification claims include repository, immutable commit, test command, scope, result and date. A verified simulator is not verified cloud behavior.

## 1. Current evidence

Prototype snapshot: [infra.composer.example 9a2f38e](https://github.com/lambdawalker/infra.composer.example/tree/9a2f38e841f3eb27164aca9ee1e13950131662ca). On 2026-11-01, `python -m unittest discover -v` passed **50 tests** on a clean local checkout with an identical Git tree (`ca7a6bf2efa83de4eec1f86f56b55a51c76ef4ad`). This is local validation only.

| Standard behavior | Evidence in that snapshot | Limit |
|---|---|---|
| Explicit/unique matching, labels, defaults and ambiguity | [application tests](https://github.com/lambdawalker/infra.composer.example/blob/9a2f38e841f3eb27164aca9ee1e13950131662ca/tests/test_application.py), including incompatible explicit selection and production rejection | Exact contract major/scalar types; no general SemVer or cloud-scope solver |
| Creation versus runtime relationships | Same tests: mutual runtime references, nested output edges, default-introduced cycles, forwarding cycles | Declared relationships only |
| Self/mutual/long cycle diagnostics | [graph tests](https://github.com/lambdawalker/infra.composer.example/blob/9a2f38e841f3eb27164aca9ee1e13950131662ca/tests/test_graph.py) and [iterative graph implementation](https://github.com/lambdawalker/infra.composer.example/blob/9a2f38e841f3eb27164aca9ee1e13950131662ca/infra_composer/graph.py) | No provider-discovered dependencies |
| Immutable declarations/plans and structured CLI failures | [model tests](https://github.com/lambdawalker/infra.composer.example/blob/9a2f38e841f3eb27164aca9ee1e13950131662ca/tests/test_model.py), [CLI tests](https://github.com/lambdawalker/infra.composer.example/blob/9a2f38e841f3eb27164aca9ee1e13950131662ca/tests/test_cli.py) | Trusted in-process plan boundary; no untrusted serialized-plan execution |
| Standalone/integrated examples and zero operations on invalid plans | [simulator tests](https://github.com/lambdawalker/infra.composer.example/blob/9a2f38e841f3eb27164aca9ee1e13950131662ca/tests/test_simulator.py) | Repeatable records, no persistent resource idempotency |
| Secret sources/vault, durable jobs, readiness, admin/authorization, release routing and cloud adapters | Design documents only | Not implemented or verified by these 50 tests |

For future claims, identify individual cases as well as a total count; a growing test count does not establish coverage by itself. Keep [local milestone limitations](https://github.com/lambdawalker/infra.composer.example/blob/9a2f38e841f3eb27164aca9ee1e13950131662ca/docs/local-milestone.md) visible.

## 2. Next bounded milestone

**Recommended minimum cloud milestone:** retain the existing local composer and add a Pulumi adapter for one dev environment, two small reference features and a deliberately small resource set. Prove declaration → resolution → preview → deploy → read-back, configuration ownership and safe recovery before building the full dashboard.

Exit criteria:

- Typed unknown/output references and sensitivity survive translation; no secret fixtures in plans, logs or preview exports.
- Invalid logical composition blocks both executors in a combined workflow. Each invalid plan produces zero mutations by its executor; separately completed bootstrap effects remain recorded if later native feature validation fails.
- A source-pinned fixture works through Pulumi mocks and a separately authorized disposable dev integration.
- Repeated deployment converges without duplicate resources; bounded update/failure recovery preserves ownership and unrelated settings.
- A foundation can be created/adopted without prior outputs; wrong account/backend and lost decryption access fail clearly.
- Readiness gates activation and survives worker interruption without resetting deadlines.
- Evidence records exact code/configuration/adapter versions and what was actually tested.

This milestone needs its own reviewed implementation design. It does not authorize deploying cloud resources now.

Defer multi-engine execution, remote feature marketplace/discovery, general SemVer solving, all 16 panels, production tenancy and mobile update enforcement until their prerequisite contracts are proven. Deferred requirements remain on the roadmap, not removed.

## 3. Test layers and failure evidence

| Layer | Required evidence as the capability is added |
|---|---|
| Resolver/model tests | Input-order permutations, ambiguous provider sets after default expansion, version/scope rejection, forwarded references and reproducible locks |
| Contract conformance | Required operations and behavioral guarantees; incompatible implementations rejected despite matching labels |
| Adapter/Pulumi mocks | Output edges/secrets, native full-map preservation, update/replacement semantics and supported operation checks |
| Reader/writer tests | Missing versus unavailable/denied source, cache bounds, rotation overlap, revision conflicts and release targeting |
| Job/failure injection | Crash before/after native effect, retries, lease expiry, authorization revocation, audit outage and partial rollback |
| Panel/API security | Cross-environment/shared scope, property escalation, CSRF/XSS, token purpose, target substitution, rate/body limits and secret exclusion |
| Isolated provider integration | Native read-back plus actual data-plane readiness, deletion/recovery boundaries and resource cleanup inventory |
| Release/client contracts | Capability mismatch, unavailable routes, stale policy, independent version axes and supported old/new consumers |

Run cheap deterministic layers first. Mocks cannot prove effective IAM, DNS propagation or actual model quality. Live checks need explicit environment/cost/destruction scope and synthetic data. Do not use a production reset, purge or real identity document as a smoke test.

Documentation CI should validate relative links, manifest/example schemas once finalized, source pins, fences and status/evidence references. Until that CI exists, report manual checks honestly. Provider guidance gets a review date and applicability, not a claim of evergreen currency.

## 4. Disposition of the external review

Reviewed [the shared DeepSeek critique](https://chat.deepseek.com/share/ladj87yh8uee1qeg5f) against main snapshot `d31a00854fc6c48fe0266ec9af5c1b7b3206beed` on 2026-11-01. Its observations are inputs, not normative requirements.

| Review point | Disposition |
|---|---|
| Matching/registration lacks precision | Adopt terminology, explicit registration/lock boundary and deterministic closure in [composition protocol](composition-protocol.md) |
| Cycle algorithm absent | Partly inaccurate: architecture already specified expanded resource/input edges and topological/SCC analysis; prototype implements iterative DFS. Add evidence and clearer operation-graph scope |
| Readiness/bootstrap unspecified | Adopt explicit foundation stage, bounded readiness schema and durable deadlines |
| Application/artifact boundary unclear | Add a classification decision procedure and coupled-change ownership to the configuration guide |
| Credential/auth/panel/audit mechanisms too abstract | Extend [security baseline](security-and-operations.md); retain service-specific artifact plans |
| Client capability negotiation unspecified | Add a proposed advertisement and server-side matching procedure; advertised versions remain untrusted |
| Feature discovery needs a registry | Start with explicit locked package registration; a hosted registry is optional future work |
| General version solver and multiple engines needed | Defer; reject unsupported range grammar and preserve a thin plan/adapter boundary with Pulumi as current cloud target |
| Tests/prioritization absent | Partly inaccurate: acceptance criteria and phased roadmap existed. Add pinned implementation evidence, test layers and a bounded next milestone |
| Status/decision records inconsistent | Add evidence/status convention and lightweight [decision record](decisions.md) |
| Source examples lack pins/date | Already present for the Attestra inventory/catalog. Preserve pinned snapshots and review dates; never imply they track upstream automatically |

Do not add mandatory signed client advertisements as a substitute for authorization, label every sentence with process tags, or claim source-reviewed examples are deployed/secure merely because their documentation is detailed.
