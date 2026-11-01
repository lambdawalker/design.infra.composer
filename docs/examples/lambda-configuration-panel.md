# Lambda: expanded post-deployment configuration and custom-panel plan

## 1. Scope and evidence

This extends the earlier URL/secret-source example into an operational configuration plan for Attestra's Lambda artifacts. Apply [configuration policy](../configuration-and-administration.md): security and functional constraints first, AWS guidance next, operating cost among eligible choices.

Reviewed [go.attestra.aws.auth 4607807](https://github.com/lambdawalker/go.attestra.aws.auth/commit/4607807ab0346f4a38532982889fe2e56954412e) on 2026-11-01. This is a source-derived proposal, not current cloud observations or implemented controls. See the [artifact inventory](attestra-configuration-plan.md) and adjacent [API Gateway panel plan](api-gateway-configuration-panel.md).

The custom panel should expose curated, typed controls per artifact profile, not an arbitrary Lambda console or raw environment-variable editor.

## 2. Current function profiles

All reviewed functions use Go `provided.al2023`, ARM64 ZIPs. Published Lambda versions/alias traffic management are not declared in this snapshot.

| Profile | Explicit source defaults | Invocation constraints |
|---|---|---|
| Email signup/resend/confirm | 256 MB, 25 seconds | Synchronous HTTP API; secret-backed proof operations and SES/Cognito calls |
| Passkey registration and sign-in handlers | 20 seconds; memory omitted in the resource declarations | Synchronous HTTP API/Cognito operations; some enrollment handlers read runtime policy |
| Cognito challenge trigger | 10 seconds; memory omitted | Cognito synchronous trigger has its own fixed five-second response deadline |
| Capture API | 256 MB, 25 seconds | Synchronous HTTP API; identity/consent checks and uploads |
| Capture worker | 1024 MB, 90 seconds | SQS mapping, batch size 1, max concurrency default 2, partial-batch failure reporting |
| Capture dispatcher | 1024 MB, 90 seconds | Minute-based EventBridge sweep; same deployment loop currently assigns worker-sized defaults |
| Public app-config | 128 MB, 10 seconds | Public HTTP API; current DynamoDB runtime configuration projection |
| Shared admin/index | 256 MB, 20 seconds | HTTP API, shared control plane; index explicitly uses shared concurrency |
| Environment reset | 256 MB, 60 seconds | Explicit control calls and minute-based work; work loop uses an internal time budget |

Evidence: [main functions](https://github.com/lambdawalker/go.attestra.aws.auth/blob/4607807ab0346f4a38532982889fe2e56954412e/infra/main.go), [capture](https://github.com/lambdawalker/go.attestra.aws.auth/blob/4607807ab0346f4a38532982889fe2e56954412e/infra/capture.go), [runtime](https://github.com/lambdawalker/go.attestra.aws.auth/blob/4607807ab0346f4a38532982889fe2e56954412e/infra/runtime.go), [reset](https://github.com/lambdawalker/go.attestra.aws.auth/blob/4607807ab0346f4a38532982889fe2e56954412e/infra/reset.go), [admin](https://github.com/lambdawalker/go.attestra.aws.auth/blob/4607807ab0346f4a38532982889fe2e56954412e/infra-index/admin.go), [index](https://github.com/lambdawalker/go.attestra.aws.auth/blob/4607807ab0346f4a38532982889fe2e56954412e/infra-index/main.go), [reset handler](https://github.com/lambdawalker/go.attestra.aws.auth/blob/4607807ab0346f4a38532982889fe2e56954412e/cmd/environment-reset/main.go).

Memory omitted in code is not a measured live memory setting. Inspect effective values before adopting them as managed configuration.

Capture currently has a shared deployment reservation setting applied to three functions. Default `-1` means shared account capacity in the tooling; zero is rejected. Production requires explicit choices and quota checks. Do not assume this is one reservation covering all three functions.

## 3. Settings worth opening after deployment

| Setting | Value to operator | Application mechanism | Recommendation |
|---|---|---|---|
| Memory MB | Tune performance, CPU allocation and cost | Native Lambda configuration | First increment, per-function bounds and before/after metrics |
| Timeout seconds | Adjust execution budget for observed workloads | Native Lambda configuration | First increment, constrained by caller and downstream budgets |
| Reserved concurrency | Protect dependencies and allocate/cap account capacity | Function-level concurrency API | First increment with account/quota/reset checks |
| SQS worker maximum concurrency | Limit parallel extraction and downstream load | Lambda event-source mapping adapter | First increment for the capture worker; coordinate with reservation |
| Safe application log verbosity | Diagnose incidents without exposing data | Supported structured logger + compatible Lambda logging controls or declared application reader | Early increment after logger capability is verified |
| Log retention | Balance investigation/data-retention requirements and storage cost | CloudWatch Logs adapter | Show as linked control; not a Lambda environment variable |
| Approved nonsecret property values | Adjust behavior/endpoints without source edits | Declared env/remote reader and coordinated change plan | Retain prior schema/source rules; no unrestricted env editor |
| External request timeouts / retry budget | Bound latency, amplification and provider cost | Declared application property, currently constants | Later increment after code supports the reader and total-budget tests |
| Extraction token budget | Bound output/cost within accepted quality | Declared application property, currently fixed at 4096 | Later, approved range and output-quality validation |
| Temporary storage MB | Support larger disk-staged processing | Native Lambda ephemeral storage | Advanced/conditional; current image path is memory-oriented, so no demonstrated need to increase /tmp |
| Scheduled async retry/event age | Bound retries of asynchronous scheduled invocation | Lambda async-invocation adapter; EventBridge delivery policy is separate | Advanced, source-specific; not a generic SQS retry slider |
| SQS mapping enable/pause | Stop new queue polling while investigating | Event-source mapping adapter with recovery workflow | Advanced privileged operation; does not cancel in-flight jobs |
| Provisioned concurrency | Reduce cold-start latency where measured need exists | Qualified version/alias configuration | Opt-in later; consumes paid capacity and requires release support |
| Approved secret/cache refresh policy | Balance rotation freshness and retrieval overhead | Secret-aware adapter | Follow key/secret migration plan; never allow stale/insecure fallback merely to save calls |

More memory allocates more CPU; the smallest memory allocation is not automatically the lowest total cost if duration changes. Use representative nonproduction measurements rather than guessing a universal optimum.

Reserved concurrency is different from provisioned concurrency. Reserving capacity does not prewarm execution environments. Native reservations affect the whole function across published versions; they are not an independent limit for each release alias. Mapping concurrency belongs to the selected mapping.

## 4. Caller-aware timeout validation

One global 1–900-second control would be misleading for these workloads.

- **HTTP handlers:** validate against the actual API Gateway integration and client deadline. HTTP API integration timeout is at most 30 seconds; a longer Lambda timeout does not make the client wait longer and may allow side effects after a client timeout.
- **Cognito challenge:** display the fixed five-second Cognito response deadline beside the declared ten-second Lambda timeout. Do not imply increasing Lambda timeout extends Cognito's deadline. Investigate p95/p99 work and provider retry behavior; fail proposed operating budgets that cannot fit the caller's envelope.
- **Capture worker:** preserve a budget for reading images, processing, inference, storing results and retries. Current inference request budget is 55 seconds under a 90-second Lambda timeout; changing only one constant is insufficient.
- **SQS coupling:** current queue visibility is 720 seconds. With no batch window, AWS's six-times recommendation supports up to 120 seconds by that inequality, not a blanket recommendation to set worker timeout to 120. Longer budgets require coordinated queue changes and a proven workload envelope.
- **Dispatcher/reset:** validate their own internal work budget and schedule overlap/idempotency, not HTTP-only constraints.
- **Internal callers:** reset control calls and SDK/HTTP clients have their own timeouts. Confirm whether an operation returns a job or waits synchronously before increasing a function budget.

The current Cognito discrepancy is an effective-deadline caveat, not proof of a live timeout incident or a reason to silently change infrastructure.

## 5. Source-specific candidates requiring code work

Current source includes values worth considering, but they are not configurable simply because the panel adds fields:

| Candidate | Current source behavior | Required groundwork |
|---|---|---|
| Inference request timeout | 55 seconds in context and HTTP client | One validated budget property, coordinated client/context construction |
| Inference max completion tokens | Fixed 4096 | Quality/cost bounds, response parsing and truncation/failure tests |
| Capture object HTTP timeout | 25 seconds | Operation-specific budget and retry envelope |
| Internal signed HTTP timeout | 10 seconds | Classify synchronous versus job-control calls before tuning |
| Email challenge lifetime | Ten minutes | Security/abuse policy, new-record snapshot semantics, in-flight transaction compatibility |
| Resend cooldown / resend count | 60 seconds / at most three resends in current path | Explicit abuse-control contract; public behavior and rate-budget tests |
| Worker application retry backoff | Attempt-based minute delays | Coordinate persisted due times, SQS receives/redrive and partial failures |
| Upload limits/lifetime and evidence retention | Policy/constants and stored record deadlines | Consent/policy identity, S3 cleanup/lifecycle and existing-record handling |

Evidence: [extractor](https://github.com/lambdawalker/go.attestra.aws.auth/blob/4607807ab0346f4a38532982889fe2e56954412e/awscapture/extractor.go), [capture transport](https://github.com/lambdawalker/go.attestra.aws.auth/blob/4607807ab0346f4a38532982889fe2e56954412e/awscapture/transport.go), [internal HTTP](https://github.com/lambdawalker/go.attestra.aws.auth/blob/4607807ab0346f4a38532982889fe2e56954412e/internal/awshttp/client.go), [email service](https://github.com/lambdawalker/go.attestra.aws.auth/blob/4607807ab0346f4a38532982889fe2e56954412e/email/service.go), [worker](https://github.com/lambdawalker/go.attestra.aws.auth/blob/4607807ab0346f4a38532982889fe2e56954412e/capture/worker.go), [capture service](https://github.com/lambdawalker/go.attestra.aws.auth/blob/4607807ab0346f4a38532982889fe2e56954412e/capture/service.go).

Do not put proof expiry, anti-abuse controls, retention or consent limits in the first general operations panel. They belong in a separate security/behavior change profile with stronger permissions and coordinated rollout. Code constants remain fixed until their runtime contracts and tests exist.

Keep model selection security-reviewed and tied to IAM/region availability; do not expose arbitrary inference URLs or model IDs as ordinary tuning.

## 6. Diagnostics and logging are different controls

`DIAGNOSTIC_MODE` is currently read into `email.Service.Diagnostics`. It changes whether some operational failures are returned rather than retaining generic public responses intended to reduce account-enumeration risk. It is **not merely a debug log switch**.

Initial policy:

- Keep diagnostic response mode off/locked in production.
- Do not relabel it as "verbose logs".
- If explicitly enabled in an isolated nonproduction environment, require a separate permission, audit and bounded expiry with an actual reversion mechanism.
- Never expose tokens, proof codes, secret values, image contents or raw sensitive request/response bodies.

For real log-level controls, these Go custom-runtime artifacts must declare a compatible logger capability. AWS application log filtering requires suitable JSON output with a level field; verify the logger pipeline and configure it deliberately. A native console setting alone does not prove existing text logs will be filtered as intended.

Log retention belongs to CloudWatch Logs. Configure an approved log group and required write permissions first; retain security/audit records according to policy. If implementing sampled diagnostics, audit/security records must not be sampled away.

## 7. Native controls versus runtime properties

The panel must label how a save is applied:

| Change category | Save operation | Scope / propagation |
|---|---|---|
| Memory, timeout, ephemeral storage, environment-backed properties | Function configuration update, then publication/activation if qualified releases are used | Version-specific configuration; no in-place edit to a published version |
| Reserved concurrency | Put/DeleteFunctionConcurrency | Whole function; shared/unreserved mode must be distinct from zero |
| Worker parallelism / pause | UpdateEventSourceMapping | One mapping; AWS state transition and in-flight work must be considered |
| Log retention | CloudWatch Logs update | Log group shared by all users of that group |
| Async retry/event-age policy | Qualified/unqualified invoke config as applicable | Applies to async Lambda invocation, not synchronous HTTP/Cognito or SQS polling |
| Approved dynamic property | Selected writer/source deployment | Defined cache/freshness/rotation semantics; not necessarily instant |
| Provisioned concurrency | Qualified version/alias update | Later release-aware capacity control with explicit cost |

The Lambda `MaximumRetryAttempts` asynchronous setting is not SQS redrive count. SQS retries involve queue visibility, receives/redrive, application jobs and partial-batch reporting. EventBridge target delivery retries are another layer. Expose the correct mechanism for each invocation profile.

Native changes should not add a configuration-store call to each business invocation. Application-level readers can use local values or bounded caches only when security/freshness constraints allow.

## 8. Proposed panel: two dashboard sections

The dashboard separates **Application settings** from **Artifact settings**. Lambda performance/capacity/log delivery and source bindings appear under Artifact settings. Logical feature values appear under Application settings, even when delivered through environment variables. Separate backend permissions apply; app editing rights do not imply Lambda/IAM write rights.

Risk is independent of section: diagnostic response mode, proof lifetime, abuse limits and consent are security-sensitive application settings. They remain restricted or read-only until their specific change workflow exists. The source binding/secret reader is configured under Artifact settings; approved value editing uses the Application settings workflow without creating a second writer.

### Artifact settings / Lambda

**Target header:** application, environment/shared scope, logical function, account/region, invocation profile, active target/version, code hash and desired/applied/observed config revision.

**Performance:** current/requested memory and timeout, caller deadline, downstream budget, and available duration/memory/error/throttle metrics. Show unknown when metrics are absent; do not fabricate recommendations.

**Capacity:** shared-account or reserved mode, current reservation, applicable mapping maximum, account availability and dependency limits. Label whether the change affects all releases.

**Observability:** supported log verbosity, linked log-retention control and expiry for temporary diagnostics. Public diagnostic response mode stays separately restricted.

**Source bindings:** only the artifact's approved schema; reader location, cache/refresh policy and secret references/status belong here. No arbitrary env names/values or IAM edits. Provide a link to the approved logical value in Application settings.

**Advanced:** eligible async policies, mapping pause/resume and temporary storage. Provisioned concurrency remains hidden until release/alias capability and cost policy are available.

**Review/apply:** exact diff, coupled changes, propagation/restart effects, scope/blast radius, estimated cost assumptions, durable job progress and auditable history.

### Application settings / feature

Show approved feature behavior values and business-service URLs under their feature, with type/constraints, current value or protected replacement control, revision, history and impact. Onboarding modes, password rules and disclosure text use the existing runtime-policy contract; do not duplicate them in a generic Lambda env editor. Display the selected delivery source and propagation method read-only, with a link to Artifact settings for authorized operators. Security-sensitive application controls require their own permissions and compatible-change checks.

No default "invoke a sample request" button for state-changing production functions: authentication/capture/reset can send email, create records, run inference or delete data. Benchmarks/smoke checks need safe fixtures, a controlled environment and explicit operation scope.

## 9. Change workflow, ownership and permissions

1. Resolve target from trusted deployment inventory, never a browser-supplied arbitrary ARN.
2. Authorize environment/shared scope and operation category. Ordinary runtime publishers do not automatically get concurrency or infrastructure rights.
3. Load observed configuration, code identity and managed registry revision; detect drift.
4. Validate property coverage, source support, bounds, caller/queue capacity, reset status and deployment locks.
5. Record a durable job and baseline. Serialize with CI/deployment and reset operations.
6. Apply only allowlisted changes with appropriate revision protection; preserve unrelated environment/configuration fields.
7. Wait for update/mapping status, publish/activate deliberately when supported, and verify the intended code/configuration target.
8. Record applied and observed revision plus partial-failure checkpoints; offer conflict-aware rollback.

Attestra's reset workflow manipulates function concurrency. Panel changes must coordinate with that workflow rather than overwrite its temporary shutdown or be overwritten by its restore. Block or defer capacity edits while reset owns the function.

Use a configuration worker role with scoped read/update actions, and separate concurrency/mapping/logging capabilities. Do not give browser code AWS credentials or let a broad Lambda configuration API become a route to changing execution role, VPC, layers or security fields.

One authoritative registry owns adopted mutable fields. The deployment adapter reads those values on later Pulumi runs, preserving overrides. Source constants are bootstrap defaults, not values to reapply after every operator edit. Avoid blanket ignored-resource ownership or two independent writers.

Current unqualified function routing means a native update can affect active traffic without release isolation. Begin in nonproduction; make that impact explicit. A production release-safe save requires published-version/alias ownership or another explicitly reviewed rollout strategy. Do not claim old clients retain their exact backend configuration until that exists.

Reserved concurrency/mapping changes are not rolled back by merely moving a Lambda alias. A rollback plan must restore each affected scope with concurrency checks and avoid clobbering newer changes.

## 10. Limits and controls not for routine editing

Keep these deployment/security-controlled: runtime and architecture, code package, execution role/policies, VPC/networking, layers/extensions, function URL/public access, resource identities, token verification boundaries and secret/key provider migrations.

Do not offer emergency "disable" through an accidental concurrency value of zero. A deliberate privileged pause needs an explicit action, impact on queued/in-flight work, ownership lease, audit and independent recovery. Shared admin/index/reset controls require stronger safeguards to avoid disabling the system that restores them.

Changing timeout/memory is not evidence of a performance improvement. Higher memory, paid warm capacity, additional /tmp, retries and log volume need measured cost assumptions; security constraints remain mandatory.

## 11. Delivery plan and verification

**Increment 1:** declare per-function operating profiles and adopt memory/timeout inspection and configuration ownership; expose environment-function controls with caller-aware bounds, durable worker updates and deployment preservation.

**Increment 2:** add reserved/mapping concurrency with production quotas, reset coordination, explicit pause/recovery and correct shared/version scope.

**Increment 3:** establish structured/redacted Go logging, safe verbosity/retention controls, and metrics-based comparison.

**Increment 4:** introduce selected application tuning contracts after code support: inference timeout/token budgets and safe remote-client budgets first. Keep expiry/abuse/consent controls in their security-reviewed profile.

**Later:** add optional version/alias provisioned capacity and source-specific asynchronous retry controls only where the invocation model and workload justify them.

Required tests: missing/unknown mappings; unsupported fields; invalid memory/timeout; caller deadline violation; queue/batch-window timeout coupling; quota/reservation/mapping conflict; separate shared authorization; application-versus-artifact permission boundaries and risk classification; reset race; stale revision/code hash; failed update/publication and partial rollback; no accidental zero reservation; production diagnostic rejection; custom-runtime log filtering/redaction; secret unavailability/rotation; cache freshness; async-versus-SQS policy selection; and preservation of panel-managed values on later deployment.

No AWS update, benchmarking, application invocation or implementation change is performed by this plan.

## 12. References

- [Lambda memory and CPU](https://docs.aws.amazon.com/lambda/latest/dg/configuration-memory.html)
- [Lambda timeout](https://docs.aws.amazon.com/lambda/latest/dg/configuration-timeout.html)
- [Reserved concurrency](https://docs.aws.amazon.com/lambda/latest/dg/configuration-concurrency.html)
- [Ephemeral storage](https://docs.aws.amazon.com/lambda/latest/dg/configuration-ephemeral-storage.html)
- [Environment variables and version immutability](https://docs.aws.amazon.com/lambda/latest/dg/configuration-envvars.html)
- [Custom-runtime log-level filtering](https://docs.aws.amazon.com/lambda/latest/dg/monitoring-cloudwatchlogs-log-level.html)
- [Cognito trigger response deadline](https://docs.aws.amazon.com/cognito/latest/developerguide/cognito-user-pools-working-with-lambda-triggers.html)
- [HTTP API timeout quota](https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-quotas.html)
- [SQS mapping configuration](https://docs.aws.amazon.com/lambda/latest/dg/services-sqs-configure.html)
- [SQS invocation error handling](https://docs.aws.amazon.com/lambda/latest/dg/services-sqs-errorhandling.html)
