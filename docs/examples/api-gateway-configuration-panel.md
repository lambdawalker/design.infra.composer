# API Gateway: post-deployment configuration and custom-panel plan

## 1. Scope

This is the next artifact-specific plan after Lambda, applying the [configuration rules](../configuration-and-administration.md) to Attestra's **API Gateway HTTP APIs**. It is a proposal, not implemented functionality. No infrastructure or Attestra source code is changed.

Source snapshot: [go.attestra.aws.auth 4607807](https://github.com/lambdawalker/go.attestra.aws.auth/commit/4607807ab0346f4a38532982889fe2e56954412e), reviewed 2026-11-01. See the [full artifact inventory](attestra-configuration-plan.md).

API Gateway is a managed resource: it does not read environment variables or AWS AppConfig to discover these settings. The framework stores desired configuration and applies it through the API Gateway management adapter.

## 2. Current settings from source

| API binding | Scope | Current default throttle | Current browser policy |
|---|---|---|---|
| Environment API, logical `email-http-api` | One selected backend environment | 10 requests/second; burst bucket capacity 20 | Selected app origin; GET/POST; content-type/authorization; preflight cache 300 seconds |
| Shared index, `index-api` | Shared control plane | 10 requests/second; burst 20 | Public GET discovery with origin wildcard; preflight cache 300 seconds |
| Shared admin, `admin-api` | Shared control plane | 5 requests/second; burst 10 | No gateway CORS configuration declared; console uses same-origin APIs |

All three declare an auto-deployed `$default` stage. They use Lambda proxy integrations. Protected capture/admin routes use JWT authorizers; index publication uses AWS_IAM, while intended reads/assets remain public.

Evidence: [environment API/stage](https://github.com/lambdawalker/go.attestra.aws.auth/blob/4607807ab0346f4a38532982889fe2e56954412e/infra/main.go), [capture authorization](https://github.com/lambdawalker/go.attestra.aws.auth/blob/4607807ab0346f4a38532982889fe2e56954412e/infra/capture.go), [shared index](https://github.com/lambdawalker/go.attestra.aws.auth/blob/4607807ab0346f4a38532982889fe2e56954412e/infra-index/main.go), [shared admin](https://github.com/lambdawalker/go.attestra.aws.auth/blob/4607807ab0346f4a38532982889fe2e56954412e/infra-index/admin.go), [API domain mapping](https://github.com/lambdawalker/go.attestra.aws.auth/blob/4607807ab0346f4a38532982889fe2e56954412e/infra/api_domain.go).

These are source defaults, not verified current cloud values. CORS belongs to the API and can affect every stage; throttles in this plan belong to the selected stage/routes. Retained Lambda releases behind the same API/stage share these settings: a panel must not advertise per-release isolation unless separate API/stage bindings actually provide it. No stage access-log configuration is declared in these files; Lambda execution logs are a separate concern.

## 3. What is worth exposing

| Property | Value after deployment | Recommended exposure |
|---|---|---|
| Stage default steady request rate | Adjust traffic pressure as usage changes | First panel version, infrastructure-operator permission |
| Stage default burst capacity | Accommodate short spikes while controlling downstream pressure | First panel version, paired with rate |
| Existing-route throttle overrides | Lower targets for costly capture/auth work and different discovery behavior | Second increment; choose declared routes only, show inheritance and removal |
| Environment API allowed browser origins | Add/remove approved web-client origins without editing application code | First version as a privileged change with stricter review |
| CORS preflight cache duration | Tune browser policy propagation versus preflight requests | Advanced increment; visible current value and effect |
| Approved CORS request/exposed headers | Support explicitly declared client protocols such as policy-revision headers | Advanced increment; require client/header contract, not arbitrary wildcards |
| Access logging enablement/approved format | Improve diagnosis and response to incidents | Separate opt-in increment after log destination, access, retention and redaction are provisioned |
| Monitoring readouts | Show 429s, latency and error counts around changes | Read-only where approved metric permissions/data are available |

The burst value is token-bucket capacity, not a promise of concurrent Lambda executions. API Gateway throttles are best-effort targets, not strict security, spending, per-user, or per-IP ceilings. Backend admission/rate controls and authentication remain separate.

For the initial panel, keep methods GET/POST and required content-type/authorization headers fixed for the environment API; do not expose arbitrary method/header removal.

Preserve the index's intentional public GET wildcard without treating it as a defect. Its CORS policy does not authorize IAM-protected writes. Keep index-origin-policy changes and admin CORS changes deployment/security-reviewed rather than routine settings.

CORS controls browsers, not native Android clients or general API callers. Adding an origin does not update Cognito callbacks, passkey relying-party settings, or the backend's own Origin checks; validate those dependencies separately.

## 4. Settings excluded from routine editing

Show these as read-only with links to a deployment/change workflow:

- Route creation/deletion/path changes, integration targets and Lambda invocation permissions.
- JWT issuer, audiences, required scopes, authorizer assignment and authorization mode.
- TLS/custom domains, certificates, DNS and API mappings.
- API protocol, stage identity and auto-deploy mode.
- Disabling the default endpoint, unless a separate domain-readiness/migration plan is completed.
- Resource IDs, account/region and environment/shared ownership.
- Account-level service quotas; a panel cannot manufacture more account capacity.
- Usage plans/API-key quotas or REST-only caching/tracing controls; do not promise REST API features for these HTTP APIs.

Throttling is not maintenance mode. Do not implement shutdown by interpreting zero rate/burst as a convenient toggle. If maintenance is needed, give it a separate artifact/application-level contract and recovery plan.

## 5. Property contract and application binding

Example proposed property declarations:

```python
gateway.configuration.number(
    "default_rate_rps", required=True, minimum_exclusive=0,
)
gateway.configuration.integer(
    "default_burst", required=True, minimum=1,
)
gateway.configuration.origins(
    "cors_origins", required=True,
)
```

The origins property applies only to API bindings that explicitly expose it. Do not require an origins mapping for the current same-origin admin API.

Example application binding:

```python
app.configure_artifact(
    gateway,
    properties={
        "default_rate_rps": ManagedResourceProperty(
            adapter="aws.apigatewayv2.stage",
            field="DefaultRouteSettings.ThrottlingRateLimit",
            initial_value=10,
        ),
        "default_burst": ManagedResourceProperty(
            adapter="aws.apigatewayv2.stage",
            field="DefaultRouteSettings.ThrottlingBurstLimit",
            initial_value=20,
        ),
        "cors_origins": ManagedResourceProperty(
            adapter="aws.apigatewayv2.api",
            field="CorsConfiguration.AllowOrigins",
            initial_value=[app.web_origin],
        ),
    },
    configuration_owner="application",
)
```

This is pseudocode, not an available adapter. The framework resolves API/stage IDs from trusted deployment inventory and binds them to account, region, application, environment/shared scope and an allowed field set. Browser input supplies logical property values, never arbitrary AWS IDs, ARNs, patch operations, or resource targets.

Initial values seed management once. Later deployments must preserve applied administrator settings rather than resubmit source constants. Required mapping gaps, wrong scopes, unsupported properties or absent worker access block adoption/deployment.

## 6. Custom-panel flow

The application owns the panel by default. A feature's optional standalone panel uses the same backend contract and is suppressed inside an app-owned configuration deployment.

1. **Select target:** application, account/region, environment API or explicitly shared index/admin resource.
2. **Load observed and managed values:** show source defaults, applied desired revision, observed AWS state and any drift/pending job.
3. **Traffic controls:** rate and burst with units, inherited route defaults, optional advanced overrides.
4. **Browser access:** approved origins only where allowed; explain CORS scope and cached preflights.
5. **Review diff:** show exactly which properties change, affected APIs/routes and shared impact.
6. **Submit change:** record expected configuration revision and baseline hash, then create a durable job.
7. **Observe result:** queued, validating, applying, verifying, applied, failed, or drift/conflict. Display which steps changed if only part succeeds.
8. **History/restore:** restore a previous setting set as a new change against current state, not an unaudited blind rollback.

A grant for one backend environment does not authorize editing shared admin/index gateways. Existing Attestra grant-manager rights also do not automatically imply infrastructure-operator rights; add explicit actions/scopes.

Changing the admin API can lock out its own UI through excessive throttling or browser policy mistakes. Require an operator-defined minimum safe profile, approved origins/fields, and an independent CLI/worker recovery path before exposing those changes. Default first rollout targets only the environment API.

## 7. Write path and credentials

Proposed path:

**Panel request → configuration API authorization/validation → durable change record/job → scoped worker → API Gateway management API → read-back and smoke checks.**

Use `GetApi`, `GetStage` and route inventory for inspection; `UpdateStage` for default/route throttles and `UpdateApi` for allowed CORS fields. HTTP APIs are already auto-deployed; apply changes with this behavior in mind. Do not tell the user that edits wait for a separate manual deployment.

The selected fields are stored/applied natively in API Gateway. Application Lambda invocations need no extra database/AppConfig lookup to enforce gateway throttling or produce gateway CORS headers.

Provision a worker identity with only the necessary API Gateway management GET/PATCH access on registered API/stage paths. Add route-list access only for the route-override capability. IAM can authorize a broader native resource update than one property, so enforce the exact field allowlist in the backend too.

The browser receives no AWS credentials. Keep the existing admin Lambda's authority narrow; submitting a job does not require granting it unrestricted gateway modification. Any log/metric permissions in a later increment must be separately scoped.

## 8. Validation and coupled constraints

- Rate is finite and positive; burst is a positive integer. Apply operator-approved lower/upper bounds and available regional/account quotas. Do not hard-code one worldwide account quota.
- A route override must identify an existing authorized route in the selected API/stage. Removing an override restores inheritance, not zero.
- Show backend Lambda concurrency and expensive-operation implications when raising rates; do not equate request rates and concurrency.
- Environment origins must be approved exact HTTPS origins without credentials, paths, queries or fragments. Local development exceptions require explicit nonproduction policy.
- Retain required methods/headers and reject credentialed wildcard-origin combinations. Credentials mode is not an editable initial-panel control.
- Validate backend Origin allowlists, OAuth redirects, passkey domains and CSP dependencies where applicable. CORS alone cannot establish support for an added web application.
- Existing cached preflight responses can outlive a CORS edit; represent this propagation window honestly.
- Keep public index/read behavior, IAM publication and JWT protections unchanged.
- Reject stale desired revisions and changed target identities before mutation.
- Shared edits require shared-resource permission and clearly identify their impact.
- A logging expansion must use an approved destination/format that omits bodies, tokens, authorization headers, proof codes and sensitive query data.

Do not move these properties into the current public `/v1/app-config` document or allow its existing runtime-publish endpoint to mutate infrastructure.

## 9. Ownership, concurrency and partial failure

The current code hard-codes gateway defaults in Pulumi. Before enabling panel writes, introduce one authoritative managed-property registry and a common coordinator used by admin, CI and deployment.

Recommended ownership model:

- Pulumi continues to own gateway resource identity and fixed infrastructure/security properties.
- The registry owns adopted mutable fields after initialization.
- The native change worker and deployment adapter both consume the same validated registry and coordinate writes.
- Every future Pulumi run resolves the managed fields from that authority, preserving admin overrides.
- Legacy deployment paths that cannot honor ownership must be rejected or explicitly reconciled before changes are enabled.

Do not solve this with a blanket `ignoreChanges` over an entire API/stage, or by having a later deployment restore stale defaults.

Use a durable per-target lease, internal configuration revisions and a normalized observed-state hash. The baseline hash is an application conflict check, not an AWS atomic compare-and-swap guarantee: external console/API writers can still race. Read back, detect drift, and reconcile explicitly.

CORS and stage throttle updates are separate native calls and are not one transaction. Preserve unrelated CORS/default/route fields, record a checkpoint per step, retry idempotently, and distinguish desired, applied and observed state. Report partial application instead of pretending an all-or-nothing save occurred.

Rollback must confirm that the target has not changed since this job applied its values. Do not overwrite a newer operator's change. Read-back verifies control-plane state; controlled HTTP tests provide separate evidence of data-plane behavior.

## 10. Incremental delivery and verification

### Increment 1: environment API throttles and approved origins

- Declare the environment gateway's properties, consumers/targets, defaults, ownership and source snapshot.
- Add native inspection/update adapter behind the configuration coordinator.
- Add scoped operator authorization, durable jobs and revision/drift checks.
- Build custom controls, review diff, progress/status, history and recovery instructions.
- Verify that a later environment deployment preserves panel-managed values.

### Increment 2: route overrides and shared-resource profiles

- Add declared-route inventory, inheritance/reset controls and approved bounds.
- Add explicit shared index/admin rights and shared-impact UI.
- Test index publication and administrator recovery before offering shared writes.

### Increment 3: optional diagnostics

- Provision approved access-log destination/retention and read-only metric views.
- Validate log format and privacy; avoid assuming Lambda logs already provide API access logs.

Local tests should cover schema gaps, invalid values, origin normalization, route inheritance, rejected arbitrary targets/fields, separate shared authorization, missing worker permissions, baseline drift, concurrent jobs, partial CORS/stage failure, idempotent retries, safe rollback and preservation across Pulumi redeployment.

Future authorized smoke tests should check allowed/denied browser preflights with actual Origin/request-method headers, intended GET/POST behavior, JWT/IAM protections and recovery paths. Do not use a production load test to promise an exact best-effort throttle ceiling.

No panel, worker, permissions or smoke deployment is implemented or executed by this plan.

## 11. Provider references

- [HTTP API throttling and best-effort semantics](https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-throttling.html)
- [Regional/account quotas](https://docs.aws.amazon.com/apigateway/latest/developerguide/limits.html)
- [HTTP API CORS](https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-cors.html)
- [API Gateway v2 stage read/update](https://docs.aws.amazon.com/apigatewayv2/latest/api-reference/apis-apiid-stages-stagename.html)
- [API Gateway v2 API read/update](https://docs.aws.amazon.com/apigatewayv2/latest/api-reference/apis-apiid.html)
