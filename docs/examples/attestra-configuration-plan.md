# Attestra AWS Auth: artifact inventory and configuration plan

## 1. Scope and evidence

Reviewed [go.attestra.aws.auth](https://github.com/lambdawalker/go.attestra.aws.auth/blob/4607807ab0346f4a38532982889fe2e56954412e/README.md) at commit [4607807](https://github.com/lambdawalker/go.attestra.aws.auth/commit/4607807ab0346f4a38532982889fe2e56954412e) on 2026-11-01.

This is a source review and proposed application of the [configuration rules](../configuration-and-administration.md). It is not a live AWS inventory, security certification, deployment, or implementation change. Resource counts below describe declarations in this snapshot; optional settings and deployment progress determine actual resources.

Source behavior takes precedence over older prose. The repository's own [service inventory](https://github.com/lambdawalker/go.attestra.aws.auth/blob/4607807ab0346f4a38532982889fe2e56954412e/docs/agents/aws-services.md) is helpful but records an older reviewed revision.

Important terminology: the repository's `app-config` Lambda and `GET /v1/app-config` route are its own DynamoDB-backed runtime configuration API. They are **not AWS AppConfig**.

This repository provisions/uses five configuration mechanisms already: Lambda environment variables, Pulumi settings (including a marked secret), strongly consistent DynamoDB runtime records, AWS service configuration, and a deployment credential vault. AWS AppConfig, Secrets Manager and Parameter Store are proposed providers, not currently provisioned by the reviewed stacks.

## 2. Artifact inventory

| Type | Current use | Ownership / evidence |
|---|---|---|
| Lambda functions and ZIP artifacts | Authentication, Cognito challenge, capture/dispatch/extraction, public configuration, reset, shared admin/index; Go custom runtime `provided.al2023`, ARM64 | [Environment](https://github.com/lambdawalker/go.attestra.aws.auth/blob/4607807ab0346f4a38532982889fe2e56954412e/infra/main.go), [capture](https://github.com/lambdawalker/go.attestra.aws.auth/blob/4607807ab0346f4a38532982889fe2e56954412e/infra/capture.go), [runtime](https://github.com/lambdawalker/go.attestra.aws.auth/blob/4607807ab0346f4a38532982889fe2e56954412e/infra/runtime.go), [reset](https://github.com/lambdawalker/go.attestra.aws.auth/blob/4607807ab0346f4a38532982889fe2e56954412e/infra/reset.go), [shared](https://github.com/lambdawalker/go.attestra.aws.auth/blob/4607807ab0346f4a38532982889fe2e56954412e/infra-index/main.go), [admin](https://github.com/lambdawalker/go.attestra.aws.auth/blob/4607807ab0346f4a38532982889fe2e56954412e/infra-index/admin.go) |
| API Gateway HTTP APIs | Three APIs: environment, shared index, shared admin; proxy integrations, routes/stages, JWT or IAM controls where declared | Same environment/shared infrastructure files |
| Cognito identity resources | Application user pool/public client; separate administrator pool/client, managed login domain/branding | [Application](https://github.com/lambdawalker/go.attestra.aws.auth/blob/4607807ab0346f4a38532982889fe2e56954412e/infra/main.go), [admin](https://github.com/lambdawalker/go.attestra.aws.auth/blob/4607807ab0346f4a38532982889fe2e56954412e/infra-index/admin.go), [SDK setup](https://github.com/lambdawalker/go.attestra.aws.auth/blob/4607807ab0346f4a38532982889fe2e56954412e/adminsetup/setup.go) |
| DynamoDB tables/indexes | Five logical tables: proofs, captures, reset control, environment registry, admin/runtime configuration; capture work-due GSI; TTL where applicable | [Environment](https://github.com/lambdawalker/go.attestra.aws.auth/blob/4607807ab0346f4a38532982889fe2e56954412e/infra/main.go), [capture](https://github.com/lambdawalker/go.attestra.aws.auth/blob/4607807ab0346f4a38532982889fe2e56954412e/infra/capture.go), [reset](https://github.com/lambdawalker/go.attestra.aws.auth/blob/4607807ab0346f4a38532982889fe2e56954412e/infra/reset.go), [shared](https://github.com/lambdawalker/go.attestra.aws.auth/blob/4607807ab0346f4a38532982889fe2e56954412e/infra-index/main.go), [runtime store](https://github.com/lambdawalker/go.attestra.aws.auth/blob/4607807ab0346f4a38532982889fe2e56954412e/runtimeconfig/store.go) |
| S3 buckets/objects/policies | Private versioned capture evidence; setup-managed private versioned Pulumi state; optional Android association asset bucket | [Capture](https://github.com/lambdawalker/go.attestra.aws.auth/blob/4607807ab0346f4a38532982889fe2e56954412e/infra/capture.go), [setup](https://github.com/lambdawalker/go.attestra.aws.auth/blob/4607807ab0346f4a38532982889fe2e56954412e/tools/deploy/internal/workflow/bootstrap.go), [associations](https://github.com/lambdawalker/go.attestra.aws.auth/blob/4607807ab0346f4a38532982889fe2e56954412e/infra/assetlinks.go) |
| SQS queues and Lambda event-source mapping | Capture queue plus DLQ; worker batches of one, partial failure reporting, maximum concurrency | [Capture](https://github.com/lambdawalker/go.attestra.aws.auth/blob/4607807ab0346f4a38532982889fe2e56954412e/infra/capture.go) |
| EventBridge rules/targets | Minute-based capture dispatch sweep and environment reset work | [Capture](https://github.com/lambdawalker/go.attestra.aws.auth/blob/4607807ab0346f4a38532982889fe2e56954412e/infra/capture.go), [reset](https://github.com/lambdawalker/go.attestra.aws.auth/blob/4607807ab0346f4a38532982889fe2e56954412e/infra/reset.go); these are rules, not EventBridge Scheduler resources |
| CloudWatch logging and alarm | Lambda logs; alarm for visible messages in the capture DLQ | [Capture](https://github.com/lambdawalker/go.attestra.aws.auth/blob/4607807ab0346f4a38532982889fe2e56954412e/infra/capture.go); explicit log retention and alarm notification actions are not declared there |
| SES identity/DKIM and email calls | Verified sender domain, email delivery, Cognito developer email configuration | [Infrastructure](https://github.com/lambdawalker/go.attestra.aws.auth/blob/4607807ab0346f4a38532982889fe2e56954412e/infra/main.go), [sender](https://github.com/lambdawalker/go.attestra.aws.auth/blob/4607807ab0346f4a38532982889fe2e56954412e/awsemail/sender.go) |
| Bedrock Mantle inference dependency | Worker calls regional SigV4 chat-completions API using a fixed model; no external model API token | [Extractor](https://github.com/lambdawalker/go.attestra.aws.auth/blob/4607807ab0346f4a38532982889fe2e56954412e/awscapture/extractor.go), [worker IAM](https://github.com/lambdawalker/go.attestra.aws.auth/blob/4607807ab0346f4a38532982889fe2e56954412e/infra/capture.go); accessed service, not a model provisioned by this stack |
| ACM certificates and validation | Regional API/index/admin domains; optional association-site CloudFront certificate in us-east-1 | [API domain](https://github.com/lambdawalker/go.attestra.aws.auth/blob/4607807ab0346f4a38532982889fe2e56954412e/infra/api_domain.go), shared stack, [associations](https://github.com/lambdawalker/go.attestra.aws.auth/blob/4607807ab0346f4a38532982889fe2e56954412e/infra/assetlinks.go) |
| DNS records/providers | Optional Route 53 records; deployment wizard also supports Cloudflare | [Infrastructure](https://github.com/lambdawalker/go.attestra.aws.auth/blob/4607807ab0346f4a38532982889fe2e56954412e/infra/main.go), [Cloudflare adapter](https://github.com/lambdawalker/go.attestra.aws.auth/blob/4607807ab0346f4a38532982889fe2e56954412e/tools/deploy/internal/dns/cloudflare.go) |
| CloudFront/OAC, optional | Android Digital Asset Links hosting backed by private S3; not the current admin UI host | [Associations](https://github.com/lambdawalker/go.attestra.aws.auth/blob/4607807ab0346f4a38532982889fe2e56954412e/infra/assetlinks.go) |
| IAM roles/policies and OIDC trust | Per-function execution access, API invocation, deployment and GitHub environment-bound access | Environment/shared files; [deployment permissions](https://github.com/lambdawalker/go.attestra.aws.auth/blob/4607807ab0346f4a38532982889fe2e56954412e/tools/deploy/internal/workflow/aws_setup_policy.go) |
| Web assets and public documents | Admin HTML/JS/CSS embedded in its Lambda; index JSON; public runtime config; optional assetlinks.json | [Embedded assets](https://github.com/lambdawalker/go.attestra.aws.auth/blob/4607807ab0346f4a38532982889fe2e56954412e/adminapi/assets.go), [admin handler](https://github.com/lambdawalker/go.attestra.aws.auth/blob/4607807ab0346f4a38532982889fe2e56954412e/adminapi/handler.go), [registry](https://github.com/lambdawalker/go.attestra.aws.auth/blob/4607807ab0346f4a38532982889fe2e56954412e/registry/registry.go), [public config](https://github.com/lambdawalker/go.attestra.aws.auth/blob/4607807ab0346f4a38532982889fe2e56954412e/runtimeconfig/api.go) |
| Deployment/operations artifacts | Go setup/deployment tooling, local encrypted credentials, Pulumi state/configuration, GitHub workflow settings | [Wizard](https://github.com/lambdawalker/go.attestra.aws.auth/blob/4607807ab0346f4a38532982889fe2e56954412e/tools/deploy/internal/workflow/bootstrap.go), [vault](https://github.com/lambdawalker/go.attestra.aws.auth/blob/4607807ab0346f4a38532982889fe2e56954412e/tools/deploy/internal/vault/credential_vault.go), [workflow](https://github.com/lambdawalker/go.attestra.aws.auth/blob/4607807ab0346f4a38532982889fe2e56954412e/.github/workflows/deploy.yml) |

No RDS/relational database, EC2/ECS workload, or external database password is declared in the reviewed application stacks. DynamoDB, S3, SQS, SES and Bedrock access use role credentials rather than invented static service passwords. A customer-managed KMS key is not created by these stacks; tooling can recognize existing state-bucket KMS encryption and grant access. Account-level resources may exist independently.

### Lambda declaration groups

| Group | Logical functions / artifacts |
|---|---|
| Email verification | `email-signup`, `email-resend`, `email-confirm` |
| Cognito challenge | `cognito-grant-challenge` |
| Passkey registration | `passkeyoptions`, `passkeycomplete` |
| Sign-in / enrollment | `auth-email-start`, `auth-email-complete`, `auth-passkey-start`, `auth-passkey-complete`, `auth-refresh`, `auth-status`, `auth-password-start`, `auth-password-complete`, `auth-password-set` |
| Capture | `capture`, `capture-dispatcher`, `capture-worker` |
| Environment configuration/operations | `app-config`, `environment-reset` |
| Shared control plane | `index-handler`, `admin-handler` |

The environment declares 20 functions and the shared stack another two. The reviewed code does not declare Lambda published-version/alias routing. Retained releases and alias activation in the framework are future capabilities, not current repository behavior.

## 3. Selection rules for this application

For every property and consumer, enforce security/correctness constraints first, prefer applicable AWS guidance next, and compare cost only among eligible choices.

Separate four kinds of value:

1. **Resource bindings:** IDs, table names, queue URLs, bucket names and issuers. Usually immutable deployment references delivered locally through nonsecret environment variables.
2. **Application configuration:** onboarding/capture behavior, disclosures, optional operational tuning. Current authority is the runtime table or code; freshness determines whether a cached source is eligible.
3. **Secrets / cryptographic operations:** proof-key material and operator tokens. Use protected providers; do not treat these as public runtime settings.
4. **Managed-resource configuration:** pool policies, queue attributes, storage lifecycle, domains, capacity and permissions. Applied by service/deployment adapters; resources do not read these from AppConfig.

Business records (proofs, challenge transactions, captures, grants, leases, reset state and audit history) remain in transactional storage. They must not be migrated wholesale into AppConfig.

### Dashboard classification

The admin dashboard separates **Application settings** (feature behavior and logical property values) from **Artifact settings** (execution/infrastructure and source bindings). Store choice does not decide the category: an env-backed feature value is still application configuration. Separate server-side permissions apply; security-sensitive application settings remain restricted. See the [two-section dashboard rules](../configuration-and-administration.md).

## 4. Per-artifact configuration plan

| Artifact type | Exposed configuration candidates | Read / application method | Change owner and access |
|---|---|---|---|
| Lambda | Nonsecret resource IDs, origins, sender, route selectors; code/runtime/memory/timeout/concurrency; secret references | Environment reader for deployment bindings; secret-aware reader for credentials; dynamic reader only where freshness permits; native function configuration for execution settings | Deployment/configuration worker owns full function map and rollout; execution role gets source-specific read access, never administrative write access |
| API Gateway | CORS origins, throttles, route/integration targets, JWT issuer/audiences, domain mapping | API Gateway/Pulumi adapter; authorizers and gateway settings are native resource properties | Deployment worker; app admin may submit validated change jobs, not arbitrary gateway edits |
| Cognito | Pool security baseline, MFA/passkeys, permitted factors, OAuth callbacks/token lifetime, client configuration | Cognito/Pulumi adapter with SDK-owned fields explicitly separated | Identity/deployment operator role; preserve separate admin/application boundaries and unrelated settings; replacement-only properties require migration |
| DynamoDB | Capacity/billing, PITR, encryption policy, TTL attribute, deletion protection, GSI/schema changes | DynamoDB/Pulumi adapter for table settings; SDK operations for application records | Infrastructure worker owns table properties; application roles only required record actions; schema/key changes may need migration/replacement |
| S3 | Evidence lifecycle, versioning, encryption/public-access/TLS policies; association object contents; state retention | S3/Pulumi adapter; object publisher for controlled documents | Separate evidence, association and state ownership; do not let an ordinary config editor weaken storage controls or delete state |
| SQS / event-source mapping | Visibility, redrive count/DLQ, retention, worker batch/concurrency | SQS/Lambda deployment adapter | Queue/deployment worker; coordinate with function timeout, retries and account capacity; policy edit is not a queue purge |
| EventBridge rule/target | Schedule, enablement, selected target and input | EventBridge/Pulumi adapter | Deployment worker; avoid using a rule edit as an unaudited reset-start mechanism |
| CloudWatch | Log retention/redaction, alarm threshold and approved notification destination | Logs/CloudWatch adapter | Operations/deployment worker; missing alarm destination should be visible in production readiness |
| SES | Verified sender domain/address, DKIM/DNS bindings | SES + DNS + IAM + Cognito/deployment adapters | Email/deployment operator; read back readiness; application keeps SES role credentials, not SMTP/API keys |
| Bedrock dependency | Approved region/model, timeout and token budget if deliberately exposed | Role/SigV4 service client; local deployment-bound tuning by default, provider adapter for access/model allowlist | Deployment worker coordinates reader configuration and IAM model restriction; do not permit arbitrary model endpoints or secret-bearing URLs |
| ACM / DNS | Hostnames, zone/provider ownership, validation records, certificate-region requirements | ACM and Route 53/Cloudflare deployment adapters | DNS/certificate operator; provider tokens stay in protected deployment credentials; wait for validation/readiness |
| CloudFront / association assets | Origin/OAC, TLS/cache policy, allowed Android package/certificate associations | CloudFront/S3/DNS adapter and versioned JSON publisher | Deployment owner; explicit association revocation and cache propagation; security baseline not editable by unprivileged runtime config users |
| IAM / OIDC | Execution read access, writer actions, repository/environment trust and explicit external roles | IAM/provider policy adapter and effective-access checks | Bootstrap/security operator; normal feature configuration cannot grant itself more privileges |
| Admin/index web artifacts | Public bootstrap issuer/client/origin, environment discovery, permitted UI metadata | Nonsecret validated bootstrap document/local values; configuration API for mutable properties | Application owns integrated configuration UI by default; suppress feature standalone panels; public projection excludes credentials and private inventory |
| Deployment tooling/state | Account/region, env/stack/backend, DNS/CI credential references, unlock mechanism | Encrypted vault + supported credential chain/SSO/OIDC + provider backend | Operator/CI identities; keep local vault separate from shared state and live application secrets |

These are contracts to introduce. A candidate being listed does not mean it is configurable today, safe to edit live, or visible to every administrator.

## 5. Concrete Lambda property mappings

The following bindings are derived from declarations and runtime reads, not from guessed resource names.

| Logical property | Existing input / consumer | Proposed source and update policy |
|---|---|---|
| `email.proof_key` | `PROOF_KEY` in email verification Lambdas; decoded by common bootstrap; used for HMAC-SHA256 | Secret-aware provider; select Secrets Manager if key material may enter Lambda memory, otherwise evaluate a KMS MAC operation adapter. Environment contains a reference only, not the key value. See migration constraints below |
| `identity.pool_id`, `identity.client_id` | `POOL_ID`, `CLIENT_ID`; exact consumers differ by handler | Explicit provider outputs to local nonsecret environment reader; reject missing and cross-environment identity bindings |
| `proofs.table` | `TABLE_NAME`; email bootstrap, challenge/enrollment as applicable | DynamoDB name/ARN reference; env for name, IAM for access; do not put proof records in a configuration provider |
| `application.origin`, `email.sender` | `APP_ORIGIN`, `SENDER_ADDRESS` | Validated deployment-bound env; updates coordinate SES IAM FromAddress condition, Cognito email configuration, relying-party/callback/domain bindings as applicable |
| `email.diagnostics` | `DIAGNOSTIC_MODE` | Boolean local value by default; privileged audited edit, production-safe logging. Dynamic delivery only after deciding freshness and redaction semantics |
| `auth.route` | `AUTH_ROUTE` | Build/deployment binding, not a user-editable runtime property |
| `runtime.location`, `runtime.environment` | `RUNTIME_TABLE`, `ENVIRONMENT` | Nonsecret environment-bound references; preserve current server-side correctness, not a cached environment snapshot of the full runtime table |
| `capture.storage`, `capture.queue` | `CAPTURE_TABLE`, `CAPTURE_BUCKET`, `CAPTURE_QUEUE_URL` | Local references plus minimal DB/S3/SQS grants per actual consumer. Binding a queue URL does not authorize access |
| `capture.admission_policy` | `CAPTURE_ENABLED`, `CAPTURE_DOCUMENT_TYPE`, `CAPTURE_PURPOSE`, `CAPTURE_JURISDICTION` plus runtime `PolicySource` | Declare current precedence: env seeds service/defaults; published runtime policy controls admission. Keep current authoritative snapshot checks; do not silently turn admission policy into a stale TTL cache |
| `admin.bootstrap` | `ADMIN_ISSUER`, `ADMIN_CLIENT_ID`, `ADMIN_ORIGIN`, `ADMIN_LOGIN_DOMAIN` | Nonsecret deployment bootstrap; update login callback/CORS/CSP and identity references coherently; no browser secret |
| `index.registry` | `REGISTRY_TABLE`, `RUNTIME_TABLE` | Local references; registry/default synchronization remains signed, leased and transactional |
| `reset.inventory`, `reset.enabled` | `RESET_MANIFEST`, `RESET_TABLE`, `RESET_ENABLED`, `ENVIRONMENT` | Deployment-derived privileged bindings, not arbitrary editable URLs/IDs. Changes require exact target inventory and reset permission checks; manifest cannot come from browser input |

References: [email bootstrap](https://github.com/lambdawalker/go.attestra.aws.auth/blob/4607807ab0346f4a38532982889fe2e56954412e/cmd/internal/bootstrap/service.go), [sign-in bootstrap](https://github.com/lambdawalker/go.attestra.aws.auth/blob/4607807ab0346f4a38532982889fe2e56954412e/cmd/signin/main.go), [capture bootstrap](https://github.com/lambdawalker/go.attestra.aws.auth/blob/4607807ab0346f4a38532982889fe2e56954412e/awscapture/bootstrap.go), [shared admin](https://github.com/lambdawalker/go.attestra.aws.auth/blob/4607807ab0346f4a38532982889fe2e56954412e/cmd/admin/main.go), [index](https://github.com/lambdawalker/go.attestra.aws.auth/blob/4607807ab0346f4a38532982889fe2e56954412e/cmd/index/main.go), [reset](https://github.com/lambdawalker/go.attestra.aws.auth/blob/4607807ab0346f4a38532982889fe2e56954412e/cmd/environment-reset/main.go).

### Proof key: security and migration constraints

Current source marks `proofKey` as a Pulumi secret, injects its value into Lambda configuration, and loads one decoded key during initialization. It is not an unmarked plaintext Pulumi setting, but the runtime delivery differs from the proposed secret-reference policy.

AWS recommends Secrets Manager over environment variables for sensitive credentials. For cryptographic key material, the application must additionally decide whether key export into process memory is allowed. If not, evaluate KMS HMAC `GenerateMac`/`VerifyMac`; that changes the cryptographic operation interface and introduces remote-call latency/cost. A cached Secrets Manager reader is an alternative only when export/caching satisfies the required security boundary; do not label it universally the most secure option.

Current proof transactions store digests produced by one key and no per-record key identifier. Naively rotating the key can invalidate in-flight manual-code verification across Lambdas/releases.

Proposed sequence:

1. Declare the security boundary and select the eligible key/operation provider.
2. Import/reference the existing protected key without printing or accidentally replacing it; deployment tooling already guards against silent regeneration.
3. Introduce version-aware verification/key IDs or an explicitly bounded drain transition. The current ten-minute challenge expiry alone is not a complete rotation policy; include resends, retries and retained releases.
4. Coordinate all signing/verifying consumers; new writes use the intended version and existing eligible records retain verification.
5. Refresh through the reader/operation abstraction, not a permanently captured key that ignores rotation.
6. Enable rotation only after compatibility and failure-path tests; an arbitrary custom key does not gain a correct rotation workflow merely by being stored in Secrets Manager.
7. Remove raw `PROOF_KEY` delivery only after the migration is proven; keep rollback and secret retirement deliberate.

Do not introduce a production raw-env fallback if secret retrieval fails. Secret/log/state redaction must cover both old and new paths.

## 6. Existing runtime settings: preserve semantics before optimization

Current runtime configuration includes:

- `onboarding.idCapture`, `onboarding.passkey`, `onboarding.password`: required/optional/disabled.
- `onboarding.passwordPlacement`: hidden/with_email/after_verification, with validation.
- Application password min/max length and lowercase/uppercase/numbers/symbol rules.
- `features.idCapture`, normalized consistently with onboarding mode.
- Consent/disclosure messages in English/Spanish/French; fixed id_card and empty jurisdiction on new publications.
- Schema/environment identity, revision and timestamp.

[Model](https://github.com/lambdawalker/go.attestra.aws.auth/blob/4607807ab0346f4a38532982889fe2e56954412e/runtimeconfig/model.go) and [onboarding rules](https://github.com/lambdawalker/go.attestra.aws.auth/blob/4607807ab0346f4a38532982889fe2e56954412e/runtimeconfig/onboarding.go) define the contract. App-level password enrollment policy is not the same object as Cognito's pool password policy. Do not map one blindly onto the other; validate the combined acceptance rules.

The current [runtime store](https://github.com/lambdawalker/go.attestra.aws.auth/blob/4607807ab0346f4a38532982889fe2e56954412e/runtimeconfig/store.go) uses strongly consistent reads. Publish/grant updates use conditional transactions with current grant checks, expected revisions and audit history. Deployment default synchronization preserves admin overrides. The [public endpoint](https://github.com/lambdawalker/go.attestra.aws.auth/blob/4607807ab0346f4a38532982889fe2e56954412e/runtimeconfig/api.go) is allowlisted and no-store; it must never expose secret references/values or arbitrary new properties just because the framework supports them.

Recommended split:

| Property class | Initial plan | Why |
|---|---|---|
| Admin grants/revocation, deployment leases, reset state/token cutoff | Keep transactional authoritative reads/checks | Staleness changes authorization or coordination correctness |
| Enrollment/password enforcement and capture admission/consent snapshot | Preserve current fresh checks initially | A cheaper cache must not silently relax security or record a policy the user did not accept |
| Informational UI text / nonsecurity operational tuning | Consider cached AppConfig or another approved source after classifying coupling | AWS recommends AppConfig for dynamic application config, but eventual propagation needs explicit acceptance |
| Public settings projection | Preserve current API/schema and client failure/refresh contract | Backing-source changes should not break clients or accidentally publish private fields |

Disclosure text participates in capture policy identity. Even apparently informational text is not automatically safe to cache independently of its policy snapshot.

If AppConfig is adopted, define a single publication authority, validated projection and desired/applied revision relationship. Do not let the browser independently write both DynamoDB and AppConfig and report success after only one write. Preserve grants/audit in transactional storage, and explicitly gate activation/rollback. AppConfig is a candidate, not a mandatory replacement for this existing system.

## 7. Coupled changes the planner must validate

- **Queue/function:** current visibility is 720 seconds and worker timeout is 90 seconds; 720 exceeds AWS's six-times baseline of 540 seconds with no batching window declared. Re-evaluate the relationship when timeout, batching or concurrency changes; do not copy constants independently.
- **Evidence/consent:** application retention is seven days; bucket lifecycle has a ten-day safety net. Neither asynchronous lifecycle nor DynamoDB TTL is an exact deletion deadline. A retention change must update consent identity, cleanup, lifecycle, existing-data policy and tests together.
- **Model/access:** current extractor model is fixed and worker IAM restricts the model. If exposed, validate region/model availability and change code/reader settings and IAM together; never add unrestricted external endpoint input.
- **Origin/identity/email:** app origin, WebAuthn relying party, callbacks, DNS/certificates, SES sender identity and IAM conditions have shared constraints. Model these edges explicitly.
- **Capacity:** preserve production's explicit reserved/worker concurrency choices and quota checks; reject changes that bypass those checks.
- **Admin identity:** retain the SDK/Pulumi field-ownership split for managed-login/passkey setup, and read back security configuration without resetting unrelated Cognito fields.
- **Reset:** controls and invocation permissions are not ordinary feature flags. Keep environment authorization and deployed target inventory authoritative.
- **Published releases:** current functions are unqualified; first implement release/alias ownership before claiming that environment changes preserve old published traffic. Then track code hash, config revision and Lambda version separately.

## 8. Required administrative capabilities

Use separate roles rather than handing cloud credentials to a browser:

| Actor | Allowed scope |
|---|---|
| Artifact execution role | Read its own approved properties/secrets and perform its business operations |
| Runtime configuration administrator | Publish allowed app properties for explicitly granted environments through backend validation |
| Configuration rollout worker | Apply approved source updates or Lambda version/configuration changes with revision checks |
| Infrastructure/security operator | Change Cognito baseline, IAM, DNS/certs, storage/queue/capacity and other managed-resource settings |
| Reset operator | Explicit authorized reset workflow; not implicit privilege from ordinary settings editing |
| Deployment operator/CI | Selected stack/environment and protected credential references; SSO/OIDC where supported |

The current admin is intentionally narrow; do not simply grant its existing Lambda broad infrastructure permissions. Add durable change jobs and scoped workers if administration expands. AWS actions that affect whole maps/resources require backend allowlisting and preservation of unrelated fields.

When embedded, Attestra should expose property contracts and suppress its standalone admin panel by default. Its shared runtime/history store and identity boundary must not be destroyed merely because the UI is suppressed. Choose whether the host application reuses those services or adapts/migrates them explicitly.

## 9. Proposed delivery sequence and verification

1. **Inventory/contracts:** expose actual property/consumer inventory, ownership, sensitivity, defaults and current precedence. Validate mappings without changing deployed behavior.
2. **Reader/writer adapters:** env reader for local bindings, current DynamoDB runtime adapter, managed-resource change plans. Add strict missing/unknown/type/source/permission diagnostics.
3. **Proof-key migration:** choose key boundary, implement compatible version handling and protected delivery, prove in-flight/old-release behavior.
4. **Configuration administration:** application ownership/panel suppression, environment/property permissions, durable update jobs, optimistic concurrency and read-back checks.
5. **Release-aware rollouts:** publish/alias support, code+configuration identity, no silent pin changes, coordinated rollback.
6. **Optional AppConfig pilot:** only for properties with accepted propagation semantics; compare actual concurrency/refresh/workload costs after security requirements pass.
7. **Managed-resource adapters:** add service-specific validation and tests incrementally, preserving existing SDK/Pulumi field owners.

Verification should cover missing per-artifact bindings, denied read/write access, cross-environment inputs, sensitive URL classification, secret unavailability/refresh, proof rotation overlap, concurrent config writes, DynamoDB grant revocation, policy-changed capture admission, password-policy consistency, queue/timeout bounds, retention/consent coupling, stale-source behavior, native resource updates, and panel suppression without deleting retained services.

Use local unit/infrastructure-mock tests first. Review requested cloud/IAM changes separately before any future smoke deployment. This document makes no claim that these migrations or tests have already been implemented.

## Artifact-specific configuration plans

The [configuration-panel catalog](configuration-panel-catalog.md) links detailed plans for all 16 artifact types in this inventory. Lambda, API Gateway and Cognito are joined by DynamoDB, S3, SQS, EventBridge, CloudWatch, SES, Bedrock, ACM, DNS, CloudFront/OAC, IAM/OIDC, admin/index artifacts and deployment tooling/state.

Each plan distinguishes **Application settings** from **Artifact settings**, identifies useful post-deployment controls and read-only/migration boundaries, and describes the custom-panel contract, scoped adapters/permissions, durable jobs, ownership, verification and recovery limits. Plans preserve the distinction between current source behavior and future capabilities. No panel or cloud change is implemented by these documents.

## 10. Provider references

- [Lambda environment variables, security recommendation and published-version behavior](https://docs.aws.amazon.com/lambda/latest/dg/configuration-envvars.html)
- [Secrets Manager retrieval/caching for Lambda](https://docs.aws.amazon.com/lambda/latest/dg/with-secrets-manager.html)
- [AWS KMS HMAC keys](https://docs.aws.amazon.com/kms/latest/developerguide/hmac.html)
- [AppConfig Lambda extension guidance](https://docs.aws.amazon.com/appconfig/latest/userguide/appconfig-integration-lambda-extensions.html)
- [AppConfig cache/propagation behavior](https://docs.aws.amazon.com/appconfig/latest/userguide/appconfig-integration-lambda-extensions-how-it-works.html)
- [Cognito update preservation and immutable settings](https://docs.aws.amazon.com/cognito/latest/developerguide/cognito-user-pool-updating.html)
- [SQS Lambda visibility/timeout guidance](https://docs.aws.amazon.com/lambda/latest/dg/services-sqs-configure.html)
- [DynamoDB TTL](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/TTL.html)
